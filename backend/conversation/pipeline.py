"""Orchestrates: crisis -> engines -> knot -> planner -> RAG -> Gemini ->
deepen -> citation filter -> ChatResponse.

See docs/phase-2-runtime-plan.md §1 for the base pipeline and
docs/phase-6-depth-plan.md for the Phase 6 depth steps (knot summarizer,
soft classifier, deepen pass, dependency detection).

Crisis remains first and lexicon-only. Every Phase 6 step is an enhancement
that degrades to the Phase 5 behaviour if the LLM is unavailable.
"""
from __future__ import annotations

from backend.conversation.emotion_response_store import EmotionResponseStore
from backend.conversation.response_generator import ResponseGenerator
from backend.conversation.schemas import ChatRequest, ChatResponse, VerseCitation
from backend.engines import (
    appraisal_analyzer,
    crisis_detector,
    defence_detector,
    dependency_detector,
    emotion_analyzer,
    guna_detector,
    intent_detector,
    knot_summarizer,
    soft_classifier,
)
from backend.engines.language import resolve_reply_lang, is_mostly_devanagari
from backend.engines.metaphor_tracker import (
    avoid_instruction,
    detect_metaphors_in_text,
    metaphor_id_from_ref,
    metaphors_from_history,
)
from backend.engines.response_planner import plan as plan_turn
from backend.memory.session_store import SessionStore
from backend.rag.citation_filter import enforce_citations
from backend.rag.retriever import Retriever
from backend.rag.taxonomy_store import TaxonomyStore
from backend.rag.verse_store import VerseStore


class ConversationPipeline:
    def __init__(
        self,
        verse_store: VerseStore,
        taxonomy_store: TaxonomyStore,
        retriever: Retriever,
        session_store: SessionStore,
        generator: ResponseGenerator,
        allowlist: set[str],
        teach_gate_min_questions: int,
        max_verses_per_turn: int,
        enable_knot_summarizer: bool = True,
        enable_soft_classifier: bool = True,
        enable_deepen_pass: bool = True,
        soft_classifier_threshold: float = 0.45,
        emotion_store: EmotionResponseStore | None = None,
    ):
        self.verse_store = verse_store
        self.taxonomy_store = taxonomy_store
        self.retriever = retriever
        self.session_store = session_store
        self.generator = generator
        self.allowlist = allowlist
        self.teach_gate_min_questions = teach_gate_min_questions
        self.max_verses_per_turn = max_verses_per_turn
        self.enable_knot_summarizer = enable_knot_summarizer
        self.enable_soft_classifier = enable_soft_classifier
        self.enable_deepen_pass = enable_deepen_pass
        self.soft_classifier_threshold = soft_classifier_threshold
        self.emotion_store = emotion_store

    @staticmethod
    def _emotion_from_history(history: list[dict], lookback: int = 2) -> str | None:
        """Re-scan the last few user turns when this turn has no lexicon hit."""
        user_turns = [h["content"] for h in history if h.get("role") == "user"]
        for content in reversed(user_turns[-lookback:]):
            result = emotion_analyzer.analyze(content)
            if result.primary:
                return result.primary
        return None

    def _citations_for(self, verse_ids: list[str]) -> list[VerseCitation]:
        citations = []
        for vid in verse_ids:
            card = self.verse_store.get(vid)
            if not card:
                continue
            translations = card.get("translations", {})
            citations.append(
                VerseCitation(
                    id=vid,
                    chapter=card["chapter"],
                    verse=card["verse"],
                    short=f"Bhagavad Gita chapter {card['chapter']}, verse {card['verse']}",
                    translation_en=translations.get("en"),
                    translation_hi=translations.get("hi") or None,
                )
            )
        return citations

    def _prefer_emotion_map_verses(
        self,
        emotion_id: str | None,
        retrieved_ids: list[str],
        already_delivered: set[str],
    ) -> list[str]:
        """Put emotion-map preferred verses first when they are allowlisted
        AND not already delivered this session.

        Confirmed bug (found live): this used to re-prepend the emotion
        card's primary_verse on every turn that emotion fired, with no
        awareness of session history at all -- overriding the retriever's
        already-correct already_delivered-aware ordering and re-serving the
        same verse (e.g. BG_9_22 for loneliness) repeatedly in one session.
        """
        if not self.emotion_store or not emotion_id:
            return retrieved_ids
        card = self.emotion_store.get(emotion_id)
        if not card:
            return retrieved_ids

        preferred: list[str] = []
        primary = card.get("primary_verse")
        if primary and primary in self.allowlist and primary not in already_delivered:
            preferred.append(primary)
        for vid in card.get("secondary_verses") or []:
            if (
                vid in self.allowlist
                and vid not in already_delivered
                and vid not in preferred
            ):
                preferred.append(vid)

        if not preferred:
            return retrieved_ids

        ordered: list[str] = []
        for vid in preferred:
            if vid not in ordered:
                ordered.append(vid)
        for vid in retrieved_ids:
            if vid not in ordered:
                ordered.append(vid)
        return ordered[: self.max_verses_per_turn]

    def handle_message(self, req: ChatRequest) -> ChatResponse:
        session = self.session_store.get_or_create(req.session_id)
        history = [{"role": m.role, "content": m.content} for m in req.conversation_history]

        # 1. Crisis — always first, always wins. L3/L4 (helplines_only) get a
        # fixed, vetted safety message with no LLM involved. L1/L2 still block
        # teaching but flow through the normal engines/planner/LLM path below
        # so the reply stays warm and conversational rather than an alarming
        # template for someone who isn't in acute danger.
        crisis = crisis_detector.detect(req.message)
        if crisis.helplines_only:
            # Answer the emergency in the language it was spoken in.
            text = crisis_detector.helpline_message(
                self.taxonomy_store.helpline_refs(), lang=crisis.lang
            )
            text_en, title_en = self.generator.english_ui(
                text,
                user_message=req.message,
                need_title=not req.conversation_history,
            )
            self.session_store.record_turn(
                req.session_id, asked_question=False, verses_used=[], crisis_level=crisis.level
            )
            return ChatResponse(
                text=text,
                is_crisis=True,
                crisis_level=crisis.level_int,
                verses=[],
                verse_citations=[],
                response_style="crisis_protocol",
                detected_emotion=None,
                teach_action="crisis",
                text_en=text_en or text,
                title_en=title_en,
            )

        # 2. Parallel-ish lexicon engines.
        emotion = emotion_analyzer.analyze(req.message)
        intent = intent_detector.detect(req.message)
        appraisal = appraisal_analyzer.analyze(req.message)
        defence = defence_detector.analyze(req.message)
        guna = guna_detector.analyze(req.message)
        # UI speech preference overrides auto-detect (captions stay English separately).
        lang = resolve_reply_lang(req.message, req.reply_lang)
        dependency = dependency_detector.analyze(req.message)

        # 2b/2c. Optional LLM side-steps. These are SECONDARY to the main reply —
        # each is a full Gemini round-trip and made first turns painfully slow.
        # Soft classifier: only when lexicon has no primary at all.
        # Knot: skip on cold first messages; run when we have session history
        # or they are explicitly seeking guidance / past the first question.
        need_soft = (
            self.enable_soft_classifier
            and emotion.primary is None
            and emotion.confidence < self.soft_classifier_threshold
        )
        need_knot = self.enable_knot_summarizer and (
            bool(history)
            or session.questions_asked >= 1
            or intent.intent == "seeking_guidance"
        )

        knot = knot_summarizer.Knot()
        soft = None

        if need_soft or need_knot:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            allowed: list[str] = []
            if need_soft:
                allowed_set = set(self.taxonomy_store.emotion_ids())
                if self.emotion_store:
                    allowed_set.update(self.emotion_store.ids())
                allowed = sorted(allowed_set)

            futures = {}
            with ThreadPoolExecutor(max_workers=2) as pool:
                if need_soft:
                    futures[
                        pool.submit(
                            soft_classifier.classify,
                            client=self.generator.client,
                            model=self.generator.model,
                            user_message=req.message,
                            allowed_emotions=allowed,
                        )
                    ] = "soft"
                if need_knot:
                    futures[
                        pool.submit(
                            knot_summarizer.summarize,
                            client=self.generator.client,
                            model=self.generator.model,
                            user_message=req.message,
                            history=history,
                        )
                    ] = "knot"

                for fut in as_completed(futures):
                    kind = futures[fut]
                    try:
                        result = fut.result()
                    except Exception:  # noqa: BLE001 - side-steps never block chat
                        continue
                    if kind == "soft":
                        soft = result
                    else:
                        knot = result

            if soft is not None and soft.available:
                if emotion.primary is None and soft.emotion:
                    emotion.primary = soft.emotion
                    emotion.confidence = max(emotion.confidence, soft.confidence)
                if soft.intent and intent.confidence < 0.5:
                    intent.intent = soft.intent

        # 3. Planner.
        turn_plan = plan_turn(
            crisis=crisis,
            emotion=emotion,
            intent=intent,
            appraisal=appraisal,
            defence=defence,
            guna=guna,
            session=session,
            teach_gate_min_questions=self.teach_gate_min_questions,
            lang=lang,
        )

        # 3b. Depth additions to the instruction: the knot, the recurring theme,
        # and dependency handling. Appended rather than replacing, so the Phase 5
        # turn structure stays intact.
        extra: list[str] = []
        knot_block = knot.as_instruction()
        if knot_block:
            extra.append(knot_block)

        theme = session.recurring_theme()
        if theme and turn_plan.turn_action == "teach":
            extra.append(
                f"\nRECURRING: this session keeps returning to {theme}. Go FURTHER than "
                "a first-time answer would — they have already heard the gentle version. "
                "Do not say you have noticed a pattern; just go deeper."
            )

        dependency_block = dependency_detector.planner_directive(
            dependency, session.dependency_hits
        )
        if dependency_block:
            extra.append(dependency_block)

        # UI Hinglish: spoken audio must be identical Devanagari Hindi (same as HI).
        # Code-switch Hinglish is only for on-screen text via roman_hinglish_ui.
        if req.reply_lang == "hinglish":
            extra.append(
                "\nSPOKEN REPLY (critical): Write the full reply in Devanagari Hindi — "
                "the SAME voice/register as Hindi mode. Do NOT write Roman Hinglish or "
                "English in the spoken reply. On-screen Hinglish is generated separately."
            )

        if extra:
            turn_plan.instruction = turn_plan.instruction + "\n" + "\n".join(extra)

        # Metaphors already spoken (session + recent assistant history).
        used_metaphors = set(session.metaphors_delivered) | metaphors_from_history(history)
        metaphor_avoid = avoid_instruction(used_metaphors)

        # 4. RAG (only if teaching this turn). Short follow-ups ("yes, exactly")
        # carry no lexicon signal, so fall back through: this turn -> recent user
        # turns -> session memory. Without this, the teaching turn that finally
        # opens the gate can retrieve blind.
        effective_emotion = (
            emotion.primary
            or self._emotion_from_history(history)
            or session.last_emotion
        )
        retrieved_ids: list[str] = []
        if turn_plan.use_verse_now:
            # The knot sharpens the semantic query: "batao kya karun" retrieves
            # nothing useful on its own, but "+ attachment to outcome" does.
            query = f"{req.message} {knot.retrieval_hint()}".strip()
            # Prefer a single primary verse for cards/trust; allow 2 only when
            # the emotion map explicitly lists secondaries and gate is deep.
            retrieve_cap = 1 if session.depth_level() < 3 else min(2, self.max_verses_per_turn)
            retrieved_ids = self.retriever.retrieve(
                query=query,
                emotion_id=effective_emotion,
                allowlist=self.allowlist,
                already_delivered=session.verses_delivered,
                crisis_flags=set(),  # NONE/L1/L2 reach here; L3/L4 short-circuit above
                cap=retrieve_cap,
            )
            # Emotion map: prefer primary (then secondary) if allowlisted AND
            # not already delivered — map ids often have no taxonomy tag row yet.
            retrieved_ids = self._prefer_emotion_map_verses(
                effective_emotion, retrieved_ids, session.verses_delivered
            )[:retrieve_cap]

        # The generator gets the full teaching package, not just a translation:
        # strategy is its mission statement, and contested/pluralism fields are
        # what stop it overclaiming on the verses most open to misuse.
        retrieved_cards = []
        for vid in retrieved_ids:
            card = self.verse_store.get(vid)
            if not card:
                continue
            translations = card.get("translations", {})
            retrieved_cards.append(
                {
                    "id": vid,
                    "chapter": card["chapter"],
                    "verse": card["verse"],
                    "translation_en": translations.get("en", ""),
                    "translation_hi": translations.get("hi", ""),
                    "response_strategy": card.get("response_strategy", ""),
                    "tone": card.get("tone", ""),
                    "readiness": card.get("readiness", ""),
                    "sample_follow_up": card.get("sample_follow_up", ""),
                    "contested": bool(card.get("contested")),
                    "pluralism_note": card.get("pluralism_note") or "",
                    "commentary_product": card.get("commentaries", {}).get("product", ""),
                    # Context only — the model may allude, but may cite only `id`.
                    "secondary_verses": (card.get("secondary_verses") or [])[:2],
                }
            )

        skip_ref = None
        if self.emotion_store and effective_emotion:
            card = self.emotion_store.get(effective_emotion)
            ref = (card or {}).get("metaphor_ref")
            mid = metaphor_id_from_ref(ref)
            if mid and mid in used_metaphors:
                skip_ref = ref

        # Defence signals come from a different engine than emotion_analyzer,
        # so the exemplar tagged for them (e.g. fs_021, "honor the frame then
        # ask") is otherwise invisible to fewshot scoring, which only sees
        # `effective_emotion`. Confirmed live: it was losing to unrelated
        # emotion-matched exemplars on a coin-flip. Feed the defence kind in
        # as an extra scoring hint without touching emotion_id itself, so the
        # emotion craft card still reflects the real underlying feeling.
        fewshot_hints: list[str] = []
        if defence.spiritual_bypass:
            fewshot_hints.append("spiritual_bypassing_defence")

        # 5. Generate — effective_emotion drives fewshot + craft card selection.
        raw_text = self.generator.generate(
            user_message=req.message,
            plan_instruction=turn_plan.instruction,
            retrieved=retrieved_cards,
            history=history,
            turn_action=turn_plan.turn_action,
            lang=lang,
            emotion_id=effective_emotion,
            metaphor_avoid=metaphor_avoid or None,
            skip_metaphor_ref=skip_ref,
            fewshot_hints=fewshot_hints or None,
        )

        # 5b. Deepen pass on teach turns — cut hedging, sharpen the hard truth.
        # Runs BEFORE the citation filter so any citation drift it introduces is
        # still caught by the wall.
        if self.enable_deepen_pass and turn_plan.turn_action == "teach" and retrieved_ids:
            raw_text = self.generator.deepen(raw_text, retrieved_ids, lang=lang)

        # 6. Citation safety wall (+ strip trailing vocative).
        clean_text, final_ids = enforce_citations(raw_text, retrieved_ids, self.allowlist)

        # Hindi + UI Hinglish: spoken text must be Devanagari (same TTS voice path).
        if req.reply_lang in ("hi", "hinglish") and not is_mostly_devanagari(clean_text):
            clean_text = self.generator.ensure_devanagari_spoken(clean_text)

        metaphors_this_turn = sorted(detect_metaphors_in_text(clean_text))

        # On-screen chrome: English by default; UI Hinglish → code-switch mix.

        need_title = not history  # first user turn in this thread payload
        if req.reply_lang == "hinglish":
            text_en, title_en = self.generator.roman_hinglish_ui(
                clean_text,
                user_message=req.message,
                need_title=need_title,
            )
        else:
            text_en, title_en = self.generator.english_ui(
                clean_text,
                user_message=req.message,
                need_title=need_title,
            )
        if not text_en:
            text_en = clean_text

        # 7. Update session memory.
        asked_question = turn_plan.turn_action in ("question", "witness") or turn_plan.ask_question
        self.session_store.record_turn(
            req.session_id,
            asked_question=asked_question,
            verses_used=final_ids,
            crisis_level=crisis.level,
            emotion_primary=emotion.primary,
            knot=knot.to_dict() if knot.available else None,
            language=lang,
            dependency=dependency.any_dependency,
            metaphors_used=metaphors_this_turn,
            pushback=intent.intent == "pushing_back",
        )

        return ChatResponse(
            text=clean_text,
            is_crisis=crisis.level != "NONE",
            crisis_level=crisis.level_int,
            verses=final_ids,
            verse_citations=self._citations_for(final_ids),
            response_style=turn_plan.style,
            detected_emotion=emotion.primary,
            teach_action=turn_plan.turn_action,
            text_en=text_en,
            title_en=title_en,
        )

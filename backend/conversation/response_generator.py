"""Gemini-backed generator. LLM is always last in the pipeline — see
docs/phase-2-runtime-plan.md §1 master principle.

Prompt composition:
  1. system: constitution + LANGUAGE BIBLE + SPEECH ANALYSIS
     (assembled by prompt_loader at startup)
  2. few-shot exemplar(s) matched by emotion + lang + register
  3. developer wrapper: planner + register + emotion card + retrieval package
  4. history: last N turns
  5. user message

Generation budget varies by turn type (Phase 5 §5.6 E3): teaching needs room
to be specific, listening turns should stay short, crisis stays tight.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from backend.conversation.fewshot_store import FewshotStore
from backend.conversation.emotion_response_store import EmotionResponseStore
from backend.conversation.prompt_loader import register_hint
from backend.llm.gemini_client import GeminiClient

logger = logging.getLogger("krishna.generator")

# Messages (not exchanges) kept in the model's window. At 8, a fact stated in
# the first 1-2 exchanges of a 6+ turn conversation falls out of view by the
# time the model needs it again -- plausible root cause of a live-reported bug
# where two numbers stated on separate early turns ("1 crore", "£30,000
# tuition") got merged into one wrong figure that then persisted: the model
# wasn't re-deriving it each time, it was reading its own prior (wrong)
# restatement back as history once the source turns were gone. Gemini's
# context is large enough that this costs little to raise.
_MAX_HISTORY_TURNS = 24

# Prefixes any reply that is NOT real model output. Tests assert on this so a
# quota error or outage can never masquerade as a passing quality check —
# during Phase 5 a 429 silently passed the "no forbidden fillers" assertion.
GENERATION_FAILED_MARKER = "[generation-unavailable]"

_FEWSHOT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "fewshot_v5.json"
_EMOTION_MAP_PATH = Path(__file__).resolve().parents[2] / "prompts" / "emotion_response.json"

# turn_action -> (max_tokens, temperature)
# Padded with headroom above what a normal reply needs: Devanagari costs more
# tokens per visible character than Latin script, and a reply that hits the
# ceiling gets silently cut off mid-sentence with no error -- confirmed live
# (see backend/llm/gemini_client.py finish_reason logging).
_BUDGETS: dict[str, tuple[int, float]] = {
    "teach": (3500, 0.7),
    "question": (2200, 0.75),
    "witness": (2200, 0.75),
    "validate": (2400, 0.75),
    "crisis_soft": (1200, 0.5),
}
_DEFAULT_BUDGET = (2200, 0.75)


class ResponseGenerator:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        fewshot_store: FewshotStore | None = None,
        emotion_store: EmotionResponseStore | None = None,
        fallback_models: list[str] | None = None,
    ):
        self._client = (
            GeminiClient(api_key, fallback_models=fallback_models) if api_key else None
        )
        self.model = model
        self.system_prompt = system_prompt
        self.fewshot_store = fewshot_store or FewshotStore(_FEWSHOT_PATH)
        self.emotion_store = emotion_store or EmotionResponseStore(_EMOTION_MAP_PATH)

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def client(self):
        """Shared Gemini client for Phase 6 side-steps (knot summarizer,
        soft classifier). None when unconfigured — every caller treats that
        as 'skip this enhancement'."""
        return self._client

    # ---------- prompt assembly ----------

    def _render_verse(self, v: dict) -> str:
        lines = [
            f"- {v['id']} (Bhagavad Gita chapter {v['chapter']}, verse {v['verse']})",
            f"  EN: \"{v['translation_en']}\"",
        ]
        if v.get("translation_hi"):
            lines.append(f"  HI: \"{v['translation_hi']}\"")
        if v.get("response_strategy"):
            lines.append(f"  MISSION (use this as the point you are making): {v['response_strategy']}")
        if v.get("tone"):
            lines.append(f"  tone: {v['tone']}")
        if v.get("commentary_product"):
            lines.append(f"  product note: {v['commentary_product']}")
        if v.get("contested"):
            note = v.get("pluralism_note") or "Traditions read this verse differently."
            lines.append(f"  ** CONTESTED — {note}")
        if v.get("secondary_verses"):
            lines.append(
                f"  related (context only, DO NOT cite): {', '.join(v['secondary_verses'])}"
            )
        return "\n".join(lines)

    def _wrapper_message(
        self,
        plan_instruction: str,
        retrieved: list[dict],
        turn_action: str = "question",
        emotion_card: str | None = None,
        metaphor_avoid: str | None = None,
    ) -> str:
        register = register_hint(turn_action)
        voice = (
            f"[REGISTER THIS TURN]\n{register}\n"
            "Obey LANGUAGE BIBLE for exact phrase families and ADDRESS rules. "
            "Obey SPEECH PATTERN ANALYSIS for mirror-first craft. "
            "Constitution §III overrides style on crisis/identity/citations.\n"
            "\n[LANGUAGE CONSISTENCY — NON-NEGOTIABLE]\n"
            "- Every example phrase in the LANGUAGE BIBLE / ANALYSIS docs (e.g. "
            "'यह निर्णय तुम्हारा है') is a PATTERN to express, not literal text to insert. "
            "Render it in the reply's actual language — see [PLANNER INSTRUCTION] below for "
            "which one this turn is in.\n"
            "- Do NOT drop an untranslated Hindi/Devanagari phrase into an English or "
            "Hinglish reply just because you recall it that way from the reference docs. The "
            "whole reply must be in one consistent language (a mid-reply वोकेटिव address "
            "word is the only exception, per ADDRESS below).\n"
            "\n[ADDRESS — NON-NEGOTIABLE]\n"
            "- At most ONE vocative (पार्थ / धनंजय / अर्जुन / …).\n"
            "- Mid-reply only: after a point is made, with more still to say after it.\n"
            "- NEVER end the whole reply on पार्थ / Partha / अर्जुन.\n"
            "\n[CITATION — NON-NEGOTIABLE]\n"
            "- Weave the teaching into your own sentence. NEVER open a sentence with an "
            "announce formula — this includes but is not limited to: "
            "'भगवद्गीता के … अध्याय के … श्लोक में कहा गया है', "
            "'As chapter X verse Y states', 'As it is written in Bhagavad Gita X.Y', "
            "'It is said in the Gita', 'As stated in Bhagavad Gita X.Y', "
            "'The Gita says/teaches that'. Any sentence that announces a source before "
            "quoting it is the same violation even if the exact wording differs.\n"
            "- Quiet tag only: 'भगवद्गीता 2.47' or 'Bhagavad Gita 2.47', placed inside the "
            "sentence carrying the teaching — not as a preamble to it. Prefer ONE verse.\n"
            "\n[LENGTH — NON-NEGOTIABLE]\n"
            "- Write COMPLETE sentences. Never stop mid-clause or trail off.\n"
            "- Listening turns (no verse): at least 3 full sentences "
            "(mirror the situation → name the underside → one real question).\n"
            "- Teach turns: 5–8 full sentences, but VARY the scaffold — not the same "
            "acknowledge→metaphor→verse→अर्थात→agency every time.\n"
            "- Hindi/Hinglish: natural spoken length, तुम only.\n"
            "- TEACH turns must NOT end with a question mark. The close is agency returned "
            "as a statement ('the choice is yours from here'), not another question — "
            "questions belong to diagnostic/listening turns, not to the close of a teaching.\n"
        )

        emotion_block = ""
        if emotion_card:
            emotion_block = f"\n{emotion_card}\n"

        avoid_block = f"\n{metaphor_avoid}\n" if metaphor_avoid else ""

        if retrieved:
            block = ["You may cite ONLY the following verse(s) if you teach this turn:"]
            block += [self._render_verse(v) for v in retrieved]
            block.append(
                "Do not invent any other BG_x_y id or chapter/verse pair. If none of "
                "these fit, do not cite a verse this turn."
            )
            block.append(
                "Teaching shape: name the underside → optional fresh image "
                "(not one already used) → weave verse narratively → अर्थात → agency. "
                "Cite at most one verse unless true synthesis requires two."
            )

            if any(v.get("contested") for v in retrieved):
                block.append(
                    "\nCONTESTED VERSE RULES (a verse above is marked contested):\n"
                    "- Say the teaching is Krishna's, spoken to Arjuna. Never speak as the "
                    "'I' of the verse. You are not that 'I'.\n"
                    "- Include one honest line that traditions read this differently, drawn "
                    "from the note above.\n"
                    "- Do not present one school's reading as settled fact.\n"
                    "- Never use it to justify harm, revenge, fatalism, or abandoning "
                    "treatment, family, or responsibility."
                )
            retrieval_block = "\n".join(block)
        else:
            retrieval_block = (
                "NO verse has been retrieved for this turn. This is a listening turn, not a "
                "teaching turn.\n"
                "- Do NOT quote, paraphrase, or allude to any Bhagavad Gita verse.\n"
                "- Do NOT write 'chapter X verse Y' or any BG_x_y id.\n"
                "- Do NOT recall scripture from your own memory — you have none available "
                "this turn.\n"
                "- Open with a DIAGNOSTIC mirror or question (LANGUAGE BIBLE / ANALYSIS). "
                "No empty empathy filler. No customer-service framing."
            )
        return (
            f"{voice}{emotion_block}{avoid_block}\n[PLANNER INSTRUCTION]\n{plan_instruction}\n\n"
            f"[RETRIEVAL]\n{retrieval_block}"
        )

    # ---------- generation ----------

    def generate(
        self,
        user_message: str,
        plan_instruction: str,
        retrieved: list[dict],
        history: list[dict],
        turn_action: str = "question",
        lang: str = "en",
        emotion_id: str | None = None,
        metaphor_avoid: str | None = None,
        skip_metaphor_ref: str | None = None,
        fewshot_hints: list[str] | None = None,
    ) -> str:
        if not self.available:
            return (
                f"{GENERATION_FAILED_MARKER} No GEMINI_API_KEY is configured. Set it in .env "
                "and restart the backend."
            )

        max_tokens, temperature = _BUDGETS.get(turn_action, _DEFAULT_BUDGET)

        messages = [{"role": "system", "content": self.system_prompt}]

        # Few-shots for non-crisis turns: match emotion + language + register.
        if turn_action not in ("crisis",):
            exemplar = self.fewshot_store.pick(
                emotion_id=emotion_id,
                lang=lang,
                turn_action=turn_action,
                max_examples=1,
                extra_hints=fewshot_hints,
            )
            if exemplar:
                messages.append({"role": "system", "content": exemplar})

        for turn in history[-_MAX_HISTORY_TURNS:]:
            role = "assistant" if turn.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": turn.get("content", "")})

        emotion_card = None
        if self.emotion_store and emotion_id:
            emotion_card = self.emotion_store.render_card(
                emotion_id,
                lang=lang,
                skip_metaphor_ref=skip_metaphor_ref,
            )

        messages.append(
            {
                "role": "system",
                "content": self._wrapper_message(
                    plan_instruction,
                    retrieved,
                    turn_action=turn_action,
                    emotion_card=emotion_card,
                    metaphor_avoid=metaphor_avoid,
                ),
            }
        )
        messages.append({"role": "user", "content": user_message})

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001 - safe fallback, log for ops
            logger.exception("Gemini generation failed")
            err = str(exc).lower()
            if (
                type(exc).__name__ in ("ResourceExhausted", "RateLimitError")
                or "resource_exhausted" in err
                or "rate_limit" in err
                or "quota" in err
                or "429" in err
            ):
                return (
                    f"{GENERATION_FAILED_MARKER} Gemini free-tier quota is exhausted "
                    "for all configured models right now. Wait a minute (RPM) or until "
                    "daily reset, enable billing in Google AI Studio, or set a fresh "
                    "GEMINI_API_KEY / GEMINI_MODEL in .env and restart the backend."
                )
            return (
                f"{GENERATION_FAILED_MARKER} I'm having trouble finding words right now. "
                "Could you say that again in a moment?"
            )

    def deepen(self, draft: str, retrieved_ids: list[str], lang: str = "en") -> str:
        """Second pass on teach turns: cut fluff, sharpen the hard truth.

        A single generation tends to hedge — it softens the difficult sentence
        into a question and pads with reassurance. This rewrite asks for the
        specificity the anti-generic charter demands.

        Citation-safe by construction: the allowed ids are restated, and the
        result still goes through the citation filter downstream. Any failure
        keeps the draft, so this can never lose a reply.
        """
        if not self.available or not draft.strip():
            return draft
        if draft.startswith(GENERATION_FAILED_MARKER):
            return draft

        allowed = ", ".join(retrieved_ids) if retrieved_ids else "NONE"
        language_rule = {
            "hi": "Keep it in Hindi.",
            "hinglish": (
                "Keep it in code-switching Hinglish — mix Roman Hindi and English "
                "in the same sentence (e.g. 'I'm thoda busy', 'Scene kya hai?'). "
                "Not pure English, not pure Roman Hindi, not Devanagari."
            ),
        }.get(lang, "Keep it in English.")

        instruction = (
            "Rewrite the companion's reply so it matches the LANGUAGE BIBLE + SPEECH ANALYSIS.\n"
            "- TEACHING: underside, optional fresh image, woven verse if any, implication, agency.\n"
            "- Lead with hard truth as a STATEMENT, not a soft question.\n"
            "- The reply must NOT end with a question mark. A teaching closes on agency "
            "returned to them as a statement — if the draft ends on a question, rewrite the "
            "final sentence as a statement instead.\n"
            "- At most one address word (पार्थ etc.) MID-reply — NEVER as the last word.\n"
            "- Ban ANY announce-then-quote formula: 'भगवद्गीता के…अध्याय…श्लोक में कहा गया है', "
            "'As it is written in Bhagavad Gita X.Y', 'It is said in the Gita', "
            "'As chapter X verse Y states', 'The Gita says/teaches that'. Weave the verse "
            "into your own sentence instead; quiet 'भगवद्गीता X.Y' tag only, no preamble.\n"
            "- Hindi/Hinglish: तुम only, never आप.\n"
            "- Cut therapy filler: never 'मैं समझता हूं' empty, never 'you got this'.\n"
            "- Keep it grounded in their specific people/stakes/words.\n"
            "- Keep exactly the same citations. Allowed verse ids: "
            f"{allowed}. Add no others, remove none that were used correctly.\n"
            f"- {language_rule}\n"
            "- Return ONLY the rewritten reply."
        )

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": draft},
                ],
                temperature=0.5,
                max_tokens=3500,
            )
            rewritten = (completion.choices[0].message.content or "").strip()
        except Exception:  # noqa: BLE001 - keep the draft on any failure
            logger.warning("Deepen pass failed; keeping draft", exc_info=True)
            return draft

        # A rewrite that lost most of the reply is a failure, not an improvement.
        if len(rewritten) < len(draft) * 0.4:
            logger.warning("Deepen pass returned a suspiciously short rewrite; keeping draft")
            return draft
        return rewritten or draft

    def ensure_devanagari_spoken(self, draft: str) -> str:
        """Force spoken reply into Devanagari Hindi (same path for HI + Hinglish).

        UI Hinglish sometimes leaks Roman/code-switch into `text`; TTS must still
        hear Devanagari so the Hindi voice stays identical.
        """
        text = (draft or "").strip()
        if not text or not self.available:
            return text
        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Rewrite the companion reply into natural spoken Hindi "
                            "in Devanagari script only. Keep the same meaning, "
                            "names, and Gita citations. Use तुम (never आप). "
                            "Return ONLY the Hindi reply — no English, no Roman script."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.15,
                max_tokens=900,
            )
            out = (completion.choices[0].message.content or "").strip()
            return out or text
        except Exception:  # noqa: BLE001
            logger.warning("ensure_devanagari_spoken failed; keeping draft", exc_info=True)
            return text

    def crisis_response(self, fixed_message: str) -> str:
        """Crisis path prefers a fixed safety string over LLM generation
        (plan §6.1: 'prefer fixed strings for safety')."""
        return fixed_message

    def english_ui(
        self,
        spoken_reply: str,
        user_message: str | None = None,
        need_title: bool = False,
    ) -> tuple[str, str | None]:
        """English on-screen copy: subtitles (+ optional sidebar title).

        Spoken reply stays in the user's language; UI chrome is English.
        Falls back to the spoken text / a short English stub if Gemini is down.
        """
        spoken = (spoken_reply or "").strip()
        if not spoken:
            return "", "New conversation" if need_title else None

        # Already Latin-only → use as subtitle; still may need a title.
        has_indic = bool(__import__("re").search(r"[\u0900-\u097F]", spoken))
        user = (user_message or "").strip()
        user_indic = bool(__import__("re").search(r"[\u0900-\u097F]", user)) if user else False

        if not self.available:
            title = None
            if need_title:
                title = "New conversation" if user_indic else (user[:42] if user else "New conversation")
            return (spoken if not has_indic else spoken), title

        if not has_indic and not (need_title and user_indic):
            title = None
            if need_title and user:
                title = user.replace("\n", " ").strip()
                if len(title) > 42:
                    title = title[:42].rstrip() + "…"
            return spoken, title

        parts = [
            "Return ONLY compact JSON, no markdown:",
            '{"subtitle_en":"...","title_en":"..."}',
            "",
            "Rules:",
            "- subtitle_en: faithful English of the companion reply for movie subtitles.",
            "  Keep meaning, names, Gita refs (e.g. Bhagavad Gita 2.47). No commentary.",
            "- title_en: 3–7 word English sidebar title for the USER message theme.",
            "  No quotes. No trailing period.",
        ]
        if has_indic:
            parts.append(f"\nCOMPANION_REPLY:\n{spoken}")
        else:
            parts.append(f'\nCOMPANION_REPLY (already English — copy into subtitle_en):\n{spoken}')
        if need_title and user:
            parts.append(f"\nUSER_MESSAGE_FOR_TITLE:\n{user}")
        else:
            parts.append('\nSet title_en to "".')

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You translate UI chrome to clear English. JSON only.",
                    },
                    {"role": "user", "content": "\n".join(parts)},
                ],
                temperature=0.2,
                max_tokens=900,
                response_format={"type": "json_object"},
            )
            raw = (completion.choices[0].message.content or "").strip()
            import json

            data = json.loads(raw)
            sub = str(data.get("subtitle_en") or "").strip() or spoken
            title = str(data.get("title_en") or "").strip() or None
            if need_title and not title:
                title = "New conversation"
            if title and len(title) > 48:
                title = title[:48].rstrip() + "…"
            if not need_title:
                title = None
            return sub, title
        except Exception:  # noqa: BLE001
            logger.warning("english_ui translate failed; falling back", exc_info=True)
            title = "New conversation" if need_title else None
            return spoken, title

    def roman_hinglish_ui(
        self,
        spoken_reply: str,
        user_message: str | None = None,
        need_title: bool = False,
    ) -> tuple[str, str | None]:
        """On-screen copy for UI Hinglish: Hindi–English code-switching.

        Spoken reply stays Devanagari Hindi for TTS (same as Hindi mode);
        captions/chat use informal code-switching Hinglish only.
        """
        spoken = (spoken_reply or "").strip()
        if not spoken:
            return "", "New conversation" if need_title else None

        user = (user_message or "").strip()
        if not self.available:
            return spoken, ("New conversation" if need_title else None)

        # Rough sentence count so the rewrite can stay voice-aligned.
        spoken_sents = [
            s.strip()
            for s in re.split(r"(?<=[.!?।…])\s+", spoken)
            if s.strip()
        ]
        sent_n = max(len(spoken_sents), 1)

        parts = [
            "Return ONLY compact JSON, no markdown:",
            '{"subtitle_hinglish":"...","title_en":"..."}',
            "",
            "Rules:",
            "- subtitle_hinglish: faithful rewrite of the SAME companion reply as "
            "natural code-switching Hinglish — Hindi (Roman letters) AND English "
            "mixed inside the same sentences (everyday Indian speech).",
            "  Style examples (match this MIX, not these words):",
            '    "I\'m thoda busy right now."',
            '    "Kal we\'ll meet at the mall."',
            '    "Yeh movie was amazing!"',
            '    "Scene kya hai?"',
            '    "Please light band kar do."',
            "  Accuracy:",
            "  - Same meaning beat-for-beat. Do not add or drop ideas.",
            f"  - Keep about {sent_n} sentence(s), SAME order as the Hindi reply.",
            "  - End each sentence with the same punctuation rhythm when possible.",
            "  Do NOT output pure English translation.",
            "  Do NOT output pure Roman Hindi only (avoid 'tum akela nahi ho' "
            "with zero English).",
            "  Keep meaning, names, and Gita refs (e.g. Bhagavad Gita 2.47).",
            "  Keep teaching anchors: Parth, dharma, karma, moha, atma.",
            "  Use tum (not aap). Natural, warm, spoken — not slang spam.",
            "- title_en: 3–7 word English sidebar title for the USER message theme.",
            "  No quotes. No trailing period.",
            f"\nCOMPANION_REPLY_HINDI:\n{spoken}",
        ]
        if need_title and user:
            parts.append(f"\nUSER_MESSAGE_FOR_TITLE:\n{user}")
        else:
            parts.append('\nSet title_en to "".')

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You rewrite Hindi into accurate code-switching Hinglish "
                            "for on-screen subtitles while voice stays Hindi. "
                            "Mix Roman Hindi + English in the same sentence. "
                            "Preserve meaning and sentence count/order. "
                            "Never pure English. Never pure Roman Hindi. JSON only."
                        ),
                    },
                    {"role": "user", "content": "\n".join(parts)},
                ],
                temperature=0.2,
                max_tokens=900,
                response_format={"type": "json_object"},
            )
            raw = (completion.choices[0].message.content or "").strip()
            import json

            data = json.loads(raw)
            sub = (
                str(data.get("subtitle_hinglish") or data.get("subtitle_roman") or "")
                .strip()
                or spoken
            )
            title = str(data.get("title_en") or "").strip() or None
            if need_title and not title:
                title = "New conversation"
            if title and len(title) > 48:
                title = title[:48].rstrip() + "…"
            if not need_title:
                title = None
            return sub, title
        except Exception:  # noqa: BLE001
            logger.warning("roman_hinglish_ui failed; falling back", exc_info=True)
            title = "New conversation" if need_title else None
            return spoken, title

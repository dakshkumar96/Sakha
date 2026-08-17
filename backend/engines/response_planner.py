"""Response planner — combines engine outputs + session state into a turn plan.
This is the only place that decides `use_verse_now`.

Teach gate (system_v1.txt §5): do not teach until
  - not in crisis L2-L4,
  - at least `teach_gate_min_questions` companion questions have been asked
    this session, OR the user is seeking guidance after one honest check,
  - no unaddressed defence (spiritual bypass forces a redirect),
  - listen-first emotions (grief etc.) delay further.

Phase 5: instructions are structured templates carrying the actual engine
readings, not thin one-liners. A planner string like "ask a question" produces
generic output; the model needs to know *what was detected* to be specific.

turn_action: "crisis" | "crisis_soft" | "witness" | "question" | "validate" | "teach"
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.engines.appraisal_analyzer import AppraisalResult
from backend.engines.crisis_detector import CrisisResult
from backend.engines.defence_detector import DefenceResult
from backend.engines.emotion_analyzer import EmotionResult
from backend.engines.guna_detector import GunaResult
from backend.engines.intent_detector import IntentResult
from backend.engines.language import mirror_instruction
from backend.memory.session_store import SessionState


@dataclass
class TurnPlan:
    turn_action: str
    style: str
    use_verse_now: bool
    tone: str
    instruction: str
    ask_question: bool = False


LISTEN_FIRST_EMOTIONS = {
    "grief_loss",
    "existential_terror",
    "fear_of_death",
    "faith_wavering",
}

_GUNA_TONE = {
    "tamas": "They sound heavy and low-energy. Keep sentences short and warm; do not pile on tasks.",
    "rajas": "They sound agitated and driven. Stay slow and steady; do not match their speed.",
    "sattva": "They sound relatively clear. You can go deeper without much cushioning.",
    "unclear": "",
}


def _reading(
    emotion: EmotionResult,
    intent: IntentResult,
    appraisal: AppraisalResult,
    defence: DefenceResult,
    guna: GunaResult,
    session: SessionState,
    lang: str,
) -> str:
    """The engines' reading of this turn, handed to the model as context.

    This is analysis for the model's use only — it must never be recited back
    to the user (persona rule: intelligence is invisible, no "I notice you
    always...").
    """
    bits = [f"- language: {lang} — {mirror_instruction(lang)}"]

    if emotion.primary:
        secondary = f" (also: {', '.join(emotion.secondary)})" if emotion.secondary else ""
        bits.append(
            f"- detected emotion: {emotion.primary}{secondary} "
            f"[intensity {emotion.intensity}/10, confidence {emotion.confidence:.2f}]"
        )
    else:
        bits.append("- detected emotion: unclear — do not guess loudly; ask.")

    bits.append(f"- intent: {intent.intent}")

    appraisal_bits = []
    if appraisal.control:
        appraisal_bits.append(f"control felt as {appraisal.control}")
    if appraisal.agency:
        appraisal_bits.append(f"agency attributed to {appraisal.agency}")
    if appraisal.fairness_violated:
        appraisal_bits.append("they feel this is unfair")
    if appraisal_bits:
        bits.append(f"- appraisal: {'; '.join(appraisal_bits)}")

    defences = [
        name
        for name, on in (
            ("spiritual bypass", defence.spiritual_bypass),
            ("minimisation", defence.minimisation),
            ("intellectualisation", defence.intellectualisation),
        )
        if on
    ]
    if defences:
        bits.append(f"- defence in play: {', '.join(defences)}")

    guna_line = _GUNA_TONE.get(guna.dominant, "")
    if guna_line:
        bits.append(f"- energy: {guna_line}")

    bits.append(
        f"- session so far: turn {session.turn_count + 1}, "
        f"{session.questions_asked} question(s) already asked by you, "
        f"depth_level {session.depth_level()}"
    )
    if session.depth_level() >= 3:
        bits.append(
            "- session depth: they have stayed and disclosed across several turns — "
            "weight toward WARM specificity; do not treat this like turn 1."
        )
    if session.metaphors_delivered:
        bits.append(
            "- metaphors already used (forbidden to reuse): "
            + ", ".join(sorted(session.metaphors_delivered))
        )

    return (
        "[ENGINE READING — for your judgement only. NEVER recite this back, "
        "never say 'I detect' or 'I notice you always'.]\n" + "\n".join(bits)
    )


def plan(
    crisis: CrisisResult,
    emotion: EmotionResult,
    intent: IntentResult,
    appraisal: AppraisalResult,
    defence: DefenceResult,
    guna: GunaResult,
    session: SessionState,
    teach_gate_min_questions: int = 2,
    lang: str = "en",
) -> TurnPlan:
    reading = _reading(emotion, intent, appraisal, defence, guna, session, lang)

    def build(directive: str) -> str:
        return f"{reading}\n\n[THIS TURN]\n{directive}"

    # 1. Crisis wins. L3/L4 short-circuit upstream with a fixed string and never
    #    reach here. L1/L2 stay conversational but teaching is off.
    if crisis.level == "L2":
        return TurnPlan(
            turn_action="crisis_soft",
            style="crisis_soft_l2",
            use_verse_now=False,
            tone="steady_calm",
            instruction=build(
                "They have expressed passive thoughts of not wanting to be here, with no "
                "plan. Respond with warmth and real concern, in their language.\n"
                "1. Say plainly that what they said matters and you are not brushing past it.\n"
                "2. Ask directly but gently how they are doing right now.\n"
                "3. Mention that support is there if it ever feels unsafe — one line, not alarmist.\n"
                "FORBIDDEN: any verse, any citation, karma/detachment/'meant to be' language, "
                "any suggestion that this is a lesson."
            ),
        )

    if crisis.level == "L1":
        return TurnPlan(
            turn_action="crisis_soft",
            style="crisis_soft_l1",
            use_verse_now=False,
            tone="gentle",
            instruction=build(
                "They sound hopeless or emotionally exhausted, with no sign of danger.\n"
                "1. Name the specific heaviness they described, in their own terms.\n"
                "2. Ask one genuine question about what is weighing most.\n"
                "FORBIDDEN: verses, citations, philosophy, silver linings."
            ),
        )

    # 2. Defence forces a redirect to something concrete before any teaching.
    if defence.any_defence:
        return TurnPlan(
            turn_action="question",
            style="redirect_to_concrete",
            use_verse_now=False,
            tone="gentle",
            instruction=build(
                "They are using philosophy or dismissal to stay away from a feeling.\n"
                "1. Gently name that the framing they used may be holding something at arm's length.\n"
                "2. Ask one grounded question about what actually happened, to a real person, "
                "at a real time.\n"
                "FORBIDDEN: agreeing with the bypass, quoting scripture that reinforces it, "
                "teaching this turn."
            ),
        )

    # 3. Pushback -> validate before redirecting. Confirmed design gap: on a
    # SECOND consecutive pushback, repeating "validate then continue teaching
    # the same way" is the exact failure a person in distress notices
    # fastest — agreeing verbally and then changing nothing. Force a real
    # strategy change instead of a bigger, more careful version of the same
    # thing that already didn't land.
    if intent.intent == "pushing_back" and session.pushback_streak >= 1:
        return TurnPlan(
            turn_action="question",
            style="reset_check_in",
            use_verse_now=False,
            tone="steady_calm",
            instruction=build(
                "They have pushed back AGAIN — this is at least the second time in this "
                "session that what you offered didn't land for them. Agreeing and then "
                "repeating the same shape (acknowledge → metaphor → verse → agency) is "
                "itself the problem now; do not do it again.\n"
                "1. Drop the framework entirely this turn. No verse, no physical image, "
                "no teaching.\n"
                "2. Say plainly, in ONE short sentence, that what you tried isn't working "
                "for them.\n"
                "3. Ask ONE direct, concrete question: what would actually help them right "
                "now — not a diagnostic mirror question, a real practical one.\n"
                "Keep the whole reply SHORT — this is a reset, not another attempt at depth.\n"
                "FORBIDDEN: any verse, any physical image/metaphor, restating your framework, "
                "explaining why the Gita approach is right, more than 3 sentences total."
            ),
        )

    if intent.intent == "pushing_back":
        return TurnPlan(
            turn_action="validate",
            style="validate_then_redirect",
            use_verse_now=session.questions_asked >= 1,
            tone="steady_calm",
            instruction=build(
                "They are pushing back on you or on the Gita.\n"
                "1. Take the objection seriously and say what is fair in it — genuinely, "
                "not as a rhetorical move before disagreeing.\n"
                "2. Only then offer the other side, if you have something real to offer.\n"
                "FORBIDDEN: defensiveness, wounded tone, insisting they will understand later."
            ),
        )

    listen_first = emotion.primary in LISTEN_FIRST_EMOTIONS

    # 4. Curiosity without distress can be answered directly.
    if intent.intent == "curiosity" and emotion.confidence < 0.5:
        return TurnPlan(
            turn_action="teach",
            style="cite_freely",
            use_verse_now=True,
            tone="instructive_firm",
            instruction=build(
                "This is curiosity, not distress. Answer the question cleanly and warmly, "
                "using the retrieved verse. Keep it human, not encyclopaedic. One light "
                "check-in question at the end is fine."
            ),
        )

    gate_open = session.questions_asked >= teach_gate_min_questions or (
        intent.intent == "seeking_guidance" and session.questions_asked >= 1
    )

    # 5. Listen-first emotions: sit before anything else.
    if listen_first and session.questions_asked < 1:
        return TurnPlan(
            turn_action="witness",
            style="sit_with_it",
            use_verse_now=False,
            tone="gentle",
            instruction=build(
                "This is grief or existential fear. Sit with it.\n"
                "1. Acknowledge the specific loss or fear they named — the person, the thing, "
                "not 'your situation'.\n"
                "2. One soft question, or none at all if silence serves better.\n"
                "FORBIDDEN: any verse, 'they are in a better place', eternal-soul philosophy, "
                "anything that shortens their grief."
            ),
            ask_question=True,
        )

    if gate_open and not listen_first:
        depth = session.depth_level()
        warm_bias = ""
        if depth >= 3:
            warm_bias = (
                "\nSESSION DEPTH: this is not a first disclosure. Prefer Warm register "
                "weight — name the specific stakes they have revealed across turns. "
                "Do not restart the same acknowledge→metaphor→verse scaffolding as if "
                "you just met them.\n"
            )
        variety = (
            "SHAPE VARIETY: do not always use acknowledge → metaphor → verse → अर्थात → "
            "agency → पार्थ. Rotate: sometimes hard truth first; sometimes image first; "
            "sometimes Warm only with no image; never close on an address word.\n"
        )
        return TurnPlan(
            turn_action="teach",
            style="teach_warm" if depth >= 3 else "teach",
            use_verse_now=True,
            tone="gentle" if depth >= 3 or intent.intent == "venting" else "instructive_firm",
            instruction=build(
                f"{warm_bias}{variety}"
                "The teach gate is open. Teach now:\n"
                "1. HARD TRUTH — name what they have been circling. Attack the stuck story, "
                "never their worth. Statement, not a soft question.\n"
                "2. Optionally ONE fresh physical image (constitution bank) — skip if Warm "
                "alone serves, and NEVER reuse an image already used this session.\n"
                "3. Weave the retrieved verse as narrative. FORBIDDEN announce formulas: "
                "'भगवद्गीता के … अध्याय के … श्लोक में कहा गया है', 'As chapter X verse Y states'. "
                "Quiet tag only if needed: 'भगवद्गीता 2.47' / 'Bhagavad Gita 2.47'. "
                "Prefer citing ONE verse even if two were retrieved.\n"
                "4. Implication (अर्थात) and RETURN AGENCY.\n"
                "Address word: at most one, MID-reply only — never the last word.\n"
                "FORBIDDEN: 'you got this', 'everything happens for a reason', bullet lists, "
                "generic life advice, verse shopping lists, closing with पार्थ।"
            ),
        )

    if gate_open and listen_first and session.questions_asked >= teach_gate_min_questions:
        return TurnPlan(
            turn_action="teach",
            style="teach_delayed",
            use_verse_now=True,
            tone="gentle",
            instruction=build(
                "Enough listening has happened that a teaching can land, but this is grief or "
                "deep fear — do not rush past the feeling.\n"
                "1. Acknowledge what they have been carrying, specifically.\n"
                "2. Offer the retrieved verse gently, as something to sit beside them, not as "
                "an answer that closes the subject.\n"
                "3. Leave the door open rather than prescribing.\n"
                "FORBIDDEN: brisk hard truth, 'time heals', treating the verse as a fix."
            ),
        )

    # 6. Default: explore the knot.
    return TurnPlan(
        turn_action="question",
        style="explore",
        use_verse_now=False,
        tone="gentle",
        instruction=build(
            "Still listening — the gate is not open yet. Give a FULL companion reply, "
            "not a single thin line.\n"
            "Structure (all three required):\n"
            "1. MIRROR — 1–2 complete sentences restating their actual situation in their "
            "words/people/stakes. Not 'that sounds hard'.\n"
            "2. UNDERSIDE — 1–2 complete sentences naming what feels stuck underneath "
            "(pressure from many sides, not knowing which pain is first, etc.).\n"
            "3. ONE real diagnostic question that digs into that knot.\n"
            "Write at least 3 complete sentences (4–6 is better). Never cut a sentence short.\n"
            "FORBIDDEN: any verse or citation, multiple questions, empty sympathy, "
            "one-line mirrors that trail off."
        ),
        ask_question=True,
    )

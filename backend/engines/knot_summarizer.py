"""Knot summarizer — a short structured LLM call between the engines and the
planner.

The lexicon engines see *words*. This sees the **knot**: what is actually stuck
underneath what was said. It exists because short follow-ups ("yes, exactly",
"batao kya karun") carry no lexicon signal at all, yet they are usually the turn
right before teaching — the moment specificity matters most.

Hard constraints:
  - It MUST NOT emit verse ids. Retrieval owns citations; letting a free-text
    step name verses would route around the citation wall.
  - It never overrides crisis. Crisis is lexicon-only, decided before this runs.
  - Any failure degrades to an empty knot and the lexicon path continues
    unchanged. This is an enhancement, never a dependency.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("krishna.knot")

# Hidden-knot vocabulary. A closed set keeps the output usable by the planner
# and stops the model inventing categories nothing downstream understands.
KNOT_KINDS = [
    "attachment_to_outcome",
    "shame_about_identity",
    "guilt_about_an_act",
    "fear_of_a_result",
    "loneliness",
    "grief",
    "duty_in_conflict",
    "anger_at_injustice",
    "loss_of_meaning",
    "need_for_approval",
    "exhaustion",
    "doubt_about_the_divine",
    "unclear",
]

_SCHEMA_PROMPT = """You are an analysis step inside a companion app grounded in the Bhagavad Gita.
Read the conversation and name what is actually stuck underneath what the person said.

Return ONLY a JSON object, no prose, with exactly these keys:
{{
  "surface": "<what they said they feel, one short clause>",
  "hidden_knot": "<one of: {kinds}>",
  "appraisal": {{"control": "low|high|unclear", "fairness": "violated|intact|unclear"}},
  "language": "en|hi|hinglish",
  "teach_ready_hint": true|false
}}

Rules:
- NEVER include any Bhagavad Gita verse, chapter number, verse number, or BG id.
- "teach_ready_hint" is true only if they have said enough that a hard truth would land.
- If you cannot tell, use "unclear". Do not guess confidently.
"""

_BG_PATTERN = re.compile(r"\b(BG[_\s]?\d|chapter\s+\d+|verse\s+\d+|\d+[.:]\d+)\b", re.IGNORECASE)


@dataclass
class Knot:
    surface: str = ""
    hidden_knot: str = "unclear"
    control: str = "unclear"
    fairness: str = "unclear"
    language: str = "en"
    teach_ready_hint: bool = False
    available: bool = False
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "surface": self.surface,
            "hidden_knot": self.hidden_knot,
            "appraisal": {"control": self.control, "fairness": self.fairness},
            "language": self.language,
            "teach_ready_hint": self.teach_ready_hint,
        }

    def as_instruction(self) -> str:
        if not self.available:
            return ""
        bits = [f"- surface: {self.surface}"] if self.surface else []
        bits.append(f"- hidden knot: {self.hidden_knot}")
        if self.control != "unclear":
            bits.append(f"- control felt as: {self.control}")
        if self.fairness == "violated":
            bits.append("- they feel this is unfair")
        return (
            "[KNOT — deeper read of what is stuck. Speak TO this, never name it "
            "clinically, never say 'your knot is'.]\n" + "\n".join(bits)
        )

    def retrieval_hint(self) -> str:
        """Extra text folded into the semantic query."""
        if not self.available:
            return ""
        parts = [self.surface, self.hidden_knot.replace("_", " ")]
        return " ".join(p for p in parts if p)


def _strip_verse_leakage(data: dict) -> dict:
    """Defence in depth: drop any field that smuggled in a citation."""
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str) and _BG_PATTERN.search(value):
            logger.warning("Knot summarizer emitted verse-like text in %r; dropping", key)
            cleaned[key] = ""
        else:
            cleaned[key] = value
    return cleaned


def summarize(
    client,
    model: str,
    user_message: str,
    history: list[dict],
    max_tokens: int = 220,
) -> Knot:
    """Returns a Knot. Always safe to call — failures yield available=False."""
    if client is None:
        return Knot()

    recent = history[-4:]
    transcript = "\n".join(
        f"{'User' if h.get('role') == 'user' else 'Companion'}: {h.get('content','')}"
        for h in recent
    )
    transcript = f"{transcript}\nUser: {user_message}" if transcript else f"User: {user_message}"

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": _SCHEMA_PROMPT.format(kinds=", ".join(KNOT_KINDS)),
                },
                {"role": "user", "content": transcript},
            ],
            temperature=0.2,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content or "{}"
        data = _strip_verse_leakage(json.loads(raw))
    except Exception:  # noqa: BLE001 - enhancement only, never a dependency
        logger.warning("Knot summarizer unavailable; continuing on lexicon path", exc_info=True)
        return Knot()

    appraisal = data.get("appraisal") or {}
    knot_kind = data.get("hidden_knot", "unclear")
    if knot_kind not in KNOT_KINDS:
        knot_kind = "unclear"

    return Knot(
        surface=str(data.get("surface", ""))[:200],
        hidden_knot=knot_kind,
        control=str(appraisal.get("control", "unclear")),
        fairness=str(appraisal.get("fairness", "unclear")),
        language=str(data.get("language", "en")),
        teach_ready_hint=bool(data.get("teach_ready_hint", False)),
        available=True,
        raw=data,
    )

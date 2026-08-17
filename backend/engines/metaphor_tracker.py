"""Detect metaphor-bank images already used in this conversation.

Used to stop the same fist/Ganga or coal/diamond image recurring within a
session. Detection is phrase-level over assistant history — good enough to
steer the planner without a second LLM call.
"""
from __future__ import annotations

# id -> surface phrases (HI + EN). Match is casefold substring.
METAPHOR_BANK: dict[str, tuple[str, ...]] = {
    "fist_ganga": (
        "मुट्ठी",
        "खुली हथेली",
        "गंगा",
        "closed fist",
        "open palm",
        "ganga",
    ),
    "worn_clothes": (
        "पुराना वस्त्र",
        "नया धारण",
        "worn clothes",
        "changing clothes",
        "old clothes",
    ),
    "oil_water": (
        "तेल उड़",
        "oil evaporat",
        "water remains",
    ),
    "sky_rain": (
        "बारिश से पहले",
        "dirty before rain",
        "sky dirty",
    ),
    "leaves": (
        "पत्तियाँ गिर",
        "leaves falling",
        "few leaves",
    ),
    "chain": (
        "लोहे की",
        "सोने की श्रृंखला",
        "iron chain",
        "gold chain",
        "brass chain",
    ),
    "desire_cascade": (
        "कामना से तृष्णा",
        "desire → craving",
        "craving → anger",
    ),
    "ocean_drop": (
        "समुद्र में विलीन",
        "drop merging",
        "merging with the ocean",
    ),
    "lamp": (
        "दीपक",
        "lamp against",
        "deep darkness",
    ),
    "season": (
        "मौसम से पहले",
        "blooms before",
        "before its season",
    ),
    "coal_diamond": (
        "कोयला",
        "हीरा",
        "coal becoming",
        "coal into diamond",
        "under pressure",
    ),
    "hourglass": (
        "रेतघड़ी",
        "hourglass",
        "narrow present",
    ),
}

# Map emotion_response metaphor_ref substrings -> bank ids
_REF_TO_ID: tuple[tuple[str, str], ...] = (
    ("fist", "fist_ganga"),
    ("ganga", "fist_ganga"),
    ("worn clothes", "worn_clothes"),
    ("changing worn", "worn_clothes"),
    ("oil", "oil_water"),
    ("sky dirty", "sky_rain"),
    ("leaves", "leaves"),
    ("chain", "chain"),
    ("desire", "desire_cascade"),
    ("ocean", "ocean_drop"),
    ("lamp", "lamp"),
    ("season", "season"),
    ("blooms", "season"),
    ("coal", "coal_diamond"),
    ("diamond", "coal_diamond"),
    ("hourglass", "hourglass"),
)


def metaphor_id_from_ref(ref: str | None) -> str | None:
    if not ref:
        return None
    low = ref.casefold()
    for needle, mid in _REF_TO_ID:
        if needle in low:
            return mid
    return None


def detect_metaphors_in_text(text: str) -> set[str]:
    if not text:
        return set()
    low = text.casefold()
    hit: set[str] = set()
    for mid, phrases in METAPHOR_BANK.items():
        for p in phrases:
            if p.casefold() in low:
                hit.add(mid)
                break
    return hit


def metaphors_from_history(history: list[dict], lookback: int = 12) -> set[str]:
    """Union of metaphor bank hits in recent assistant turns."""
    found: set[str] = set()
    assistants = [h.get("content", "") for h in history if h.get("role") == "assistant"]
    for content in assistants[-lookback:]:
        found |= detect_metaphors_in_text(content)
    return found


def avoid_instruction(used: set[str]) -> str:
    if not used:
        return ""
    labels = {
        "fist_ganga": "closed fist / open palm in the Ganga",
        "worn_clothes": "changing worn clothes",
        "oil_water": "oil evaporates, water remains",
        "sky_rain": "sky dirty before rain",
        "leaves": "a few leaves falling",
        "chain": "iron/brass/gold chain",
        "desire_cascade": "desire → craving → anger cascade",
        "ocean_drop": "drop merging with the ocean",
        "lamp": "lamp against darkness",
        "season": "nothing blooms before its season",
        "coal_diamond": "coal becoming diamond under pressure",
        "hourglass": "the hourglass / narrow present",
    }
    names = [labels.get(m, m) for m in sorted(used)]
    return (
        "[ALREADY USED THIS SESSION — DO NOT REUSE]\n"
        "These physical images were already delivered. Choose a DIFFERENT image "
        "from the constitution metaphor bank, or skip the image if none fit:\n- "
        + "\n- ".join(names)
    )

"""Intent detection — runs parallel to emotion analysis.

Enums per product doc §7: venting, seeking_guidance, questioning_god,
pushing_back, curiosity.
"""
from __future__ import annotations

from dataclasses import dataclass

_MARKERS: dict[str, list[str]] = {
    "pushing_back": [
        "that's not helpful", "you don't get it", "that's easy for you to say",
        "i disagree", "that doesn't apply to me", "whatever", "sure, right",
        # Hindi / Hinglish
        "yeh gita kaam nahi karta", "galat hai yeh", "tum samajhte nahi",
        "aasan hai kehna", "bakwas", "यह काम नहीं करता", "तुम समझते नहीं",
    ],
    "questioning_god": [
        "why would god", "does god even care", "is there even a god",
        "why does god allow", "angry at god", "doubt there is a god",
        # Hindi / Hinglish
        "bhagwan hai kya", "bhagwan hote to", "insaf kahan", "bhagwan ko dikhta nahi",
        "भगवान है क्या", "इंसाफ कहाँ", "भगवान क्यों",
    ],
    "curiosity": [
        "just curious", "wondering about", "what does the gita say",
        "out of interest", "just asking",
        # Hindi / Hinglish
        "gita mein kya likha", "gita kya kehti", "matlab kya hai",
        "bas jaanna tha", "गीता में क्या", "मतलब क्या है",
    ],
    "seeking_guidance": [
        "what should i do", "how do i", "help me figure out", "need advice",
        "what would krishna say", "give me guidance", "just give me the verse",
        # Hindi / Hinglish
        "batao kya karun", "kya karun main", "raasta chahiye", "gita se kuch",
        "salah chahiye", "madad chahiye", "बताओ क्या करूँ", "रास्ता चाहिए",
        "क्या करूँ मैं",
    ],
    "venting": [
        "i just need to vent", "just need to get this out",
        "not looking for advice", "just listen",
        # Hindi / Hinglish
        "bas sunkar", "sirf bolna tha", "koi answer mat do", "bas sun lo",
        "salah nahi chahiye", "बस सुन लो", "सिर्फ बोलना था",
    ],
}


@dataclass
class IntentResult:
    intent: str = "seeking_guidance"
    confidence: float = 0.3


def detect(text: str) -> IntentResult:
    lowered = text.lower()
    scores = {}
    for intent, phrases in _MARKERS.items():
        hits = sum(1 for p in phrases if p in lowered)
        if hits:
            scores[intent] = hits

    if not scores:
        # Default: question mark => seeking guidance; long emotional share => venting
        if "?" in text:
            return IntentResult(intent="seeking_guidance", confidence=0.3)
        return IntentResult(intent="venting", confidence=0.3)

    top = max(scores.items(), key=lambda kv: kv[1])
    confidence = min(1.0, 0.5 + 0.15 * top[1])
    return IntentResult(intent=top[0], confidence=confidence)

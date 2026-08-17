"""Defence-lite: spiritual bypass, minimisation, intellectualisation.

When detected, the planner is forced toward a question/bring-personal
turn rather than teaching — per persona forbidden_behaviours (no
spiritual bypass of acute pain) and situations_v1.json
`spiritual_bypass_risk: redirect_to_concrete`.
"""
from __future__ import annotations

from dataclasses import dataclass

_SPIRITUAL_BYPASS = [
    "it's all maya", "nothing matters anyway so whatever", "it's just karma",
    "everything happens for a reason so", "detachment means i shouldn't feel",
    "just gotta let go of everything",
    # Hindi / Hinglish
    "sab maya hai", "sab moh maya", "karma ka khel hai", "sab bhagwan ki marzi",
    "prarabdh hai", "moh maya chhod di", "sab kuch maya",
    "सब माया है", "सब मोह माया", "भगवान की मर्ज़ी", "कर्मों का खेल",
]
_MINIMISATION = [
    "it's not a big deal", "i'm fine, really", "it's nothing",
    "i shouldn't even be talking about this", "other people have it worse",
    # Hindi / Hinglish
    "koi badi baat nahi", "main thik hoon", "kuch nahi hai",
    "logo ko isse zyada dukh", "chhodo yaar",
    "कोई बड़ी बात नहीं", "मैं ठीक हूँ", "कुछ नहीं है",
]
_INTELLECTUALISATION = [
    "philosophically speaking", "objectively analyzing this",
    "from a purely logical standpoint", "in theory this shouldn't bother me",
    # Hindi / Hinglish
    "logically dekha jaye", "theory me to", "darshan ke hisab se",
    "तार्किक रूप से", "सिद्धांत के हिसाब से",
]


@dataclass
class DefenceResult:
    spiritual_bypass: bool = False
    minimisation: bool = False
    intellectualisation: bool = False

    @property
    def any_defence(self) -> bool:
        return self.spiritual_bypass or self.minimisation or self.intellectualisation


def analyze(text: str) -> DefenceResult:
    lowered = text.lower()
    return DefenceResult(
        spiritual_bypass=any(p in lowered for p in _SPIRITUAL_BYPASS),
        minimisation=any(p in lowered for p in _MINIMISATION),
        intellectualisation=any(p in lowered for p in _INTELLECTUALISATION),
    )

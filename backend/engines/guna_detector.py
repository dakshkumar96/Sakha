"""Guna-lite: tamas / rajas / sattva keyword skew, used only to nudge the
planner's tone instruction string (never exposed as a diagnosis to the user).
"""
from __future__ import annotations

from dataclasses import dataclass

_TAMAS = ["can't get out of bed", "no energy at all", "numb", "don't care about anything", "stuck in bed", "heavy and dull"]
_RAJAS = ["can't stop moving", "restless and driven", "need to win", "competitive", "racing to get everything done", "agitated"]
_SATTVA = ["feel clear and calm", "at peace", "grateful and steady", "content"]


@dataclass
class GunaResult:
    dominant: str = "unclear"  # "tamas" | "rajas" | "sattva" | "unclear"


def analyze(text: str) -> GunaResult:
    lowered = text.lower()
    scores = {
        "tamas": sum(1 for p in _TAMAS if p in lowered),
        "rajas": sum(1 for p in _RAJAS if p in lowered),
        "sattva": sum(1 for p in _SATTVA if p in lowered),
    }
    top = max(scores.items(), key=lambda kv: kv[1])
    return GunaResult(dominant=top[0] if top[1] > 0 else "unclear")

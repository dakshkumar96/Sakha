"""Appraisal-lite: control, agency, fairness signals that feed the
response planner's reframe hints (research/02 appraisal-first method).
"""
from __future__ import annotations

from dataclasses import dataclass

_CONTROL_LOW = ["out of my control", "can't control", "nothing i can do", "helpless", "no say in"]
_CONTROL_HIGH = ["i have to control", "need to control everything", "if i don't control this"]
_AGENCY_OTHER = ["they made me", "because of them", "it's their fault", "someone else decides for me"]
_AGENCY_SELF = ["i chose to", "i decided", "it's on me", "i did this to myself"]
_FAIRNESS_VIOLATED = ["it's not fair", "unfair", "i didn't deserve this", "why me", "undeserved"]


@dataclass
class AppraisalResult:
    control: str | None = None  # "low" | "high"
    agency: str | None = None  # "self" | "other"
    fairness_violated: bool = False


def analyze(text: str) -> AppraisalResult:
    lowered = text.lower()
    control = None
    if any(p in lowered for p in _CONTROL_LOW):
        control = "low"
    elif any(p in lowered for p in _CONTROL_HIGH):
        control = "high"

    agency = None
    if any(p in lowered for p in _AGENCY_SELF):
        agency = "self"
    elif any(p in lowered for p in _AGENCY_OTHER):
        agency = "other"

    fairness_violated = any(p in lowered for p in _FAIRNESS_VIOLATED)

    return AppraisalResult(control=control, agency=agency, fairness_violated=fairness_violated)

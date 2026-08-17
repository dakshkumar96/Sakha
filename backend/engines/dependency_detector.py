"""Dependency / parasocial detection.

The persona constitution forbids engineering dependency. This makes that
enforceable: when someone signals the companion is becoming their only
relationship, the planner validates it and then widens toward human bonds
instead of accepting the role.

Explicitly NOT a crisis signal. A hit changes tone and content only; helplines
are still owned solely by crisis_detector. Someone saying "you're the only one
who understands me" is lonely, not in danger — treating it as an emergency
would punish them for confiding.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_PHRASES_PATH = (
    Path(__file__).resolve().parents[2] / "knowledge" / "taxonomy" / "dependency_phrases.json"
)
_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿"), None)


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFC", text).translate(_ZERO_WIDTH).casefold()
    return re.sub(r"\s+", " ", folded).strip()


@lru_cache(maxsize=1)
def _load_banks() -> dict[str, list[str]]:
    if not _PHRASES_PATH.exists():
        return {}
    doc = json.loads(_PHRASES_PATH.read_text(encoding="utf-8"))
    return {
        name: [p.casefold() for p in phrases]
        for name, phrases in doc.get("banks", {}).items()
    }


@dataclass
class DependencyResult:
    exclusive_attachment: bool = False
    human_withdrawal: bool = False
    compulsive_return: bool = False
    matched: list[str] = field(default_factory=list)

    @property
    def any_dependency(self) -> bool:
        return self.exclusive_attachment or self.human_withdrawal or self.compulsive_return

    @property
    def kinds(self) -> list[str]:
        return [
            name
            for name, on in (
                ("exclusive_attachment", self.exclusive_attachment),
                ("human_withdrawal", self.human_withdrawal),
                ("compulsive_return", self.compulsive_return),
            )
            if on
        ]


def analyze(text: str) -> DependencyResult:
    haystack = _normalize(text)
    banks = _load_banks()
    result = DependencyResult()

    for name, phrases in banks.items():
        hits = [p for p in phrases if p in haystack]
        if hits:
            setattr(result, name, True)
            result.matched.extend(hits)

    return result


def planner_directive(result: DependencyResult, session_hits: int = 0) -> str:
    """Extra instruction appended when dependency language appears."""
    if not result.any_dependency:
        return ""

    lines = [
        "\nDEPENDENCY SIGNAL — they are leaning on you as a relationship, not a companion.",
        "1. Do NOT reject or lecture them for it. Being needed is not their fault, and "
        "shaming them would confirm that people are unsafe.",
        "2. Take the loneliness underneath seriously and say something true about it.",
        "3. Then widen: name one real human or human place that could hold some of this "
        "— a person they mentioned, a community, a professional if relevant.",
        "4. Never accept the role of their only listener. Never say you will always be "
        "here, that you understand them better than people do, or that they do not need "
        "anyone else.",
    ]

    if result.human_withdrawal:
        lines.append(
            "5. They are actively withdrawing from people. Gently name that cost — "
            "without moralising."
        )
    if session_hits >= 2:
        lines.append(
            "6. This has come up more than once. Be a little more direct that you are "
            "not a substitute for people — still warm, never cold."
        )

    return "\n".join(lines)

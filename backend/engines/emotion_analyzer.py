"""Lexicon-first emotion detection mapped onto knowledge/taxonomy/emotions_v1.json
emotion ids. Runs on the backend only (never the frontend), per product doc §7.

Phrase banks live in JSON (knowledge/taxonomy/emotion_lexicon_{en,hi}.json)
rather than hardcoded here, so Hindi/Hinglish coverage can grow without code
changes. V1 is keyword/phrase scoring, not a trained classifier — auditable
and free-tier friendly.

Crisis-flavoured ids (exhaustion_l1, hopelessness_l1, crisis_l2_plus) are
deliberately absent: backend.engines.crisis_detector owns crisis routing so
the two systems can never disagree.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_TAXONOMY = _ROOT / "knowledge" / "taxonomy"
_EMOTION_MAP = _ROOT / "prompts" / "emotion_response.json"
_LEXICON_FILES = ("emotion_lexicon_en.json", "emotion_lexicon_hi.json")

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿"), None)


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFC", text).translate(_ZERO_WIDTH).casefold()
    return re.sub(r"\s+", " ", folded).strip()


def _known_emotion_ids() -> set[str]:
    """Taxonomy v1 ids plus the 40 emotion-response map ids (both are valid labels)."""
    known: set[str] = set()
    emotions_path = _TAXONOMY / "emotions_v1.json"
    if emotions_path.exists():
        doc = json.loads(emotions_path.read_text(encoding="utf-8"))
        known = {e["id"] for e in doc.get("emotions", [])}
    if _EMOTION_MAP.exists():
        doc = json.loads(_EMOTION_MAP.read_text(encoding="utf-8"))
        known.update(e["id"] for e in doc.get("emotions", []) if e.get("id"))
    return known


@lru_cache(maxsize=1)
def _load_lexicon() -> dict[str, list[str]]:
    """Merge taxonomy banks + emotion_response what_people_say into one lexicon.

    Map ids are first-class (not dropped): they feed the generator craft card
    and preferred verse. Taxonomy files still require a known id so typos do
    not slip through.
    """
    known = _known_emotion_ids()
    merged: dict[str, list[str]] = {}

    for filename in _LEXICON_FILES:
        path = _TAXONOMY / filename
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        for emotion_id, phrases in doc.get("lexicon", {}).items():
            if known and emotion_id not in known:
                continue
            merged.setdefault(emotion_id, []).extend(p.casefold() for p in phrases)

    if _EMOTION_MAP.exists():
        doc = json.loads(_EMOTION_MAP.read_text(encoding="utf-8"))
        for card in doc.get("emotions", []):
            eid = card.get("id")
            if not eid:
                continue
            phrases = [p.casefold() for p in card.get("what_people_say") or [] if p]
            words = (card.get("linguistic_markers") or {}).get("words") or []
            phrases.extend(w.casefold() for w in words if w and len(str(w)) > 3)
            if phrases:
                merged.setdefault(eid, []).extend(phrases)

    return merged


def unknown_lexicon_ids() -> set[str]:
    """Ids present in a lexicon file but missing from taxonomy + emotion map.
    Surfaced by validation rather than failing at runtime."""
    known = _known_emotion_ids()
    if not known:
        return set()
    seen: set[str] = set()
    for filename in _LEXICON_FILES:
        path = _TAXONOMY / filename
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        seen.update(doc.get("lexicon", {}).keys())
    return seen - known


@dataclass
class EmotionResult:
    primary: str | None = None
    secondary: list[str] = field(default_factory=list)
    intensity: int = 5
    confidence: float = 0.0
    all_scores: dict[str, int] = field(default_factory=dict)


_INTENSITY_BOOSTERS = [
    "so ",
    "extremely ",
    "completely ",
    "totally ",
    "can't take it",
    "every day",
    "all the time",
    "bahut ",
    "bilkul ",
    "hamesha",
    "roz ",
    "बहुत ",
    "हमेशा",
]


def analyze(text: str) -> EmotionResult:
    lowered = _normalize(text)
    lexicon = _load_lexicon()

    scores: dict[str, int] = {}
    for emotion_id, phrases in lexicon.items():
        # Weight by phrase length so multi-word map exemplars beat lone keywords.
        score = 0
        for phrase in phrases:
            if phrase and phrase in lowered:
                score += max(1, len(phrase.split()))
        if score:
            scores[emotion_id] = score

    if not scores:
        return EmotionResult(primary=None, secondary=[], intensity=5, confidence=0.0, all_scores={})

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    primary = ranked[0][0]
    secondary = [eid for eid, _ in ranked[1:3]]

    total_hits = sum(scores.values())
    confidence = min(1.0, 0.4 + 0.15 * total_hits)

    intensity = 5 + sum(1 for b in _INTENSITY_BOOSTERS if b in lowered)
    intensity = max(1, min(10, intensity))

    return EmotionResult(
        primary=primary,
        secondary=secondary,
        intensity=intensity,
        confidence=confidence,
        all_scores=scores,
    )

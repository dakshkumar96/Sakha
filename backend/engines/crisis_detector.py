"""Crisis detector — always runs first, before any other engine or the LLM.

Levels (aligned with knowledge/taxonomy/crisis_forbidden.json and
prompts/system_v1.txt §5 crisis protocol):

  NONE  no crisis signal
  L1    hopeless / exhausted, no death ideation -> empathise, no verse dump
  L2    passive suicidal ideation / self-harm urge, no plan -> no teaching
  L3    means, intent, or finality language -> helplines only
  L4    L3 signal + immediacy ("tonight", "aaj raat") -> helplines only, urgent

Markers live in JSON (knowledge/taxonomy/crisis_markers_{en,hi}.json) rather
than hardcoded here, so the phrase banks can be reviewed and extended without
touching detection logic.

Lexicon-first by design: fast, auditable, and no model dependency in the
safety-critical path. Intentionally over-sensitive — a false positive routes
someone to care, which is a safe failure; a false negative is not.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_KNOWLEDGE = Path(__file__).resolve().parents[2] / "knowledge" / "taxonomy"
_MARKER_FILES = ("crisis_markers_en.json", "crisis_markers_hi.json")

_BANK_NAMES = (
    "hopeless",
    "passive_ideation",
    "means_and_intent",
    "goodbye_finality_language",
)

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿"), None)
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def normalize(text: str) -> str:
    """Fold text so roman Hinglish spelling drift doesn't defeat matching.

    Devanagari is left intact (NFC only) — the patterns for it are written
    literally.
    """
    folded = unicodedata.normalize("NFC", text).translate(_ZERO_WIDTH)
    folded = folded.casefold()
    return re.sub(r"\s+", " ", folded).strip()


def is_devanagari_majority(text: str) -> bool:
    """True when the message is written mostly in Devanagari script."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    deva = sum(1 for c in letters if _DEVANAGARI.match(c))
    return deva / len(letters) > 0.5


@lru_cache(maxsize=1)
def _load_markers() -> tuple[dict[str, list[re.Pattern]], list[re.Pattern]]:
    """Compile every marker bank across all language files."""
    banks: dict[str, list[re.Pattern]] = {name: [] for name in _BANK_NAMES}
    immediacy: list[re.Pattern] = []

    for filename in _MARKER_FILES:
        path = _KNOWLEDGE / filename
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        for name in _BANK_NAMES:
            for pattern in doc.get("banks", {}).get(name, []):
                banks[name].append(re.compile(pattern, re.IGNORECASE))
        for pattern in doc.get("immediacy", []):
            immediacy.append(re.compile(pattern, re.IGNORECASE))

    return banks, immediacy


@dataclass
class CrisisResult:
    level: str = "NONE"  # NONE | L1 | L2 | L3 | L4
    level_int: int = 0
    flags: set[str] = field(default_factory=set)
    matched_phrases: list[str] = field(default_factory=list)
    lang: str = "en"  # language to answer crisis in

    @property
    def blocks_teaching(self) -> bool:
        return self.level != "NONE"

    @property
    def helplines_only(self) -> bool:
        return self.level in ("L3", "L4")


def detect(text: str) -> CrisisResult:
    banks, immediacy_patterns = _load_markers()
    haystack = normalize(text)

    flags: set[str] = set()
    matched: list[str] = []

    for bank_name, patterns in banks.items():
        for pattern in patterns:
            m = pattern.search(haystack)
            if m:
                flags.add(bank_name)
                matched.append(m.group(0))

    has_means_or_finality = bool(flags & {"means_and_intent", "goodbye_finality_language"})
    has_immediacy = any(p.search(haystack) for p in immediacy_patterns)
    has_passive = "passive_ideation" in flags
    has_hopeless = "hopeless" in flags

    if has_means_or_finality and has_immediacy:
        level, level_int = "L4", 4
    elif has_means_or_finality:
        level, level_int = "L3", 3
    elif has_passive:
        level, level_int = "L2", 2
    elif has_hopeless:
        level, level_int = "L1", 1
    else:
        level, level_int = "NONE", 0

    return CrisisResult(
        level=level,
        level_int=level_int,
        flags=flags,
        matched_phrases=matched,
        lang="hi" if is_devanagari_majority(text) else "en",
    )


_HELPLINE_EN = (
    "What you are sharing sounds very serious, and I want to make sure you get real, "
    "immediate support — not words from an app.\n\n"
    "Please reach out right now:\n{refs}\n\n"
    "I am a digital companion presenting the Gita's teachings. I am not able to give you "
    "the human help you deserve in this moment, but the people at these numbers can."
)

_HELPLINE_HI = (
    "आप जो कह रहे हैं वह बहुत गंभीर है, और मैं चाहता हूँ कि आपको अभी असली मदद मिले — "
    "किसी ऐप के शब्द नहीं।\n\n"
    "कृपया अभी संपर्क करें:\n{refs}\n\n"
    "मैं गीता की शिक्षाओं पर आधारित एक डिजिटल साथी हूँ। इस पल में जो इंसानी सहारा आपको चाहिए, "
    "वह मैं नहीं दे सकता — लेकिन इन नंबरों पर बैठे लोग दे सकते हैं।"
)


def helpline_message(helpline_refs: list[str], lang: str = "en") -> str:
    """Fixed, vetted safety text. Never LLM-generated — an emergency is the
    last place to let a model improvise."""
    refs = "\n".join(f"- {ref}" for ref in helpline_refs)
    template = _HELPLINE_HI if lang == "hi" else _HELPLINE_EN
    return template.format(refs=refs)

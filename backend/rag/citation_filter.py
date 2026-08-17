"""Citation safety wall.

Rule (absolute, from persona + Phase 1 knowledge plan):
the model may only cite verse IDs that were actually retrieved for this
turn AND are present in the allowlist. Anything else the model writes
(an invented BG_x_y, or scripture recalled from its own weights on a
turn where no verse was retrieved) is stripped from the spoken text.

verse_citations returned to the UI are ONLY ids that actually appear in
the spoken reply — never every retrieved candidate. Otherwise the UI
shows verse cards for verses the companion never mentioned.
"""
from __future__ import annotations

import re
from pathlib import Path

_BG_ID_RE = re.compile(r"\bBG[_\s]?(\d{1,2})[_.,:](\d{1,3})\b", re.IGNORECASE)
_CHAPTER_VERSE_RE = re.compile(
    r"\b(?:Bhagavad\s+Gita,?\s+)?chapter\s+(\d{1,2})[,]?\s+verse\s+(\d{1,3})\b",
    re.IGNORECASE,
)
# Short spoken forms: "भगवद्गीता 2.47" / "Bhagavad Gita 2.47" / "Gita 2.47"
_SHORT_GITA_RE = re.compile(
    r"(?:भगवद्?\s*गीता|Bhagavad\s+Gita|Gita)\s*"
    r"(?:[,:]?\s*)?"
    r"(\d{1,2})\s*[.:、]\s*(\d{1,3})",
    re.IGNORECASE,
)
# Hindi long form: "अध्याय 2 ... श्लोक 47" (digits or later we only need digits)
_HI_ADHYAYA_SHLOKA_RE = re.compile(
    r"अध्याय\s*(\d{1,2})\s*(?:के|का|,)?\s*(?:सैं?तालीसवें|[^\d]{0,24})?"
    r"श्लोक\s*(?:संख्या\s*)?(\d{1,3})",
    re.IGNORECASE,
)
# "2.47" immediately after गीता / Gita already covered; bare "श्लोक 47" alone is ambiguous.

# Bare verse-only mentions with NO chapter — unverifiable against the allowlist
# and not useful to the user, so they get stripped like a fabricated citation
# rather than reaching the screen unchecked. Two forms:
#   - digit: "श्लोक 12" / "श्लोक संख्या 12"
#   - ordinal word: "बारहवें श्लोक" (Hindi ordinals from 4th on end in वें/वीं,
#     so this is a general pattern rather than an exhaustive word list)
_BARE_HI_SHLOKA_DIGIT_RE = re.compile(
    r"श्लोक\s*(?:संख्या\s*)?(\d{1,3})\b", re.IGNORECASE
)
_BARE_HI_SHLOKA_ORDINAL_RE = re.compile(
    r"[^\s।,]*(?:वें|वीं)\s+श्लोक(?:\s*में)?", re.IGNORECASE
)
_BARE_EN_VERSE_RE = re.compile(r"\b(?:in\s+)?verse\s+(\d{1,3})\b", re.IGNORECASE)
# A chapter mention anywhere nearby means the pair should already have been
# caught by _HI_ADHYAYA_SHLOKA_RE / _CHAPTER_VERSE_RE; only strip when isolated.
_NEARBY_CHAPTER_RE = re.compile(r"अध्याय|chapter", re.IGNORECASE)

# Cleanup for the wreckage a removed citation leaves behind.
_DANGLING_PATTERNS = [
    (re.compile(r"\bIn\s*,\s*", re.IGNORECASE), "In the Gita, "),
    (re.compile(r"\bin\s+it\s+is\s+written\b", re.IGNORECASE), "it is written"),
    (re.compile(r"भगवद्?\s*गीता\s*के\s*(?:[^\s।]{0,40})?में\s*कहा\s*गया\s*है\s*[—\-–:]?\s*", re.IGNORECASE), ""),
    (re.compile(r"\s{2,}"), " "),
    (re.compile(r"\s+([,.;:।])"), r"\1"),
    (re.compile(r"\(\s*\)"), ""),
]

# Trailing vocative — constitution §VI: never close a reply on an address word.
_TRAILING_ADDRESS_RE = re.compile(
    r"(?:,|\s)+("
    r"पार्थ|धनंजय|अर्जुन|हे\s*कौंतेय|हे\s*कुंती\s*पुत्र|हे\s*महाबाहु|"
    r"Partha|Dhananjaya|Arjuna"
    r")\s*[।.!]*\s*$",
    re.IGNORECASE | re.UNICODE,
)


def load_allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def _normalise(chapter: str | int, verse: str | int) -> str:
    return f"BG_{int(chapter)}_{int(verse)}"


def found_ids(text: str) -> set[str]:
    """Every verse id the text cites, in English or Hindi spoken forms."""
    ids: set[str] = set()
    for m in _BG_ID_RE.finditer(text):
        ids.add(_normalise(m.group(1), m.group(2)))
    for m in _CHAPTER_VERSE_RE.finditer(text):
        ids.add(_normalise(m.group(1), m.group(2)))
    for m in _SHORT_GITA_RE.finditer(text):
        ids.add(_normalise(m.group(1), m.group(2)))
    for m in _HI_ADHYAYA_SHLOKA_RE.finditer(text):
        ids.add(_normalise(m.group(1), m.group(2)))
    return ids


def _tidy(text: str) -> str:
    for pattern, replacement in _DANGLING_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()


def _complete_citation_spans(text: str) -> list[tuple[int, int]]:
    """Character ranges already covered by a validated chapter+verse citation
    — bare-mention stripping must not touch these."""
    spans: list[tuple[int, int]] = []
    for pattern in (_BG_ID_RE, _CHAPTER_VERSE_RE, _SHORT_GITA_RE, _HI_ADHYAYA_SHLOKA_RE):
        spans.extend((m.start(), m.end()) for m in pattern.finditer(text))
    return spans


def _overlaps(span: tuple[int, int], covered: list[tuple[int, int]]) -> bool:
    return any(span[0] < end and span[1] > start for start, end in covered)


def strip_incomplete_citations(text: str) -> str:
    """Remove verse-only mentions with no chapter number.

    'बारहवें श्लोक में' or 'in verse 12' cannot be checked against the
    allowlist and isn't verifiable by the user either — same treatment as a
    fabricated id: stripped rather than shown. A citation missing its chapter
    already correctly matched by _HI_ADHYAYA_SHLOKA_RE etc. is left alone.
    """
    covered = _complete_citation_spans(text)
    removals: list[tuple[int, int]] = []

    for pattern in (_BARE_HI_SHLOKA_DIGIT_RE, _BARE_HI_SHLOKA_ORDINAL_RE, _BARE_EN_VERSE_RE):
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            if _overlaps(span, covered):
                continue
            window_start = max(0, m.start() - 50)
            window_end = min(len(text), m.end() + 30)
            nearby = text[window_start : m.start()] + text[m.end() : window_end]
            if _NEARBY_CHAPTER_RE.search(nearby):
                continue  # a chapter is mentioned nearby (either order); leave it be
            removals.append(span)

    if not removals:
        return text

    removals.sort()
    out: list[str] = []
    cursor = 0
    for start, end in removals:
        if start < cursor:
            continue  # overlapping bare matches (rare) — keep the first
        out.append(text[cursor:start])
        cursor = end
    out.append(text[cursor:])
    return _tidy("".join(out))


def strip_trailing_address(text: str) -> str:
    """Remove a vocative that is the last word of the whole reply."""
    if not text:
        return text
    cleaned = _TRAILING_ADDRESS_RE.sub("", text).rstrip()
    # If we orphaned trailing punctuation spacing, tidy lightly.
    cleaned = re.sub(r"\s+([।.!])", r"\1", cleaned)
    return cleaned.strip()


def enforce_citations(
    text: str, retrieved_ids: list[str], allowlist: set[str]
) -> tuple[str, list[str]]:
    """Returns (corrected text, verse ids actually mentioned in the reply).

    Fabricated ids (outside retrieved ∩ allowlist) are stripped from text.
    UI citations = spoken ids ∩ allowed — never the full retrieval set.
    """
    allowed = set(retrieved_ids) & allowlist if allowlist else set(retrieved_ids)
    fabricated = found_ids(text) - allowed

    cleaned = text
    if fabricated:

        def drop_if_fabricated(match: re.Match) -> str:
            verse_id = _normalise(match.group(1), match.group(2))
            return "" if verse_id in fabricated else match.group(0)

        cleaned = _BG_ID_RE.sub(drop_if_fabricated, cleaned)
        cleaned = _CHAPTER_VERSE_RE.sub(drop_if_fabricated, cleaned)
        cleaned = _SHORT_GITA_RE.sub(drop_if_fabricated, cleaned)
        cleaned = _HI_ADHYAYA_SHLOKA_RE.sub(drop_if_fabricated, cleaned)
        cleaned = _tidy(cleaned)

    cleaned = strip_incomplete_citations(cleaned)
    cleaned = strip_trailing_address(cleaned)

    spoken = found_ids(cleaned) & allowed
    # Preserve retrieval order for stable cards.
    final_citations = [vid for vid in retrieved_ids if vid in spoken]
    return cleaned, final_citations

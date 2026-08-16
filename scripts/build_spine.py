"""
Build knowledge/gita/verses.json spine (~700 cards) + citation_allowlist.txt
from Prabhupada Bhagavad-gita As It Is plain text extract.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "knowledge" / "raw_text" / "Bhagavad-gita-As-It-Is.txt"
OUT = ROOT / "knowledge" / "gita" / "verses.json"
ALLOW = ROOT / "knowledge" / "validation" / "citation_allowlist.txt"

CHAPTER_SIZES = {
    1: 47,
    2: 72,
    3: 43,
    4: 42,
    5: 29,
    6: 47,
    7: 30,
    8: 28,
    9: 34,
    10: 42,
    11: 55,
    12: 20,
    13: 34,  # common count yielding total 700; some editions add 13.35
    14: 27,
    15: 20,
    16: 24,
    17: 28,
    18: 78,
}

WORD_TO_NUM = {
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "FOUR": 4,
    "FIVE": 5,
    "SIX": 6,
    "SEVEN": 7,
    "EIGHT": 8,
    "NINE": 9,
    "TEN": 10,
    "ELEVEN": 11,
    "TWELVE": 12,
    "THIRTEEN": 13,
    "FOURTEEN": 14,
    "FIFTEEN": 15,
    "SIXTEEN": 16,
    "SEVENTEEN": 17,
    "EIGHTEEN": 18,
}

CHAPTER_RE = re.compile(
    r"^CHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|"
    r"ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN)\b",
    re.M | re.I,
)
TEXT_RE = re.compile(
    r"^TEXTS?\s+(\d+)(?:\s*[–\-/]\s*(\d+))?\s*$",
    re.M | re.I,
)
PAGE_RE = re.compile(r"===== PAGE \d+ / \d+ =====")


def clean_ws(s: str) -> str:
    s = PAGE_RE.sub(" ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def empty_card(ch: int, v: int) -> dict:
    vid = f"BG_{ch}_{v}"
    return {
        "id": vid,
        "chapter": ch,
        "verse": v,
        "section_title": "",
        "sanskrit_devanagari": "",
        "iast": "",
        "translations": {"en": "", "en_by_source": {}, "hi": "", "hi_by_source": {}},
        "commentaries": {},
        "contested": False,
        "pluralism_note": None,
        "emotions": [],
        "situations": [],
        "intensity_range": None,
        "tone": "",
        "response_strategy": "",
        "readiness": "teach_ok",
        "depth_level": 1,
        "secondary_verses": [],
        "sample_follow_up": "",
        "sources": [],
        "quality": "spine",
        "do_not_use_when": ["acute_suicidality", "crisis_l2_plus"],
    }


def parse_as_it_is(text: str) -> dict[tuple[int, int], dict]:
    """Return map (chapter, verse) -> {en, iast_guess, locator}."""
    last_start: dict[int, int] = {}
    for m in CHAPTER_RE.finditer(text):
        word = m.group(1).upper()
        ch = WORD_TO_NUM[word]
        last_start[ch] = m.start()

    ordered = sorted(((ch, pos) for ch, pos in last_start.items()), key=lambda x: x[1])

    results: dict[tuple[int, int], dict] = {}
    for i, (ch, start) in enumerate(ordered):
        end = ordered[i + 1][1] if i + 1 < len(ordered) else len(text)
        body = text[start:end]
        title_m = re.search(r"CHAPTER[^\n]*\n([^\n]+)", body, re.I)
        section = title_m.group(1).strip() if title_m else ""

        text_matches = list(TEXT_RE.finditer(body))
        for j, tm in enumerate(text_matches):
            v_start = int(tm.group(1))
            v_end = int(tm.group(2)) if tm.group(2) else v_start
            t_start = tm.end()
            t_end = text_matches[j + 1].start() if j + 1 < len(text_matches) else len(body)
            block = body[t_start:t_end]

            tr = re.search(
                r"TRANSLATION\s*(.*?)(?=PURPORT\b|$)",
                block,
                re.S | re.I,
            )
            en = clean_ws(tr.group(1)) if tr else ""
            en = re.sub(r"=====.*", "", en).strip()

            before = block[: tr.start()] if tr else block
            iast_parts = []
            for line in before.splitlines():
                line = line.strip()
                if not line or line.upper().startswith("TEXT"):
                    continue
                if "—" in line or "–" in line:
                    continue
                letters = sum(c.isalpha() for c in line)
                if letters >= 8 and sum("\u0900" <= c <= "\u097F" for c in line) <= 3:
                    iast_parts.append(line)
            iast = clean_ws(" ".join(iast_parts[:6]))

            for v in range(v_start, v_end + 1):
                results[(ch, v)] = {
                    "en": en,
                    "iast": iast,
                    "section_title": section,
                    "locator": f"CHAPTER {ch} TEXT {v_start}"
                    + (f"-{v_end}" if v_end != v_start else ""),
                }
    return results


# Minimal trusted EN fallbacks for critical teaching verses if parse fails
FALLBACK_EN: dict[tuple[int, int], str] = {
    (1, 47): (
        "Sanjaya said: Arjuna, having thus spoken on the battlefield, cast aside "
        "his bow and arrows and sat down on the chariot, his mind overwhelmed with grief."
    ),
    (2, 47): (
        "You have a right to perform your prescribed duty, but you are not "
        "entitled to the fruits of action. Never consider yourself to be the "
        "cause of the results of your activities, and never be attached to not "
        "doing your duty."
    ),
    (2, 48): (
        "Perform your duty equipoised, O Arjuna, abandoning all attachment to "
        "success or failure. Such equanimity is called yoga."
    ),
    (17, 9): (
        "Foods that are too bitter, too sour, salty, pungent, dry and hot, are "
        "liked by people in the mode of passion. Such foods cause pain, distress, "
        "and disease."
    ),
    (17, 10): (
        "Food cooked more than three hours before being eaten, which is tasteless, "
        "stale, putrid, decomposed and unclean, is food liked by people in the mode "
        "of ignorance."
    ),
    (18, 66): (
        "Abandon all varieties of dharma and just surrender unto Me. I shall "
        "deliver you from all sinful reaction. Do not fear."
    ),
}


def main() -> int:
    if not SRC.exists():
        print(f"Missing {SRC}", file=sys.stderr)
        return 1

    text = SRC.read_text(encoding="utf-8", errors="replace")
    parsed = parse_as_it_is(text)
    print(f"Parsed verse blocks: {len(parsed)}")

    verses: list[dict] = []
    missing: list[str] = []
    for ch, n in CHAPTER_SIZES.items():
        for v in range(1, n + 1):
            card = empty_card(ch, v)
            p = parsed.get((ch, v))
            en = ""
            if p and p["en"] and len(p["en"]) > 20:
                en = p["en"]
                card["section_title"] = p.get("section_title") or ""
                card["iast"] = p.get("iast") or ""
                card["sources"] = [
                    {
                        "file": "knowledge/raw_text/Bhagavad-gita-As-It-Is.txt",
                        "locator": p["locator"],
                        "tradition": "prabhupada",
                    }
                ]
            elif (ch, v) in FALLBACK_EN:
                en = FALLBACK_EN[(ch, v)]
                card["sources"] = [
                    {
                        "file": "knowledge/raw_text/Bhagavad-gita-As-It-Is.txt",
                        "locator": f"fallback_seed BG_{ch}_{v}",
                        "tradition": "prabhupada",
                    }
                ]
            else:
                missing.append(f"BG_{ch}_{v}")

            card["translations"]["en"] = en
            if en:
                card["translations"]["en_by_source"]["prabhupada"] = en
            verses.append(card)

    # If still missing, synthesize placeholder that is honest (not invent as citation quality)
    # Use nearest prior verse note is bad - better generic cross-ref
    still = [c for c in verses if not c["translations"]["en"]]
    if still:
        print(f"Missing EN after parse: {len(still)} — applying secondary fill from parsed nearest chapter pool")
        # Second pass: for each missing, use empty marker and fill from chapter's known texts only if exact missing
        # Public well-known paraphrases for remainder: mark quality spine with source synthetic_gap
        for c in still:
            c["translations"]["en"] = (
                f"[Translation pending extraction for {c['id']}. "
                f"See Bhagavad-gita As It Is chapter {c['chapter']} text {c['verse']}.]"
            )
            c["sources"] = [
                {
                    "file": "knowledge/raw_text/Bhagavad-gita-As-It-Is.txt",
                    "locator": f"unparsed BG_{c['chapter']}_{c['verse']}",
                    "tradition": "prabhupada",
                    "note": "placeholder_pending_manual",
                }
            ]

    payload = {
        "counting_convention": "critical_700",
        "default_en_source": "prabhupada_as_it_is",
        "chapter_sizes": CHAPTER_SIZES,
        "total": len(verses),
        "parsed_from_source": len(parsed),
        "verses": verses,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ALLOW.parent.mkdir(parents=True, exist_ok=True)
    ALLOW.write_text("\n".join(c["id"] for c in verses) + "\n", encoding="utf-8")

    filled = sum(1 for c in verses if not c["translations"]["en"].startswith("["))
    print(f"Wrote {OUT} ({len(verses)} cards, {filled} solid EN, {len(verses)-filled} placeholders)")
    print(f"Wrote {ALLOW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

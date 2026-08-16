"""Build FAISS-ready jsonl chunk layers from verses, books, conversations."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "knowledge" / "chunks"
VERSES = ROOT / "knowledge" / "gita" / "verses.json"
TRAD = ROOT / "knowledge" / "gita" / "traditions_map.json"
EXAMPLES = ROOT / "docs" / "v1" / "persona" / "examples"
CONV = ROOT / "knowledge" / "Krishna_Conversations"


def verse_chunks(data: dict) -> list[dict]:
    out = []
    for v in data["verses"]:
        emo = ", ".join(v.get("emotions") or [])
        strat = v.get("response_strategy") or ""
        en = (v.get("translations") or {}).get("en") or ""
        embed = f"{v['id']}. Chapter {v['chapter']} verse {v['verse']}. {en}"
        if emo:
            embed += f" Emotions: {emo}."
        if strat:
            embed += f" Strategy: {strat}"
        out.append(
            {
                "chunk_id": f"verse:{v['id']}",
                "verse_id": v["id"],
                "layer": "verse",
                "embed_text": embed[:4000],
                "weight": 1.0 if v.get("quality") == "tier_a" else 0.85,
                "quality": v.get("quality"),
            }
        )
    return out


def book_chunks() -> list[dict]:
    trad_map = json.loads(TRAD.read_text(encoding="utf-8"))["sources"]
    # Prefer gita commentary EN sources
    preferred = [
        "knowledge/raw_text/Bhagavad-gita-As-It-Is.txt",
        "knowledge/raw_text/Bhagavad_Gita_-_The_Song_of_God_-_Swami_Mukundananda.txt",
        "knowledge/raw_text/Teachings_of_the_Bhagavadgita.txt",
        "knowledge/raw_text/A-Study-of-the-Bhagavadgita.txt",
        "knowledge/raw_text/Krishna_Book.txt",
        "knowledge/raw_text/mahabharataofkri12roypuoft.txt",
    ]
    out: list[dict] = []
    for rel in preferred:
        path = ROOT / rel
        if not path.exists():
            continue
        meta = trad_map.get(rel.replace("\\", "/"), {})
        weight = float(meta.get("weight", 0.5))
        tradition = meta.get("tradition", "unknown")
        text = path.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"===== PAGE \d+ / \d+ =====", "\n", text)
        # ~400-500 tokens ~ 1600-2000 chars
        size = 1800
        step = 1400
        i = 0
        idx = 0
        while i < len(text) and idx < 400:  # cap per book for V1 size
            chunk = text[i : i + size].strip()
            if len(chunk) < 200:
                break
            # detect simple verse mention
            vids = []
            for m in re.finditer(r"\b(\d{1,2})\.(\d{1,2})\b", chunk[:500]):
                ch, vs = int(m.group(1)), int(m.group(2))
                if 1 <= ch <= 18 and 1 <= vs <= 78:
                    vids.append(f"BG_{ch}_{vs}")
            vids = list(dict.fromkeys(vids))[:5]
            cid = f"book:{path.stem}:{idx}"
            out.append(
                {
                    "chunk_id": cid,
                    "source_file": rel.replace("\\", "/"),
                    "tradition": tradition,
                    "text": chunk[:2500],
                    "linked_verse_ids": vids,
                    "weight": weight,
                    "layer": "book",
                }
            )
            i += step
            idx += 1
    return out


def conversation_chunks() -> list[dict]:
    out: list[dict] = []
    if EXAMPLES.exists():
        for p in sorted(EXAMPLES.glob("*.md")):
            text = p.read_text(encoding="utf-8", errors="replace").strip()
            if len(text) < 50:
                continue
            vids = re.findall(r"BG[_\s]?(\d+)[_\.\s](\d+)", text, re.I)
            verse_ids = [f"BG_{a}_{b}" for a, b in vids]
            # also "chapter 2, verse 47"
            for m in re.finditer(
                r"chapter\s+(\d+)\s*,?\s*verse\s+(\d+)", text, re.I
            ):
                verse_ids.append(f"BG_{m.group(1)}_{m.group(2)}")
            verse_ids = list(dict.fromkeys(verse_ids))
            pattern = p.stem
            out.append(
                {
                    "chunk_id": f"conv:examples/{p.stem}",
                    "pattern": pattern,
                    "text": text[:5000],
                    "verse_ids_mentioned": verse_ids,
                    "weight": 0.8,
                    "layer": "conversation",
                }
            )
    if CONV.exists():
        for p in sorted(CONV.iterdir()):
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8", errors="replace").strip()
            if len(text) < 80:
                continue
            # chunk large keepers into ~2000 char windows
            size, step, i, idx = 2000, 1600, 0, 0
            while i < len(text) and idx < 50:
                chunk = text[i : i + size].strip()
                if len(chunk) < 80:
                    break
                out.append(
                    {
                        "chunk_id": f"conv:keepers/{p.name}:{idx}",
                        "pattern": f"keeper_{p.name}",
                        "text": chunk,
                        "verse_ids_mentioned": [],
                        "weight": 0.7,
                        "layer": "conversation",
                    }
                )
                i += step
                idx += 1
    return out


def write_jsonl(path: Path, rows: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> int:
    data = json.loads(VERSES.read_text(encoding="utf-8"))
    n1 = write_jsonl(CHUNKS / "gita_verse_chunks.jsonl", verse_chunks(data))
    n2 = write_jsonl(CHUNKS / "book_chunks.jsonl", book_chunks())
    n3 = write_jsonl(CHUNKS / "conversation_chunks.jsonl", conversation_chunks())
    counts = {"gita_verse_chunks": n1, "book_chunks": n2, "conversation_chunks": n3}
    (CHUNKS / "counts.json").write_text(
        json.dumps(counts, indent=2) + "\n", encoding="utf-8"
    )
    print(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

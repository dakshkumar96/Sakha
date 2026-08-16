"""Validate Phase 1 knowledge base gates; write missing_fields_report.md."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITA = ROOT / "knowledge" / "gita"
TAX = ROOT / "knowledge" / "taxonomy"
VAL = ROOT / "knowledge" / "validation"
CHUNKS = ROOT / "knowledge" / "chunks"

TIER_A_REQUIRED = [
    "emotions",
    "situations",
    "response_strategy",
    "readiness",
    "depth_level",
]


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    verses_path = GITA / "verses.json"
    data = json.loads(verses_path.read_text(encoding="utf-8"))
    verses = data["verses"]
    ids = [v["id"] for v in verses]
    id_set = set(ids)

    if len(verses) != 700:
        errors.append(f"Expected 700 verses, got {len(verses)}")
    if len(ids) != len(id_set):
        errors.append("Duplicate verse IDs")

    allow = (VAL / "citation_allowlist.txt").read_text(encoding="utf-8").split()
    if set(allow) != id_set:
        errors.append(
            f"Allowlist mismatch: allow={len(allow)} spine={len(id_set)} "
            f"only_allow={len(set(allow)-id_set)} only_spine={len(id_set-set(allow))}"
        )

    missing_en = [v["id"] for v in verses if not (v.get("translations") or {}).get("en")]
    if missing_en:
        errors.append(f"Missing EN: {missing_en[:10]}… ({len(missing_en)})")

    anchors = json.loads((GITA / "anchor_verse_ids.json").read_text(encoding="utf-8"))
    tier = [v for v in verses if v.get("quality") == "tier_a"]
    if len(tier) < 60:
        errors.append(f"tier_a count {len(tier)} < 60")
    for a in anchors["ids"]:
        if a not in id_set:
            errors.append(f"Anchor missing from spine: {a}")
        else:
            card = next(v for v in verses if v["id"] == a)
            if card.get("quality") != "tier_a":
                errors.append(f"Anchor not tier_a: {a}")
            for field in TIER_A_REQUIRED:
                val = card.get(field)
                if val is None or val == "" or val == []:
                    errors.append(f"{a} missing {field}")

    # secondary orphans
    for v in tier:
        for s in v.get("secondary_verses") or []:
            if s not in id_set:
                errors.append(f"{v['id']} secondary orphan {s}")

    e2v = json.loads((TAX / "emotion_to_verses.json").read_text(encoding="utf-8"))["map"]
    for eid, row in e2v.items():
        prim = row.get("primary")
        if prim is not None and prim not in id_set:
            errors.append(f"emotion {eid} primary {prim} not in allowlist")
        for s in row.get("secondary") or []:
            if s not in id_set:
                errors.append(f"emotion {eid} secondary {s} not in allowlist")
        if row.get("crisis_override") == "block_teaching" and prim is not None:
            errors.append(f"crisis emotion {eid} must have primary null")

    situations = json.loads((TAX / "situations_v1.json").read_text(encoding="utf-8"))
    needed = {
        "fear_outcome",
        "arrogance",
        "grief_loss",
        "confusion_paralysis",
        "anger",
        "curiosity",
        "loneliness_night",
        "failure_shame",
        "doubt_angry_god",
        "crisis_l1",
        "crisis_l2_l4",
    }
    have = {s["id"] for s in situations["situations"]}
    if not needed.issubset(have):
        errors.append(f"Missing situations: {needed - have}")

    for name in [
        "gita_verse_chunks.jsonl",
        "book_chunks.jsonl",
        "conversation_chunks.jsonl",
    ]:
        p = CHUNKS / name
        if not p.exists():
            errors.append(f"Missing chunks {name}")
        else:
            n = sum(1 for _ in p.open(encoding="utf-8"))
            if n < 1:
                errors.append(f"Empty {name}")

    report = ["# Missing fields / validation report\n"]
    report.append(f"- Spine count: **{len(verses)}**")
    report.append(f"- Tier-A count: **{len(tier)}**")
    report.append(f"- Anchors: **{len(anchors['ids'])}**")
    report.append(f"- Errors: **{len(errors)}**")
    report.append(f"- Warnings: **{len(warnings)}**\n")
    if errors:
        report.append("## Errors\n")
        report.extend(f"- {e}" for e in errors)
    else:
        report.append("## Status\n\n**PASS** — no fatal validation errors.\n")
    if warnings:
        report.append("\n## Warnings\n")
        report.extend(f"- {w}" for w in warnings)

    (VAL / "missing_fields_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    for e in errors:
        print("ERROR:", e)
    print(f"Report: {VAL / 'missing_fields_report.md'}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

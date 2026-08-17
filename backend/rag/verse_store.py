"""Loads knowledge/gita/verses.json (Phase 1 spine + tier-A cards).

Read-only bridge — never mutates or duplicates the knowledge tree.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class VerseStore:
    def __init__(self, verses_path: Path, anchor_ids_path: Path):
        self._by_id: dict[str, dict[str, Any]] = {}
        self._tier_a_ids: list[str] = []
        self._load(verses_path, anchor_ids_path)

    def _load(self, verses_path: Path, anchor_ids_path: Path) -> None:
        data = json.loads(verses_path.read_text(encoding="utf-8"))
        cards = data["verses"] if isinstance(data, dict) else data
        for card in cards:
            self._by_id[card["id"]] = card

        if anchor_ids_path.exists():
            anchors = json.loads(anchor_ids_path.read_text(encoding="utf-8"))
            self._tier_a_ids = list(anchors.get("ids", []))
        else:
            self._tier_a_ids = [
                vid for vid, card in self._by_id.items() if card.get("quality") == "tier_a"
            ]

    def get(self, verse_id: str) -> dict[str, Any] | None:
        return self._by_id.get(verse_id)

    def en(self, verse_id: str) -> str:
        card = self.get(verse_id)
        if not card:
            return ""
        return card.get("translations", {}).get("en", "")

    def is_tier_a(self, verse_id: str) -> bool:
        card = self.get(verse_id)
        return bool(card) and card.get("quality") == "tier_a"

    def readiness(self, verse_id: str) -> str:
        card = self.get(verse_id)
        return card.get("readiness", "teach_ok") if card else "teach_ok"

    def blocked_for(self, verse_id: str, crisis_flags: set[str]) -> bool:
        """True if this verse must not be used given active crisis flags."""
        card = self.get(verse_id)
        if not card:
            return True
        do_not_use = set(card.get("do_not_use_when", []))
        return bool(do_not_use & crisis_flags)

    @property
    def tier_a_ids(self) -> list[str]:
        return self._tier_a_ids

    @property
    def count(self) -> int:
        return len(self._by_id)

    def all_ids(self) -> list[str]:
        return list(self._by_id.keys())

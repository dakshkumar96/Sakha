"""Loads knowledge/taxonomy/*.json (emotions, situations, emotion->verse map,
crisis-forbidden rules). Read-only bridge over Phase 1 output.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TaxonomyStore:
    def __init__(
        self,
        emotions_path: Path,
        situations_path: Path,
        emotion_to_verses_path: Path,
        crisis_forbidden_path: Path,
    ):
        emotions_doc = json.loads(emotions_path.read_text(encoding="utf-8"))
        situations_doc = json.loads(situations_path.read_text(encoding="utf-8"))
        etv_doc = json.loads(emotion_to_verses_path.read_text(encoding="utf-8"))
        self.crisis_forbidden: dict[str, Any] = json.loads(
            crisis_forbidden_path.read_text(encoding="utf-8")
        )

        self.emotions: dict[str, dict[str, Any]] = {
            e["id"]: e for e in emotions_doc.get("emotions", [])
        }
        self.situations: dict[str, dict[str, Any]] = {
            s["id"]: s for s in situations_doc.get("situations", [])
        }
        # emotion_to_verses.json is {"version":1, "map": {emotion_id: {...}}}
        self.emotion_to_verses: dict[str, dict[str, Any]] = etv_doc.get("map", etv_doc)

    def verse_mapping(self, emotion_id: str) -> dict[str, Any] | None:
        return self.emotion_to_verses.get(emotion_id)

    def emotion_ids(self) -> list[str]:
        return list(self.emotions.keys())

    def situation_for_emotion(self, emotion_id: str) -> dict[str, Any] | None:
        for sid, s in self.situations.items():
            if emotion_id in s.get("primary_emotions", []):
                return s
        return None

    def helpline_refs(self) -> list[str]:
        return list(self.crisis_forbidden.get("helpline_refs", []))

    def crisis_level_rules(self, level: str) -> dict[str, Any]:
        return self.crisis_forbidden.get("levels", {}).get(level, {})

    def never_cite_when(self) -> list[str]:
        return list(self.crisis_forbidden.get("never_cite_when", []))

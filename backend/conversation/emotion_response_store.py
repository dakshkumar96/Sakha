"""Emotion response map — per-emotion craft card from prompts/emotion_response.json.

Gives the generator: register_flow, pre_validation_line, primary_verse hints,
never-do rules, opening diagnostic question. Prefer this over free improvisation
when the detected emotion id matches a card.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger("krishna.emotion_response")

_DEFAULT = Path(__file__).resolve().parents[2] / "prompts" / "emotion_response.json"


@lru_cache(maxsize=1)
def _load_raw(path_str: str) -> dict[str, Any]:
    path = Path(path_str)
    if not path.exists():
        logger.warning("Emotion response map missing: %s", path)
        return {"emotions": []}
    return json.loads(path.read_text(encoding="utf-8"))


class EmotionResponseStore:
    def __init__(self, path: Path | None = None):
        raw = _load_raw(str(path or _DEFAULT))
        self.path = path or _DEFAULT
        self.by_id: dict[str, dict[str, Any]] = {
            e["id"]: e for e in raw.get("emotions", []) if e.get("id")
        }
        logger.info("Emotion response map loaded: %d emotions from %s", len(self.by_id), self.path)

    def get(self, emotion_id: str | None) -> dict[str, Any] | None:
        if not emotion_id:
            return None
        return self.by_id.get(emotion_id)

    def ids(self) -> list[str]:
        return list(self.by_id.keys())

    def phrase_lexicon(self) -> dict[str, list[str]]:
        """what_people_say → casefold phrases for lexicon emotion hits."""
        out: dict[str, list[str]] = {}
        for eid, card in self.by_id.items():
            phrases = [p.casefold() for p in card.get("what_people_say") or [] if p]
            # Light linguistic markers words also help short signals.
            words = (card.get("linguistic_markers") or {}).get("words") or []
            phrases.extend(w.casefold() for w in words if w and len(w) > 3)
            if phrases:
                out[eid] = phrases
        return out

    def render_card(
        self,
        emotion_id: str | None,
        lang: str = "en",
        skip_metaphor_ref: str | None = None,
    ) -> str | None:
        card = self.get(emotion_id)
        if not card:
            return None

        lang_key = "hi" if lang in ("hi", "hinglish") else "en"
        pre = (card.get("pre_validation_line") or {}).get(lang_key) or (
            card.get("pre_validation_line") or {}
        ).get("en", "")
        open_q = (card.get("opening_diagnostic_question") or {}).get(lang_key) or (
            card.get("opening_diagnostic_question") or {}
        ).get("en", "")
        never = card.get("never_for_this_emotion") or ""
        flow = ", ".join(card.get("register_flow") or [])
        secondaries = ", ".join(card.get("secondary_verses") or [])

        lines = [
            f"[EMOTION CARD — {card['id']} / {card.get('name', '')}]",
            f"- family: {card.get('family', '')}",
            f"- hidden_beneath: {card.get('hidden_beneath', '')}",
            f"- register_flow (prefer this arc): {flow}",
            f"- rebuking_eligible: {bool(card.get('rebuking_eligible'))}",
            f"- primary_verse preference: {card.get('primary_verse') or 'none'}",
        ]
        if secondaries:
            lines.append(f"- secondary_verses preference: {secondaries}")
        if pre:
            lines.append(f"- pre_validation_line (use when teaching or sitting with it): \"{pre}\"")
        if open_q:
            lines.append(f"- opening_diagnostic_question (listening turns): \"{open_q}\"")
        if never:
            lines.append(f"- NEVER: {never}")
        if card.get("south_asian_expression"):
            lines.append(f"- cultural note: {card['south_asian_expression']}")
        metaphor_ref = card.get("metaphor_ref")
        if metaphor_ref and metaphor_ref != skip_metaphor_ref:
            lines.append(f"- metaphor_ref: {metaphor_ref}")
        elif metaphor_ref and metaphor_ref == skip_metaphor_ref:
            lines.append(
                "- metaphor_ref: SKIP — that image was already used this session; "
                "pick a different bank image or none"
            )
        lines.append(
            "Use this card for register + undersurface naming. Cite only verses "
            "actually retrieved this turn (primary preference is not a free pass)."
        )
        return "\n".join(lines)

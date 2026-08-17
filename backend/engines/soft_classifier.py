"""Soft LLM classification for turns the lexicon reads poorly.

The lexicon is fast, auditable and free — but it only knows phrases someone
wrote down. When its confidence is low, this asks the model to pick from the
SAME closed set of ids, then fills gaps only.

Two hard rules:
  - **Crisis is never touched.** Crisis routing stays lexicon-only, always,
    because it must be deterministic and reviewable. This runs after crisis
    has already been decided and cannot change it.
  - The model may only return ids that already exist in the taxonomy. Anything
    else is discarded rather than passed downstream.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger("krishna.soft_classifier")

INTENTS = [
    "venting",
    "seeking_guidance",
    "questioning_god",
    "pushing_back",
    "curiosity",
]

_PROMPT = """You label messages for a companion app grounded in the Bhagavad Gita.

Pick the best emotion id from this list ONLY:
{emotions}

Pick the best intent from this list ONLY:
{intents}

Return ONLY JSON: {{"emotion": "<id or null>", "intent": "<intent>", "confidence": 0.0-1.0}}
If nothing fits, use null for emotion. Do not invent ids. Do not mention verses.
"""


@dataclass
class SoftResult:
    emotion: str | None = None
    intent: str | None = None
    confidence: float = 0.0
    available: bool = False


def classify(
    client,
    model: str,
    user_message: str,
    allowed_emotions: list[str],
    max_tokens: int = 120,
) -> SoftResult:
    """Always safe to call — any failure returns available=False."""
    if client is None or not user_message.strip():
        return SoftResult()

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": _PROMPT.format(
                        emotions=", ".join(allowed_emotions),
                        intents=", ".join(INTENTS),
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        data = json.loads(completion.choices[0].message.content or "{}")
    except Exception:  # noqa: BLE001 - enhancement only
        logger.warning("Soft classifier unavailable; keeping lexicon result", exc_info=True)
        return SoftResult()

    emotion = data.get("emotion")
    if emotion not in allowed_emotions:
        emotion = None

    intent = data.get("intent")
    if intent not in INTENTS:
        intent = None

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    return SoftResult(
        emotion=emotion,
        intent=intent,
        confidence=max(0.0, min(1.0, confidence)),
        available=True,
    )

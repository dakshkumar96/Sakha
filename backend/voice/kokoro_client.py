"""Thin client for Kokoro-FastAPI (OpenAI-compatible /audio/speech).

The browser never calls Kokoro directly — see docs/v1/voice/kokoro_fastapi.md.
Path is always: Browser -> our FastAPI /tts -> Kokoro -> audio bytes.

Kokoro being down is a normal, expected state (it's a separate Docker
container). Every failure here is reported as unavailable so the UI can
degrade to text-only rather than breaking the conversation.
"""
from __future__ import annotations

import logging
import re

import httpx

logger = logging.getLogger("krishna.kokoro")


class KokoroUnavailable(Exception):
    """Kokoro could not be reached or refused the request."""


# Light cleanup so the voice doesn't read markdown symbols aloud.
# Spoken citations ("chapter 2, verse 47") are deliberately preserved.
_MARKDOWN_NOISE = [
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),
    (re.compile(r"\*(.+?)\*"), r"\1"),
    (re.compile(r"`(.+?)`"), r"\1"),
    (re.compile(r"^#{1,6}\s*", re.MULTILINE), ""),
    (re.compile(r"^\s*[-•]\s*", re.MULTILINE), ""),
    (re.compile(r"\bBG[_\s](\d{1,2})[_.](\d{1,3})\b"), r"chapter \1, verse \2"),
    (re.compile(r"\s{2,}"), " "),
]


def clean_for_speech(text: str) -> str:
    cleaned = text
    for pattern, replacement in _MARKDOWN_NOISE:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned.strip()


class KokoroClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        voice_en: str,
        voice_hi: str,
        speed: float,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.voice_en = voice_en
        self.voice_hi = voice_hi
        self.speed = speed

    def voice_for(self, lang: str) -> str:
        return self.voice_hi if lang == "hi" else self.voice_en

    async def synthesize(self, text: str, lang: str = "en") -> bytes:
        spoken = clean_for_speech(text)
        if not spoken:
            raise KokoroUnavailable("nothing to speak")

        payload = {
            "model": "kokoro",
            "input": spoken,
            "voice": self.voice_for(lang),
            "response_format": "mp3",
            "speed": self.speed,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.base_url}/audio/speech", json=payload, headers=headers
                )
        except httpx.RequestError as exc:
            raise KokoroUnavailable(f"cannot reach Kokoro: {exc}") from exc

        if resp.status_code != 200:
            raise KokoroUnavailable(
                f"Kokoro returned {resp.status_code}: {resp.text[:200]}"
            )
        return resp.content

    async def reachable(self, timeout: float = 1.5) -> bool:
        """Short probe for GET /health — used by our /health endpoint so the
        UI can show 'voice resting' without waiting on a synthesis call."""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(f"{self.base_url}/audio/voices")
            return resp.status_code == 200
        except httpx.RequestError:
            return False

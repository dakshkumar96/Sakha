from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from backend.api.limits import limit_tts, require_max_length
from backend.config import get_settings
from backend.voice.kokoro_client import KokoroUnavailable

logger = logging.getLogger("krishna.tts")

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    lang: str = Field(default="en", pattern="^(en|hi)$")


@router.post("/tts", dependencies=[Depends(limit_tts)])
async def tts(req: TTSRequest, request: Request):
    settings = get_settings()
    require_max_length(
        req.text,
        settings.max_tts_chars,
        "text_too_long",
        f"That text is too long to speak. Please keep it under {settings.max_tts_chars:,} characters.",
    )
    client = request.app.state.kokoro
    try:
        audio = await client.synthesize(req.text, req.lang)
    except KokoroUnavailable as exc:
        logger.warning("TTS unavailable: %s", exc)
        return JSONResponse(status_code=503, content={"error": "tts_unavailable"})

    return Response(content=audio, media_type="audio/mpeg")

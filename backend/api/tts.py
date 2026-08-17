from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from backend.voice.kokoro_client import KokoroUnavailable

logger = logging.getLogger("krishna.tts")

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    lang: str = Field(default="en", pattern="^(en|hi)$")


@router.post("/tts")
async def tts(req: TTSRequest, request: Request):
    client = request.app.state.kokoro
    try:
        audio = await client.synthesize(req.text, req.lang)
    except KokoroUnavailable as exc:
        logger.warning("TTS unavailable: %s", exc)
        return JSONResponse(status_code=503, content={"error": "tts_unavailable"})

    return Response(content=audio, media_type="audio/mpeg")

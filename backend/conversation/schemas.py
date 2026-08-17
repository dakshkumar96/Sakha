"""Pydantic request/response contracts. Stable API surface for Phase 3
(Next.js UI) to build against — see docs/phase-2-runtime-plan.md §8.1.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str
    turn_number: int = 1
    conversation_history: list[HistoryMessage] = Field(default_factory=list)
    #: Preferred spoken reply language from the UI ("en" | "hi").
    #: When set, overrides auto-detect for generation + TTS mirroring.
    reply_lang: str | None = None


class VerseCitation(BaseModel):
    id: str
    chapter: int
    verse: int
    short: str
    translation_en: str | None = None
    translation_hi: str | None = None


class ChatResponse(BaseModel):
    text: str
    is_crisis: bool
    crisis_level: int  # 0-4
    verses: list[str]
    verse_citations: list[VerseCitation]
    response_style: str
    detected_emotion: str | None
    teach_action: str
    #: English for on-screen movie subtitles (spoken `text` may be Hindi).
    text_en: str | None = None
    #: English sidebar title hint from the user's first message (optional).
    title_en: str | None = None

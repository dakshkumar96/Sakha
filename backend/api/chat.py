from __future__ import annotations

from fastapi import APIRouter, Request

from backend.conversation.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request) -> ChatResponse:
    pipeline = request.app.state.pipeline
    return pipeline.handle_message(req)

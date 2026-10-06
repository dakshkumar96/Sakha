from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from backend.api.errors import ApiError
from backend.api.limits import limit_chat, require_max_length
from backend.config import get_settings
from backend.conversation.schemas import ChatRequest, ChatResponse

router = APIRouter()


def _check_sizes(req: ChatRequest) -> None:
    settings = get_settings()
    require_max_length(
        req.message,
        settings.max_message_chars,
        "message_too_long",
        f"That message is too long. Please keep it under {settings.max_message_chars:,} characters.",
    )
    require_max_length(
        req.session_id, 100, "bad_session_id", "That session id is not valid."
    )
    too_long = "This conversation is too long to continue. Please start a new one."
    if len(req.conversation_history) > settings.max_history_items:
        raise ApiError(400, "history_too_long", too_long)
    for turn in req.conversation_history:
        require_max_length(turn.content, settings.max_history_item_chars, "history_too_long", too_long)


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(limit_chat)])
def chat(req: ChatRequest, request: Request) -> ChatResponse:
    _check_sizes(req)
    pipeline = request.app.state.pipeline
    return pipeline.handle_message(req)

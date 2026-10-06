"""One error shape for the public API.

Every refusal the user can meet comes back as `{"error": code, "message": text}`.
The message is written to be shown, and spoken, as is. Nothing about keys,
quotas, files or restarts ever goes in it. Those details go to the server log.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.conversation.errors import GenerationUnavailable

COMPANION_UNAVAILABLE_MESSAGE = (
    "I'm having trouble finding words right now. Please try again in a moment."
)


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(f"{status_code} {code}")
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers or {}


def companion_unavailable() -> ApiError:
    return ApiError(
        503,
        "companion_unavailable",
        COMPANION_UNAVAILABLE_MESSAGE,
        headers={"Retry-After": "10"},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
            headers=exc.headers,
        )

    @app.exception_handler(GenerationUnavailable)
    async def _generation_unavailable(_: Request, exc: GenerationUnavailable) -> JSONResponse:
        # The details were logged where the failure happened. The user gets a fixed line.
        return await _api_error(_, companion_unavailable())

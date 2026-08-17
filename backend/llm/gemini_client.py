"""Google Gemini client with an OpenAI/Groq-shaped surface.

Downstream code (generator, knot summarizer, soft classifier) calls:

    client.chat.completions.create(
        model=...,
        messages=[{"role": "system"|"user"|"assistant", "content": "..."}, ...],
        temperature=...,
        max_tokens=...,
        response_format={"type": "json_object"} | None,
    )

and reads completion.choices[0].message.content.

On 429 / RESOURCE_EXHAUSTED, the client walks a fallback model list so a free-tier
cap on one flash variant does not kill the whole product mid-session.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("krishna.gemini")

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

# Tried in order after the requested model fails with quota. Separate free-tier
# buckets are common across "flash" vs "flash-lite" families.
DEFAULT_FALLBACK_MODELS: tuple[str, ...] = (
    "gemini-flash-lite-latest",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-2.0-flash",
)


@dataclass
class _Message:
    content: str


@dataclass
class _Choice:
    message: _Message


@dataclass
class _Completion:
    choices: list[_Choice]


def _is_quota_error(exc: BaseException) -> bool:
    name = type(exc).__name__
    msg = str(exc).lower()
    return (
        name in ("ResourceExhausted", "ClientError", "RateLimitError")
        and (
            "429" in msg
            or "resource_exhausted" in msg
            or "quota" in msg
            or "rate" in msg
        )
    ) or name == "ResourceExhausted"


def _retry_after_seconds(exc: BaseException) -> float | None:
    """Parse 'Please retry in N.Ns' when present."""
    import re

    m = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)\s*s", str(exc), re.I)
    if not m:
        return None
    try:
        return min(float(m.group(1)), 45.0)
    except ValueError:
        return None


def _fold_messages(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[Any]]:
    """Split chat messages into system_instruction + Content list."""
    system_parts: list[str] = []
    contents: list[Any] = []

    for msg in messages:
        role = (msg.get("role") or "user").lower()
        content = msg.get("content") or ""
        if not content.strip():
            continue
        if role == "system":
            system_parts.append(content)
            continue

        gem_role = "model" if role == "assistant" else "user"
        if types is None:
            contents.append({"role": gem_role, "parts": [{"text": content}]})
            continue

        if contents and getattr(contents[-1], "role", None) == gem_role:
            prev = contents[-1]
            prev_text = ""
            if prev.parts:
                prev_text = getattr(prev.parts[0], "text", "") or ""
            contents[-1] = types.Content(
                role=gem_role,
                parts=[types.Part(text=prev_text + "\n\n" + content)],
            )
        else:
            contents.append(
                types.Content(role=gem_role, parts=[types.Part(text=content)])
            )

    if not contents:
        if types is not None:
            contents = [types.Content(role="user", parts=[types.Part(text="Continue.")])]
        else:
            contents = [{"role": "user", "parts": [{"text": "Continue."}]}]
    else:
        first_role = getattr(contents[0], "role", None) or contents[0].get("role")  # type: ignore[union-attr]
        if first_role != "user" and types is not None:
            contents.insert(
                0,
                types.Content(role="user", parts=[types.Part(text="(context above)")]),
            )

    system = "\n\n".join(system_parts).strip() or None
    return system, contents


def _extract_text(response: Any) -> str:
    """Pull visible text from a GenerateContent response (thinking models included)."""
    try:
        t = (response.text or "").strip()
        if t:
            return t
    except Exception:  # noqa: BLE001
        pass

    chunks: list[str] = []
    try:
        for cand in response.candidates or []:
            content = getattr(cand, "content", None)
            if not content:
                continue
            for part in content.parts or []:
                if getattr(part, "thought", False):
                    continue
                text = getattr(part, "text", None)
                if text:
                    chunks.append(text)
    except Exception:  # noqa: BLE001
        logger.warning("Gemini text extract failed", exc_info=True)
    return "\n".join(chunks).strip()


class _Completions:
    def __init__(self, client: Any, fallback_models: tuple[str, ...]):
        self._client = client
        self._fallback_models = fallback_models

    def _model_chain(self, primary: str) -> list[str]:
        ordered: list[str] = []
        for m in (primary, *self._fallback_models):
            if m and m not in ordered:
                ordered.append(m)
        return ordered

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        response_format: dict[str, Any] | None = None,
        **_: Any,
    ) -> _Completion:
        if genai is None or types is None:
            raise RuntimeError(
                "google-genai is not installed. Run: pip install google-genai"
            )

        system_instruction, contents = _fold_messages(messages)
        want_json = bool(response_format and response_format.get("type") == "json_object")

        # Flash / 3.x models spend output budget on internal thinking.
        floor = 768 if want_json else 2048
        effective_max = max(int(max_tokens), floor)

        config_kwargs: dict[str, Any] = {
            "temperature": float(temperature),
            "max_output_tokens": effective_max,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if want_json:
            config_kwargs["response_mime_type"] = "application/json"
        # NOTE: thinking_config=ThinkingConfig(thinking_budget=0) was tried here
        # to rule out hidden reasoning tokens eating the visible-reply budget
        # (suspected cause of live-observed mid-sentence cutoffs). Confirmed by
        # testing: every model in DEFAULT_FALLBACK_MODELS rejects it outright
        # with a generic 400 INVALID_ARGUMENT, so setting it just doubled every
        # call (fail, then silently retry without it) for zero benefit. Left
        # out. If a future SDK/model update adds support, re-add behind a
        # try-once-then-drop wrapper rather than trying it on every call.

        config = types.GenerateContentConfig(**config_kwargs)
        last_exc: BaseException | None = None

        def _call(model_id: str):
            return self._client.models.generate_content(
                model=model_id, contents=contents, config=config
            )

        for idx, model_id in enumerate(self._model_chain(model)):
            try:
                response = _call(model_id)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if not _is_quota_error(exc):
                    raise
                wait = _retry_after_seconds(exc)
                # One short wait on the *first* model only, then walk fallbacks.
                if idx == 0 and wait and wait <= 8.0:
                    logger.warning(
                        "Gemini quota on %s; brief retry in %.1fs", model_id, wait
                    )
                    time.sleep(wait)
                    try:
                        response = _call(model_id)
                    except Exception as exc2:  # noqa: BLE001
                        last_exc = exc2
                        if not _is_quota_error(exc2):
                            raise
                        logger.warning(
                            "Gemini still quota on %s; trying fallbacks", model_id
                        )
                        continue
                    else:
                        # success after wait
                        break
                logger.warning(
                    "Gemini quota/exhaustion on %s; trying next model", model_id
                )
                continue
            else:
                if idx > 0:
                    logger.info("Gemini fallback succeeded with model=%s", model_id)
                break
        else:
            assert last_exc is not None
            raise last_exc

        text = _extract_text(response)
        finish_reason = None
        try:
            finish_reason = response.candidates[0].finish_reason  # type: ignore[index]
        except Exception:  # noqa: BLE001
            pass

        if not text:
            logger.warning("Gemini returned empty text (finish=%s model=%s)", finish_reason, model)
        elif finish_reason is not None and str(finish_reason).upper() not in (
            "STOP",
            "FINISHREASON.STOP",
            "1",
        ):
            # MAX_TOKENS truncation reads as a normal 200 response with partial
            # text -- nothing upstream would otherwise notice a reply was cut
            # off mid-sentence rather than ending naturally.
            logger.warning(
                "Gemini reply did not finish cleanly (finish=%s model=%s chars=%d)",
                finish_reason,
                model,
                len(text),
            )

        return _Completion(choices=[_Choice(message=_Message(content=text))])


class _Chat:
    def __init__(self, client: Any, fallback_models: tuple[str, ...]):
        self.completions = _Completions(client, fallback_models)


class GeminiClient:
    """Drop-in for places that previously held a Groq() instance.

    One underlying Client is reused across turns (avoids re-init per call).
    """

    def __init__(
        self,
        api_key: str,
        fallback_models: tuple[str, ...] | list[str] | None = None,
    ):
        if not api_key:
            raise ValueError("Gemini API key is empty")
        if genai is None:
            raise RuntimeError(
                "google-genai is not installed. Run: pip install google-genai"
            )
        self._api_key = api_key
        self._client = genai.Client(api_key=api_key)
        fb = tuple(fallback_models) if fallback_models else DEFAULT_FALLBACK_MODELS
        self.chat = _Chat(self._client, fb)

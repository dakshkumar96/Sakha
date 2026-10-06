"""Shared stand-ins for tests that drive the real pipeline without a model or network."""
from __future__ import annotations

import threading
from functools import lru_cache
from types import SimpleNamespace

from backend.config import get_settings
from backend.conversation.pipeline import ConversationPipeline
from backend.conversation.response_generator import ResponseGenerator
from backend.memory.session_store import SessionStore
from backend.rag.taxonomy_store import TaxonomyStore
from backend.rag.verse_store import VerseStore


class FakeModel:
    """Stands in for the Gemini client.

    `reply` is the text to return, or an exception to raise. `gate`, when
    given, makes every call wait until it is set, like a hung request.
    `messages` keeps what each call was sent.
    """

    def __init__(self, reply: str | Exception = "", gate: threading.Event | None = None):
        self.reply = reply
        self.gate = gate
        self.calls = 0
        self.messages: list[list[dict]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls += 1
        self.messages.append(kwargs.get("messages", []))
        if self.gate is not None:
            self.gate.wait(timeout=10)
        if isinstance(self.reply, Exception):
            raise self.reply
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.reply))])


def generator_with(model, system_prompt: str = "system") -> ResponseGenerator:
    generator = object.__new__(ResponseGenerator)
    generator._client = model
    generator.model = "fake"
    generator.system_prompt = system_prompt
    generator.fewshot_store = SimpleNamespace(pick=lambda **kw: None)
    generator.emotion_store = None
    return generator


@lru_cache(maxsize=1)
def stores() -> SimpleNamespace:
    settings = get_settings()
    return SimpleNamespace(
        verses=VerseStore(settings.verses_path, settings.anchor_ids_path),
        taxonomy=TaxonomyStore(
            settings.emotions_path,
            settings.situations_path,
            settings.emotion_to_verses_path,
            settings.crisis_forbidden_path,
        ),
    )


def pipeline_with(model, timeout: float = 5.0) -> ConversationPipeline:
    loaded = stores()
    return ConversationPipeline(
        verse_store=loaded.verses,
        taxonomy_store=loaded.taxonomy,
        retriever=SimpleNamespace(retrieve=lambda **kw: []),
        session_store=SessionStore(),
        generator=generator_with(model),
        allowlist=set(),
        teach_gate_min_questions=2,
        max_verses_per_turn=2,
        crisis_reply_timeout_seconds=timeout,
    )

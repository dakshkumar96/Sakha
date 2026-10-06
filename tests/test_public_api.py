"""Rate limits, input caps and safe failures on /chat and /tts.

Everything is faked. No model, no Kokoro and no network is used.
"""
from __future__ import annotations

import logging
import threading
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api import limits
from backend.api.chat import router as chat_router
from backend.api.errors import COMPANION_UNAVAILABLE_MESSAGE, register_error_handlers
from backend.api.tts import router as tts_router
from backend.conversation.errors import GenerationUnavailable
from backend.conversation.response_generator import ResponseGenerator
from backend.conversation.schemas import ChatResponse
from backend.voice.kokoro_client import KokoroUnavailable

SECRETS_THAT_MUST_NOT_LEAK = (
    "GEMINI_API_KEY",
    "restart the backend",
    ".env",
    "quota",
    "generation-unavailable",
    "Traceback",
)


class FakePipeline:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls = 0

    def handle_message(self, req):
        self.calls += 1
        if self.error:
            raise self.error
        return ChatResponse(
            text="Hello.", is_crisis=False, crisis_level=0, verses=[], verse_citations=[],
            response_style="question", detected_emotion=None, teach_action="question",
        )


class FakeKokoro:
    def __init__(self, error: Exception | None = None):
        self.error = error

    async def synthesize(self, text, lang):
        if self.error:
            raise self.error
        return b"ID3audio"


def make_app(pipeline=None, kokoro=None) -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(chat_router)
    app.include_router(tts_router)
    app.state.pipeline = pipeline or FakePipeline()
    app.state.kokoro = kokoro or FakeKokoro()
    return app


@pytest.fixture(autouse=True)
def fresh_limiters(monkeypatch):
    monkeypatch.setattr(limits, "chat_limiter", limits.RateLimiter(10))
    monkeypatch.setattr(limits, "tts_limiter", limits.RateLimiter(20))


def chat_body(message="hello", history=None):
    return {"message": message, "session_id": "s1", "conversation_history": history or []}


# --- rate limits ---------------------------------------------------------------------------


def test_the_eleventh_chat_in_a_minute_is_refused_with_a_calm_message():
    client = TestClient(make_app())
    for _ in range(10):
        assert client.post("/chat", json=chat_body()).status_code == 200
    refused = client.post("/chat", json=chat_body())
    assert refused.status_code == 429
    assert refused.json() == {"error": "rate_limited", "message": limits.TOO_MANY_MESSAGE}
    assert refused.headers["retry-after"] == "60"


def test_the_refused_chat_never_reaches_the_pipeline():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline=pipeline))
    for _ in range(12):
        client.post("/chat", json=chat_body())
    assert pipeline.calls == 10


def test_tts_has_its_own_higher_limit():
    client = TestClient(make_app())
    for _ in range(20):
        assert client.post("/tts", json={"text": "hi", "lang": "en"}).status_code == 200
    assert client.post("/tts", json={"text": "hi", "lang": "en"}).status_code == 429
    assert client.post("/chat", json=chat_body()).status_code == 200


def test_each_address_has_its_own_count():
    limiter = limits.RateLimiter(1)
    limiter.check("1.1.1.1")
    limiter.check("2.2.2.2")
    with pytest.raises(Exception) as caught:
        limiter.check("1.1.1.1")
    assert caught.value.status_code == 429


def test_zero_turns_the_limit_off():
    limiter = limits.RateLimiter(0)
    for _ in range(500):
        limiter.check("1.2.3.4")


def test_old_calls_stop_counting_and_idle_addresses_are_forgotten(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(limits.time, "monotonic", lambda: clock[0])
    limiter = limits.RateLimiter(2)
    for n in range(300):
        limiter.check(f"10.0.0.{n % 250}-{n}")
    assert limiter.tracked_addresses() == 300
    clock[0] += 61
    limiter.check("192.0.2.1")
    assert limiter.tracked_addresses() == 1


def test_the_limit_holds_under_many_threads_at_once():
    limiter = limits.RateLimiter(10)
    allowed = []

    def hit():
        try:
            limiter.check("9.9.9.9")
            allowed.append(1)
        except Exception:
            pass

    threads = [threading.Thread(target=hit) for _ in range(60)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(allowed) == 10


# --- who is asking (behind Caddy) --------------------------------------------------------------


def fake_request(peer, forwarded=None):
    headers = {"x-forwarded-for": forwarded} if forwarded is not None else {}
    return SimpleNamespace(client=SimpleNamespace(host=peer), headers=headers)


def test_behind_the_proxy_the_visitor_address_comes_from_the_forwarded_header():
    assert limits.client_address(fake_request("172.18.0.1", "203.0.113.7")) == "203.0.113.7"
    assert limits.client_address(fake_request("127.0.0.1", "203.0.113.7")) == "203.0.113.7"


def test_only_the_last_forwarded_address_counts():
    request = fake_request("172.18.0.1", "6.6.6.6, 203.0.113.7")
    assert limits.client_address(request) == "203.0.113.7"


def test_a_direct_visitor_cannot_choose_their_own_address():
    assert limits.client_address(fake_request("8.8.8.8", "6.6.6.6")) == "8.8.8.8"


def test_a_bad_or_missing_forwarded_header_falls_back_to_the_peer():
    assert limits.client_address(fake_request("172.18.0.1")) == "172.18.0.1"
    assert limits.client_address(fake_request("172.18.0.1", "not-an-ip")) == "172.18.0.1"


# --- input caps ------------------------------------------------------------------------------------


def test_a_message_over_the_cap_gets_a_clear_400():
    client = TestClient(make_app())
    ok = client.post("/chat", json=chat_body("a" * 2000))
    assert ok.status_code == 200
    long = client.post("/chat", json=chat_body("a" * 2001))
    assert long.status_code == 400
    assert long.json()["error"] == "message_too_long"
    assert "2,000" in long.json()["message"]


def test_a_huge_history_or_history_item_is_refused():
    client = TestClient(make_app())
    many = [{"role": "user", "content": "hi"}] * 61
    assert client.post("/chat", json=chat_body(history=many)).json()["error"] == "history_too_long"
    big = [{"role": "user", "content": "a" * 6001}]
    assert client.post("/chat", json=chat_body(history=big)).status_code == 400
    fine = [{"role": "user", "content": "hi"}] * 60
    assert client.post("/chat", json=chat_body(history=fine)).status_code == 200


def test_tts_text_over_the_cap_gets_a_clear_400_and_no_synthesis():
    client = TestClient(make_app(kokoro=FakeKokoro(error=AssertionError("must not synthesise"))))
    refused = client.post("/tts", json={"text": "a" * 6001, "lang": "en"})
    assert refused.status_code == 400
    assert refused.json()["error"] == "text_too_long"
    assert TestClient(make_app()).post("/tts", json={"text": "a" * 6000, "lang": "en"}).status_code == 200


def test_tts_still_reports_an_unavailable_voice_as_503():
    client = TestClient(make_app(kokoro=FakeKokoro(error=KokoroUnavailable("cannot reach Kokoro"))))
    refused = client.post("/tts", json={"text": "hi", "lang": "en"})
    assert refused.status_code == 503
    assert refused.json() == {"error": "tts_unavailable"}


# --- failures never leak (R1) ----------------------------------------------------------------------


class RaisingClient:
    def __init__(self, error):
        self.error = error
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        raise self.error


def generator_with(client) -> ResponseGenerator:
    generator = object.__new__(ResponseGenerator)
    generator._client = client
    generator.model = "m"
    generator.system_prompt = "system"
    generator.fewshot_store = SimpleNamespace(pick=lambda **kw: None)
    generator.emotion_store = None
    return generator


def generate(generator):
    return generator.generate(
        user_message="hi", plan_instruction="", retrieved=[], history=[], turn_action="question"
    )


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("429 RESOURCE_EXHAUSTED quota exceeded for GEMINI_API_KEY, restart the backend"),
        ConnectionError("cannot reach generativelanguage.googleapis.com"),
        ValueError("anything else"),
    ],
)
def test_a_failed_model_call_raises_instead_of_returning_text(error, caplog):
    with caplog.at_level(logging.ERROR), pytest.raises(GenerationUnavailable):
        generate(generator_with(RaisingClient(error)))
    assert "Gemini generation failed" in caplog.text, "the details belong in the server log"


def test_a_missing_key_and_an_empty_reply_also_raise():
    with pytest.raises(GenerationUnavailable):
        generate(generator_with(None))
    empty = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="  "))])
            )
        )
    )
    with pytest.raises(GenerationUnavailable):
        generate(generator_with(empty))


def test_the_api_answers_a_generation_failure_with_one_fixed_calm_message():
    secret = "429 RESOURCE_EXHAUSTED set a fresh GEMINI_API_KEY in .env and restart the backend"
    client = TestClient(make_app(pipeline=FakePipeline(error=GenerationUnavailable(secret))))
    response = client.post("/chat", json=chat_body())
    assert response.status_code == 503
    assert response.json() == {"error": "companion_unavailable", "message": COMPANION_UNAVAILABLE_MESSAGE}
    assert response.headers["retry-after"] == "10"
    for word in SECRETS_THAT_MUST_NOT_LEAK:
        assert word.lower() not in response.text.lower()


def test_the_calm_message_has_no_setup_words_and_is_short():
    assert len(COMPANION_UNAVAILABLE_MESSAGE) < 100
    for word in SECRETS_THAT_MUST_NOT_LEAK:
        assert word.lower() not in COMPANION_UNAVAILABLE_MESSAGE.lower()

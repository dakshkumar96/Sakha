"""Crisis levels 1 and 2 always reach a helpline, whatever the model does.

The pipeline, crisis lexicon, engines, planner and helpline text are all real.
Only the model client is fake, so no network is used.
"""
from __future__ import annotations

import threading
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api import limits
from backend.api.chat import router as chat_router
from backend.api.errors import COMPANION_UNAVAILABLE_MESSAGE, register_error_handlers
from backend.conversation.schemas import ChatRequest
from backend.engines import crisis_detector
from tests.fakes import FakeModel, pipeline_with
from tests.fakes import stores as load_stores

LEVEL_1_AND_2 = [
    pytest.param("Nothing matters and I feel hopeless every day", "L1", "en", id="L1-en"),
    pytest.param("मन नहीं लगता, सब बेकार लगता है", "L1", "hi", id="L1-hi"),
    pytest.param("I just want to die, I wish I was dead", "L2", "en", id="L2-en"),
    pytest.param("मैं मरना चाहती हूँ", "L2", "hi", id="L2-hi"),
]

WARM_REPLY = "I'm here with you. What has felt heaviest today?"


@pytest.fixture(scope="module")
def stores():
    return load_stores()


def ask(pipeline, message: str, session_id: str = "s1"):
    return pipeline.handle_message(ChatRequest(message=message, session_id=session_id))


def helpline(stores, lang: str) -> str:
    return crisis_detector.helpline_message(stores.taxonomy.helpline_refs(), lang=lang)


def assert_is_helpline(response, stores, level: str, lang: str) -> None:
    assert response.text == helpline(stores, lang)
    assert response.text_en == helpline(stores, "en")
    assert response.is_crisis is True
    assert response.crisis_level == int(level[1])
    assert response.response_style == "crisis_protocol"
    assert COMPANION_UNAVAILABLE_MESSAGE not in response.text


def test_the_fixtures_are_the_levels_they_claim(stores):
    assert stores.taxonomy.helpline_refs(), "the helpline text needs real numbers in it"
    for param in LEVEL_1_AND_2:
        message, level, lang = param.values
        result = crisis_detector.detect(message)
        assert (result.level, result.lang) == (level, lang)


@pytest.mark.parametrize("message, level, lang", LEVEL_1_AND_2)
def test_a_model_error_gives_the_helpline(message, level, lang, stores):
    model = FakeModel(RuntimeError("503 UNAVAILABLE: the model is overloaded"))
    assert_is_helpline(ask(pipeline_with(model), message), stores, level, lang)
    assert model.calls >= 1, "the warm reply should still be tried first"


@pytest.mark.parametrize("message, level, lang", LEVEL_1_AND_2)
def test_an_empty_model_reply_gives_the_helpline(message, level, lang, stores):
    model = FakeModel("")
    assert_is_helpline(ask(pipeline_with(model), message), stores, level, lang)


@pytest.mark.parametrize("message, level, lang", LEVEL_1_AND_2)
def test_a_hung_model_gives_the_helpline_within_the_deadline(message, level, lang, stores):
    gate = threading.Event()
    model = FakeModel(WARM_REPLY, gate=gate)
    pipeline = pipeline_with(model, timeout=0.3)

    started = time.monotonic()
    response = ask(pipeline, message)
    elapsed = time.monotonic() - started

    assert_is_helpline(response, stores, level, lang)
    assert elapsed < 2, f"the helpline took {elapsed:.1f}s"

    gate.set()  # let the late reply finish, then check it was thrown away
    time.sleep(0.5)
    assert pipeline.session_store.get_or_create("s1").turn_count == 1


def test_a_working_model_still_gives_the_warm_reply(stores):
    response = ask(pipeline_with(FakeModel(WARM_REPLY)), "Nothing matters and I feel hopeless every day")
    assert response.text == WARM_REPLY
    assert response.is_crisis is True
    assert response.crisis_level == 1
    assert response.teach_action != "teach"


@pytest.mark.parametrize(
    "message, level, lang",
    [
        pytest.param("I have a plan to end my life tonight", "L4", "en", id="L4-en"),
        pytest.param("मैंने नोट लिख दिया है", "L3", "hi", id="L3-hi"),
    ],
)
def test_levels_3_and_4_never_call_the_model(message, level, lang, stores):
    model = FakeModel(WARM_REPLY)
    assert_is_helpline(ask(pipeline_with(model), message), stores, level, lang)
    assert model.calls == 0


# --- through the API ------------------------------------------------------------------------


@pytest.fixture
def api(stores, monkeypatch):
    monkeypatch.setattr(limits, "chat_limiter", limits.RateLimiter(0))

    def make(model):
        app = FastAPI()
        register_error_handlers(app)
        app.include_router(chat_router)
        app.state.pipeline = pipeline_with(model)
        return TestClient(app)

    return make


def test_the_api_answers_a_failed_crisis_reply_with_helplines_not_a_503(api, stores):
    client = api(FakeModel(RuntimeError("429 RESOURCE_EXHAUSTED")))
    response = client.post(
        "/chat", json={"message": "I just want to die, I wish I was dead", "session_id": "s1"}
    )
    assert response.status_code == 200
    assert response.json()["text"] == helpline(stores, "en")


def test_an_ordinary_message_still_gets_the_calm_503(api):
    client = api(FakeModel(RuntimeError("429 RESOURCE_EXHAUSTED")))
    response = client.post("/chat", json={"message": "I had an argument with my brother", "session_id": "s1"})
    assert response.status_code == 503
    assert response.json()["message"] == COMPANION_UNAVAILABLE_MESSAGE

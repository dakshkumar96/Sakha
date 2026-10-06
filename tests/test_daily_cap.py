"""The site-wide daily cap on model calls.

Many visitors, each under their own per-minute limit, must not be able to use
up the free model quota together. Crisis messages still reach a helpline.
"""
from __future__ import annotations

from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api import limits
from backend.api.chat import router as chat_router
from backend.api.errors import DAILY_LIMIT_MESSAGE, register_error_handlers
from backend.conversation.errors import DailyCapReached
from backend.engines import crisis_detector
from backend.llm.budget import BudgetedClient, DailyCallBudget
from tests.fakes import FakeModel, pipeline_with, stores

WARM_REPLY = "I hear you. What happened after that?"
ORDINARY = "I had an argument with my brother"


def test_the_budget_allows_exactly_its_cap_each_day():
    today = [date(2026, 10, 6)]
    budget = DailyCallBudget(3, today=lambda: today[0])
    for _ in range(3):
        budget.take()
    with pytest.raises(DailyCapReached):
        budget.take()
    assert budget.used_today == 3
    today[0] = date(2026, 10, 7)
    budget.take()
    assert budget.used_today == 1


def test_zero_turns_the_daily_cap_off():
    budget = DailyCallBudget(0)
    for _ in range(5000):
        budget.take()


def test_a_capped_call_never_reaches_the_model():
    model = FakeModel(WARM_REPLY)
    client = BudgetedClient(model, DailyCallBudget(2))
    client.chat.completions.create(messages=[])
    client.chat.completions.create(messages=[])
    with pytest.raises(DailyCapReached):
        client.chat.completions.create(messages=[])
    assert model.calls == 2


def test_the_daily_limit_message_is_short_and_has_no_setup_words():
    assert len(DAILY_LIMIT_MESSAGE) < 100
    for word in ("quota", "gemini", "cap", ".env", "api"):
        assert word not in DAILY_LIMIT_MESSAGE.lower()


@pytest.fixture
def site(monkeypatch):
    """The real chat route and pipeline behind the proxy, per-address limit on."""
    monkeypatch.setattr(limits, "chat_limiter", limits.RateLimiter(10))

    def make(cap: int):
        model = FakeModel(WARM_REPLY)
        app = FastAPI()
        register_error_handlers(app)
        app.include_router(chat_router)
        app.state.pipeline = pipeline_with(BudgetedClient(model, DailyCallBudget(cap)))
        client = TestClient(app, client=("172.18.0.1", 5000))  # the proxy

        def send(message: str, address: str):
            return client.post(
                "/chat",
                json={"message": message, "session_id": address},
                headers={"x-forwarded-for": address},
            )

        return model, send

    return make


def test_the_cap_holds_against_many_addresses_each_under_their_own_limit(site):
    model, send = site(cap=3)
    responses = [send(ORDINARY, f"203.0.113.{n}") for n in range(1, 9)]

    assert responses[0].status_code == 200
    assert model.calls <= 3, "the cap is never exceeded"
    assert responses[-1].status_code == 503
    for refused in (r for r in responses if r.status_code != 200):
        assert refused.status_code == 503, "each address sent once, so this is not the per-address limit"
        assert refused.json() == {"error": "daily_limit_reached", "message": DAILY_LIMIT_MESSAGE}
        assert int(refused.headers["retry-after"]) > 0


def test_after_the_cap_a_crisis_message_still_gets_the_helpline(site):
    model, send = site(cap=1)
    send(ORDINARY, "203.0.113.1")
    assert send(ORDINARY, "203.0.113.2").status_code == 503

    crisis = send("I just want to die, I wish I was dead", "203.0.113.3")
    assert crisis.status_code == 200
    expected = crisis_detector.helpline_message(stores().taxonomy.helpline_refs(), lang="en")
    assert crisis.json()["text"] == expected
    assert model.calls == 1

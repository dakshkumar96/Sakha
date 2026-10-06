"""A site-wide daily cap on model calls.

The per-visitor rate limits stop one address hammering the API, but many
addresses together could still use up the free Gemini quota and take the site
down for everyone. This caps every model call the site makes in a day.
"""
from __future__ import annotations

import threading
from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Any, Callable

from backend.conversation.errors import DailyCapReached


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


class DailyCallBudget:
    """At most `per_day` model calls in one UTC day, across all visitors. Zero turns it off.

    The count lives in this process (the container runs one) and starts again
    at midnight UTC or on a restart. Google's free day resets at midnight
    Pacific, so keep the cap comfortably under the quota.
    """

    def __init__(self, per_day: int, today: Callable[[], date] = _utc_today) -> None:
        self.per_day = per_day
        self._today = today
        self._day: date | None = None
        self._used = 0
        self._lock = threading.Lock()

    def take(self) -> None:
        if self.per_day <= 0:
            return
        with self._lock:
            day = self._today()
            if day != self._day:
                self._day, self._used = day, 0
            if self._used >= self.per_day:
                raise DailyCapReached(f"daily model call cap of {self.per_day} reached")
            self._used += 1

    @property
    def used_today(self) -> int:
        with self._lock:
            return self._used if self._day == self._today() else 0


class BudgetedClient:
    """Spends one unit of the budget before every model call it passes on."""

    def __init__(self, client: Any, budget: DailyCallBudget) -> None:
        self._client = client
        self._budget = budget
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> Any:
        self._budget.take()
        return self._client.chat.completions.create(**kwargs)

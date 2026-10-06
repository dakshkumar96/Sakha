"""Per-address rate limits and input size caps for the public routes.

There is no sign-in, so the only thing that tells visitors apart is their
address. Counts live in this process. The container runs one uvicorn process,
so the limit is exact. With more workers each would keep its own count.
"""
from __future__ import annotations

import ipaddress
import threading
import time

from fastapi import Request

from backend.api.errors import ApiError
from backend.config import get_settings

WINDOW_SECONDS = 60

TOO_MANY_MESSAGE = "You're going a little fast. Please wait a moment and try again."


def client_address(request: Request) -> str:
    """The visitor's address.

    The API sits behind Caddy, so the direct peer is the proxy and every
    visitor would look the same. When the peer is a private or loopback
    address, the address Caddy wrote last in X-Forwarded-For is used instead.
    A direct request from the internet cannot use the header to pick its
    own address, because only private peers are trusted.
    """
    peer = request.client.host if request.client else "unknown"
    try:
        trusted_proxy = ipaddress.ip_address(peer).is_private
    except ValueError:
        return peer
    if not trusted_proxy:
        return peer
    forwarded = request.headers.get("x-forwarded-for", "")
    last = forwarded.split(",")[-1].strip()
    try:
        ipaddress.ip_address(last)
    except ValueError:
        return peer
    return last


class RateLimiter:
    """At most `per_minute` calls per address in any 60 seconds. Zero turns it off."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._next_sweep = 0.0

    def check(self, address: str) -> None:
        if self.per_minute <= 0:
            return
        now = time.monotonic()
        with self._lock:
            if now >= self._next_sweep:
                self._hits = {
                    a: h for a, h in self._hits.items() if h and now - h[-1] < WINDOW_SECONDS
                }
                self._next_sweep = now + WINDOW_SECONDS
            recent = [t for t in self._hits.get(address, []) if now - t < WINDOW_SECONDS]
            blocked = len(recent) >= self.per_minute
            if not blocked:
                recent.append(now)
            self._hits[address] = recent
        if blocked:
            raise ApiError(
                429,
                "rate_limited",
                TOO_MANY_MESSAGE,
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )

    def tracked_addresses(self) -> int:
        return len(self._hits)


_settings = get_settings()
chat_limiter = RateLimiter(_settings.chat_rate_per_minute)
tts_limiter = RateLimiter(_settings.tts_rate_per_minute)


def limit_chat(request: Request) -> None:
    chat_limiter.check(client_address(request))


def limit_tts(request: Request) -> None:
    tts_limiter.check(client_address(request))


def require_max_length(text: str, limit: int, code: str, message: str) -> None:
    if len(text) > limit:
        raise ApiError(400, code, message)

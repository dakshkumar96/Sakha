"""Failures the conversation layer raises. The API turns them into safe replies."""
from __future__ import annotations


class GenerationUnavailable(RuntimeError):
    """The model could not write a reply.

    The message is for the server log only. It may name keys or quotas. The API
    turns this into a fixed, calm 503 (see backend/api/errors.py), so none of it
    reaches the user, and a failure can never be mistaken for a real reply.
    """


class DailyCapReached(GenerationUnavailable):
    """The site has used today's share of model calls (GEMINI_DAILY_CALL_CAP).

    Raised before the model is called, so the free quota itself never runs out.
    Crisis turns still get the helpline text, like any other model failure.
    """

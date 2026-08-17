"""Lazy sentence-transformers wrapper.

Per the Phase 2 plan: "optional transformers must not block health if
heavy deps fail." If sentence-transformers / torch aren't installed or
fail to load, the app degrades to tag-only (taxonomy) retrieval instead
of crashing.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("krishna.embedder")


class Embedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._load_failed = False

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return True
        if self._load_failed:
            return False
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            return True
        except Exception:  # noqa: BLE001 - degrade gracefully, log for ops
            logger.exception("Embedding model failed to load; falling back to tag-only retrieval")
            self._load_failed = True
            return False

    @property
    def available(self) -> bool:
        return self._ensure_loaded()

    def encode(self, texts: list[str]):
        if not self._ensure_loaded():
            return None
        return self._model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        )

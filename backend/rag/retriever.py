"""Hybrid retriever: taxonomy tag path + FAISS semantic path.

Pipeline (per docs/phase-2-runtime-plan.md §7.2):
  1. Tag path: emotion_to_verses[primary] + secondaries -> +1.0 score
  2. Semantic path: FAISS top_k over query text -> cosine score
  3. Union + score
  4. Filter: id in allowlist; not already delivered this session when possible
  5. Prefer quality == tier_a on close scores
  6. Cap to settings.max_verses_per_turn
"""
from __future__ import annotations

import logging
from pathlib import Path

from backend.rag.embedder import Embedder
from backend.rag.indexer import load_index
from backend.rag.taxonomy_store import TaxonomyStore
from backend.rag.verse_store import VerseStore

logger = logging.getLogger("krishna.retriever")


class Retriever:
    def __init__(
        self,
        verse_store: VerseStore,
        taxonomy_store: TaxonomyStore,
        embedder: Embedder,
        faiss_index_path: Path,
        faiss_id_map_path: Path,
        top_k: int = 8,
    ):
        self.verse_store = verse_store
        self.taxonomy_store = taxonomy_store
        self.embedder = embedder
        self.top_k = top_k
        self._index, self._chunk_verse_ids = load_index(faiss_index_path, faiss_id_map_path)

    @property
    def faiss_loaded(self) -> bool:
        return self._index is not None

    def _tag_candidates(self, emotion_id: str | None) -> dict[str, float]:
        if not emotion_id:
            return {}
        mapping = self.taxonomy_store.verse_mapping(emotion_id)
        if not mapping:
            return {}
        scored: dict[str, float] = {}
        if mapping.get("primary"):
            scored[mapping["primary"]] = 1.2
        for vid in mapping.get("secondary", []) or []:
            scored[vid] = max(scored.get(vid, 0.0), 0.9)
        return scored

    def _semantic_candidates(self, query: str) -> dict[str, float]:
        if self._index is None or not self.embedder.available:
            return {}
        import numpy as np

        vec = self.embedder.encode([query])
        if vec is None:
            return {}
        scores, idxs = self._index.search(np.asarray(vec, dtype="float32"), self.top_k)
        scored: dict[str, float] = {}
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0 or idx >= len(self._chunk_verse_ids):
                continue
            verse_id = self._chunk_verse_ids[idx]
            scored[verse_id] = max(scored.get(verse_id, 0.0), float(score))
        return scored

    def retrieve(
        self,
        query: str,
        emotion_id: str | None,
        allowlist: set[str],
        already_delivered: set[str],
        crisis_flags: set[str],
        cap: int = 2,
    ) -> list[str]:
        tag_scores = self._tag_candidates(emotion_id)
        semantic_scores = self._semantic_candidates(query)

        combined: dict[str, float] = dict(tag_scores)
        for vid, score in semantic_scores.items():
            combined[vid] = combined.get(vid, 0.0) + score

        def valid(vid: str) -> bool:
            if allowlist and vid not in allowlist:
                return False
            if self.verse_store.blocked_for(vid, crisis_flags):
                return False
            return True

        candidates = [vid for vid in combined if valid(vid)]

        # Prefer not-yet-delivered verses; fall back to repeats only if nothing else.
        fresh = [vid for vid in candidates if vid not in already_delivered]
        pool = fresh if fresh else candidates

        def sort_key(vid: str) -> tuple[float, float]:
            tier_bonus = 0.15 if self.verse_store.is_tier_a(vid) else 0.0
            return (combined.get(vid, 0.0) + tier_bonus,)

        pool.sort(key=sort_key, reverse=True)
        return pool[:cap]

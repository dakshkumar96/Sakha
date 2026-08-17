"""FAISS index build/load helpers.

Used by scripts/build_faiss.py (offline build) and by retriever.py at
startup (load). Index lives at knowledge/indices/faiss.index +
id_map.json — never committed as a giant binary if it grows large; see
knowledge/indices/README.md.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("krishna.indexer")


def build_index(vectors, chunk_ids: list[str], index_path: Path, id_map_path: Path) -> None:
    import faiss
    import numpy as np

    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.asarray(vectors, dtype="float32"))

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    id_map_path.write_text(
        json.dumps({"chunk_ids": chunk_ids}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_index(index_path: Path, id_map_path: Path):
    """Returns (index, chunk_ids) or (None, None) if unavailable/broken."""
    if not index_path.exists() or not id_map_path.exists():
        return None, None
    try:
        import faiss

        index = faiss.read_index(str(index_path))
        chunk_ids = json.loads(id_map_path.read_text(encoding="utf-8"))["chunk_ids"]
        return index, chunk_ids
    except Exception:  # noqa: BLE001 - degrade gracefully
        logger.exception("Failed to load FAISS index; falling back to tag-only retrieval")
        return None, None

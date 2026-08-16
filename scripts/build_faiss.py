"""Build the FAISS index for Krishna AI's RAG layer (Phase 2).

Reads knowledge/chunks/gita_verse_chunks.jsonl (filter weight >= 0.4),
embeds `embed_text` with sentence-transformers, writes:
  knowledge/indices/faiss.index
  knowledge/indices/id_map.json  (parallel list of verse_id per row)

Usage:
    python scripts/build_faiss.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.rag.embedder import Embedder  # noqa: E402
from backend.rag.indexer import build_index  # noqa: E402

CHUNKS_PATH = ROOT / "knowledge" / "chunks" / "gita_verse_chunks.jsonl"
INDEX_PATH = ROOT / "knowledge" / "indices" / "faiss.index"
ID_MAP_PATH = ROOT / "knowledge" / "indices" / "id_map.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MIN_WEIGHT = 0.4


def main() -> None:
    if not CHUNKS_PATH.exists():
        print(f"ERROR: {CHUNKS_PATH} not found. Run Phase 1 scripts/build_chunks.py first.")
        sys.exit(1)

    rows = []
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("weight", 1.0) >= MIN_WEIGHT:
                rows.append(obj)

    if not rows:
        print("ERROR: no chunks passed the weight filter.")
        sys.exit(1)

    print(f"Embedding {len(rows)} verse chunks with {MODEL_NAME} ...")
    embedder = Embedder(MODEL_NAME)
    if not embedder.available:
        print(
            "ERROR: sentence-transformers is not available in this environment.\n"
            "Install backend/requirements.txt (torch + sentence-transformers) and retry.\n"
            "The app will run without FAISS (tag-only retrieval) until this succeeds."
        )
        sys.exit(1)

    texts = [r["embed_text"] for r in rows]
    verse_ids = [r["verse_id"] for r in rows]
    vectors = embedder.encode(texts)

    build_index(vectors, verse_ids, INDEX_PATH, ID_MAP_PATH)
    print(f"Wrote {INDEX_PATH}")
    print(f"Wrote {ID_MAP_PATH}")
    print(f"Rows indexed: {len(rows)}")


if __name__ == "__main__":
    main()

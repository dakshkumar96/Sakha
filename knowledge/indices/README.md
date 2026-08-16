# FAISS / vector index rebuild

Phase 1 ships **chunk JSONL**, not a committed FAISS binary (size/portability). Rebuild in Phase 2 or locally.

## Inputs

| File | Layer |
|------|--------|
| `knowledge/chunks/gita_verse_chunks.jsonl` | Verse cards |
| `knowledge/chunks/book_chunks.jsonl` | Commentary / narrative |
| `knowledge/chunks/conversation_chunks.jsonl` | Persona examples / keepers |

Filter: `weight >= 0.4`.

## Defaults

| Item | Value |
|------|--------|
| Model | `sentence-transformers/all-MiniLM-L6-v2` (EN-first) |
| Index | FAISS `IndexFlatIP` (normalize embeddings for cosine) |
| Outputs | `knowledge/indices/faiss.index`, `knowledge/indices/id_map.json` |

## Suggested script (Phase 2)

```text
python scripts/build_faiss.py
```

Embed field: `embed_text` (verse/conversation/book — for book use `text`).  
Citation filter always: any retrieved `verse_id` ∈ `knowledge/validation/citation_allowlist.txt`.

## Note

Do not invent `BG_*` IDs in retrieval post-processing.

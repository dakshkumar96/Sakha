# Phase 1 validation checklist

| Gate | Status |
|------|--------|
| `knowledge/gita/verses.json` 700 cards, EN non-empty | Done |
| `citation_allowlist.txt` matches spine | Done |
| `anchor_verse_ids.json` ≥60 and tier-A | Done (66) |
| Taxonomy emotions + situations + emotion_to_verses + crisis_forbidden | Done |
| Behaviour-matrix situations covered | Done |
| Chunk layers + counts.json | Done |
| `validate_kb.py` PASS | Done |
| `sample_retrieval.md` | Done |
| `hi_gaps.md` | Done (tier-A HI pending progressive fill) |
| `indices/README.md` | Done |
| `docs/v1/knowledge/README.md` | Done |

## Chunk counts (from `knowledge/chunks/counts.json`)

- gita_verse_chunks: **700**
- book_chunks: **1722**
- conversation_chunks: **100**


## Rebuild

```text
python scripts/build_spine.py
python scripts/enrich_tier_a.py
python scripts/build_taxonomy.py
python scripts/build_chunks.py
python scripts/validate_kb.py
```

# Krishna AI knowledge field guide (V1)

Phase 1 product-grade knowledge base for citation-safe teaching retrieval.

## Paths

| Artifact | Path |
|----------|------|
| Plan | [docs/phase-1-knowledge-plan.md](../../phase-1-knowledge-plan.md) |
| Verses (700) | `knowledge/gita/verses.json` |
| Anchors / tier-A | `knowledge/gita/anchor_verse_ids.json`, `tier_a_enrichment.json` |
| Traditions | `knowledge/gita/traditions_map.json` |
| Taxonomy | `knowledge/taxonomy/` |
| Chunks | `knowledge/chunks/*.jsonl` |
| Allowlist | `knowledge/validation/citation_allowlist.txt` |
| Validator | `python scripts/validate_kb.py` |

## Verse ID

`BG_{chapter}_{verse}` e.g. `BG_2_47`. Spoken form: “chapter 2, verse 47”.

## Quality tiers

| `quality` | Meaning |
|-----------|---------|
| `spine` | Full EN from As It Is parse (+tiny fallbacks) |
| `tier_a` | Emotions, strategy, readiness, secondaries — teaching core |

## Citation rule

Generators / APIs may only cite IDs in the allowlist. Never invent verse numbers.

## Rebuild spine + enrichments

```bash
python scripts/build_spine.py
python scripts/enrich_tier_a.py
python scripts/build_taxonomy.py
python scripts/build_chunks.py
python scripts/validate_kb.py
```

## Hindi

`translations.hi` mostly empty on tier-A in V1; see `knowledge/validation/hi_gaps.md`. OCR HI text is available for later align.

## Phase 2

Load verses + taxonomy → hybrid retrieve → crisis gate → generate with `prompts/system_v1.txt` → TTS (Kokoro-FastAPI).

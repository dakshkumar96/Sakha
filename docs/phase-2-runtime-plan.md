# Phase 2 — Runtime Core (Detailed Plan)

**Scope:** Build the **LLM-last brain** only: FastAPI pipeline that loads Phase 0 persona + Phase 1 knowledge and returns citation-safe JSON.
**Outcome:** Local `POST /chat` works end-to-end (text). Stable API contract for Phase 3 (UI/voice).
**Depends on:** Phase 0 ([prompts/system_v1.txt](../prompts/system_v1.txt)) and Phase 1 VALIDATE PASS (700 verses, taxonomy, chunks, allowlist).
**Not in Phase 2:** Next.js avatar, Web Speech, Kokoro shipping UX, soft auth@3, PostHog, Render/Vercel, fine-tune, full 20 engines, Soul Graph depth.

**Status:** Built and smoke-passing (5/5) as of this document.

---

## 1. Master principle

```text
User message
  → crisis_detector (always first)
  → emotion + intent + appraisal_lite + defence_lite + guna
  → response_planner (witness | question | validate | teach | crisis | crisis_soft)
  → hybrid RAG (tags + FAISS) if teaching
  → citation allowlist filter
  → Groq + system_v1 + planner instructions
  → post-filters (fake BG stripping)
  → ChatResponse JSON
```

LLM is **last**, never first. Engines are lexicon-first; the optional
transformer stack must not block health if heavy deps fail.

---

## 2. Success criteria — verified

| Criterion | Test | Result |
|-----------|------|--------|
| Crisis L3–L4 | Response is helplines only; no teach verse | PASS |
| Allowlist | Every returned `verse_id` ∈ citation_allowlist.txt | PASS |
| Teach gate | Ordinary fear/shame: ≥2 companion questions before first verse | PASS |
| Persona | Loads system_v1.txt; “Are you Krishna?” → honest no | PASS |
| Retrieval | Fear-of-outcome path returns BG_2_47 | PASS |
| API | `GET /health` OK; `POST /chat` returns structured body | PASS |
| No secrets | Groq key from `.env` only | PASS |

Reproduce: `python scripts/smoke_test_phase2.py` with the backend running.

---

## 3. Repo layout (as built)

```text
backend/
  main.py                 # FastAPI app, CORS, /health, startup wiring
  config.py               # pydantic-settings + knowledge paths
  requirements.txt
  api/chat.py             # POST /chat
  engines/
    crisis_detector.py    # lexicon, NONE/L1/L2/L3/L4 + fixed helpline text
    emotion_analyzer.py   # 39 emotion ids from taxonomy
    intent_detector.py    # venting/seeking/questioning_god/pushing_back/curiosity
    appraisal_analyzer.py # control / agency / fairness
    defence_detector.py   # spiritual bypass / minimisation / intellectualisation
    guna_detector.py      # tamas / rajas / sattva tone skew
    response_planner.py   # the only place that decides use_verse_now
  rag/
    verse_store.py        # verses.json loader
    taxonomy_store.py     # emotions, emotion_to_verses, crisis_forbidden
    embedder.py           # lazy sentence-transformers, degrades gracefully
    indexer.py            # FAISS build/load
    retriever.py          # hybrid tag + semantic
    citation_filter.py    # the citation safety wall
  conversation/
    pipeline.py           # orchestration
    response_generator.py # Groq client + prompt composition
    schemas.py            # ChatRequest / ChatResponse
  memory/session_store.py # in-process turns, questions, verses, last_emotion
scripts/build_faiss.py
scripts/smoke_test_phase2.py
```

`knowledge/` stays the **read-only source of truth** — nothing is duplicated under `backend/`.

---

## 4. Crisis routing (safety-critical)

Two distinct paths, deliberately:

| Level | Path | Rationale |
|-------|------|-----------|
| L3 / L4 | **Fixed vetted string**, no LLM at all | Never let a model improvise in an emergency |
| L1 / L2 | Normal LLM path, but `use_verse_now=False` and a crisis-aware planner instruction | Someone exhausted or low is not in acute danger; a helpline template would be alarming and cold |
| NONE | Full pipeline | — |

`crisis_detector` is intentionally over-sensitive: a false positive routes
to care, a false negative does not. L4 requires means/finality **and**
immediacy language; L3 is means/finality alone; L2 is passive ideation;
L1 is hopelessness without death ideation.

---

## 5. The teach gate

`response_planner` refuses to teach until:

- not L2–L4 crisis,
- at least **2** companion questions asked this session (`teach_gate_min_questions`),
  or the user is seeking guidance after ≥1 question,
- no unaddressed defence (spiritual bypass forces a redirect question),
- `LISTEN_FIRST_EMOTIONS` (grief, existential terror, fear of death,
  wavering faith) delay teaching further regardless of the counter.

---

## 6. Citation safety wall

The model may cite **only** ids retrieved this turn that are also in the
allowlist. Everything else is stripped from the text — including
scripture the model recalls from its own weights on a listening turn.

This was not theoretical: during the first live run the model quoted BG
2.47 on a question turn. The filter caught the id; the fix also
strengthened the no-verse instruction and added dangling-text cleanup so
removal doesn't leave `"In , it's written"`.

---

## 7. API surface

| Method | Path | Behaviour |
|--------|------|-----------|
| GET | `/health` | `{status, knowledge_loaded, verse_count, faiss_loaded, groq_configured}` |
| POST | `/chat` | full pipeline |

Run:

```bash
uvicorn backend.main:app --reload --port 8000
```

Build the index first (one-off, ~700 vectors):

```bash
python scripts/build_faiss.py
```

---

## 8. Known gaps carried into Phase 3

- Session memory is in-process; lost on restart (Supabase is Phase 4).
- Emotion detection is lexicon-only — short follow-ups fall back to
  `session.last_emotion` rather than re-detecting.
- Hindi/Hinglish input is not yet detected or routed.
- No `/tts` proxy yet; Kokoro stays a Phase 3 concern.
- No automated persona-quality eval beyond the 5 smoke checks; the full
  [eval_prompts.md](v1/persona/eval_prompts.md) suite is still manual.

---

## 9. Handoff to Phase 3

Phase 3 consumes the stable `ChatRequest` / `ChatResponse` contract
(`backend/conversation/schemas.py`), base URL
`NEXT_PUBLIC_API_URL=http://localhost:8000`, and the UI-relevant fields:
`text`, `verse_citations`, `is_crisis`, `response_style`, `teach_action`.

---

## 10. Absolute rules (unchanged)

1. Crisis detector every message before the LLM
2. LLM last
3. Teach gate
4. Allowlist / retrieved-only citations
5. system_v1 identity — nimitta, never divinity
6. Free stack only
7. No conversation content logged to third parties in Phase 2

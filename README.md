# Krishna AI

A voice-first companion grounded in the Bhagavad Gita — not a chatbot in a Krishna costume, not Krishna himself. A *nimitta*, a digital sevak: an instrument that reflects the Gita's teachings back to someone carrying something heavy, in their own language, with real citations.

> Someone alone at 2am, not looking for information — looking for evidence they're not as unseen as they feel.

## What it does

- Listens first. Doesn't teach until it has actually understood what's going on (a "teach gate" — at least two real questions before any verse).
- Speaks Hindi, Hinglish, or English, matching whatever the person used.
- Cites real Bhagavad Gita verses only — chapter and verse, checked against an allowlist, never invented.
- Detects crisis language (English, Hindi, and roman Hinglish) and routes straight to real helplines instead of scripture.
- Remembers the shape of a conversation within a session — recurring themes, verses already used, images already used — so it doesn't repeat itself.
- Never claims to be Krishna, God, or a therapist. Says so plainly if asked.

## Stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, Google Gemini |
| Retrieval | FAISS + sentence-transformers (hybrid tag + semantic search over the Gita) |
| Frontend | Next.js (App Router), TypeScript, Tailwind |
| Voice | Web Speech API (STT) → FastAPI → Kokoro-FastAPI (TTS), with a browser-speech fallback |
| Knowledge base | Hand-curated Gita verse spine + emotion/situation taxonomy, stored as JSON |

No paid services required to run it locally.

## Repo layout

```
backend/            FastAPI app — engines, RAG, session memory, LLM generation
web/                 Next.js frontend
knowledge/           The Gita knowledge base: verses, taxonomy, chunks, validation
prompts/             System prompt (constitution), language/voice guides, few-shot examples
docs/                Phase-by-phase build plans (persona → knowledge → runtime → UI/voice → hardening → depth)
scripts/             Knowledge-base build/validate scripts + smoke tests + eval suite
```

## Running it locally

**1. Backend**

```bash
cd backend
pip install -r requirements.txt
```

Copy `.env.example` to `.env` at the repo root and set `GEMINI_API_KEY` (free at [aistudio.google.com](https://aistudio.google.com)).

```bash
uvicorn backend.main:app --reload --port 8000
```

Check it's healthy: `curl http://localhost:8000/health`

**2. Frontend**

```bash
cd web
npm install
npm run dev
```

Opens on `http://localhost:3000`.

**3. Voice (optional)**

Text-to-speech works out of the box via the browser's built-in speech synthesis. For the nicer Kokoro voice:

```bash
docker compose -f docker/kokoro-compose.yml up -d
```

If Kokoro isn't running, the app falls back to browser speech automatically — nothing breaks.

## Testing

```bash
python scripts/validate_kb.py          # knowledge base integrity
python scripts/smoke_test_crisis.py    # crisis detection, offline, no server needed
python scripts/smoke_test_phase5.py    # safety + retrieval, needs the backend running
python scripts/eval_persona_suite.py   # full multi-turn persona eval
```

## Where to look next

- [`docs/phases-roadmap.md`](docs/phases-roadmap.md) — build order and current status of every phase
- [`prompts/system_v1.txt`](prompts/system_v1.txt) — the constitution: who this is, what it will never do
- [`knowledge/validation/`](knowledge/validation/) — gaps, checklists, and known limitations, kept honest on purpose

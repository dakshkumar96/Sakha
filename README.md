# Sakha

Sakha is a voice companion built on the Bhagavad Gita. You talk to it about whatever is weighing on you. It listens, asks questions until it understands, and only then answers with a teaching from the Gita, citing the real chapter and verse.

It isn't Krishna and it doesn't pretend to be. It's an AI. It isn't a therapist or a religious authority either, and the app says so on screen.

Live at [sakha-hazel.vercel.app](https://sakha-hazel.vercel.app).

> Someone alone at 2am. Not looking for information. Looking for evidence they're not as unseen as they feel.

## What it does

- It listens first. A "teach gate" means it asks at least two real questions before it offers any verse.
- It speaks English or Hindi. You pick one, and every reply stays in that one language.
- It only cites real Gita verses. Every citation is checked against an allowlist, and any verse the model invents gets stripped out.
- It watches for crisis language in English, Hindi, and Hindi typed in Roman letters. The most serious messages skip the model completely and get a fixed message with real helpline numbers.
- It remembers the shape of a conversation while it lasts. Recurring themes, verses it has used and images it has used all count, so it doesn't repeat itself.
- It never claims to be Krishna, God or a therapist.

## How a reply gets made

1. The browser listens with the Web Speech API and sends the text to `POST /chat`.
2. The crisis check runs first. It's keyword based and never calls the model. Levels 3 and 4 get the helpline text straight away. Levels 1 and 2 get a warm reply from the model if it answers within 25 seconds. If it fails, times out or comes back empty, they get the helpline text instead.
3. A set of small engines reads emotion, intent and defences. A planner then decides what this turn is for. It might ask a question, sit with what was said, validate it, or teach.
4. On a teaching turn, retrieval finds verses using FAISS and sentence-transformers alongside tag matching.
5. Gemini writes the reply. A citation filter removes any verse it wasn't handed.
6. The browser speaks the reply with Kokoro if it's running, and with its own built-in voice if not.

## The prompt documents

The model works from the same documents on every turn. They live in `prompts/`. Four of them do most of the work, and a fifth adds notes on style.

| File | What it is |
|---|---|
| `system_v1.txt` | The system prompt, now v1.4. Who Sakha is, what it never does, and the crisis rules. |
| `krishna_language.md` | The Language Bible. Registers, forms of address, and phrases to use and to avoid. |
| `emotion_response.json` | The emotion-response map. 40 emotions, each with what tends to sit underneath it and how to answer. |
| `fewshot_v5.json` | 100 example conversations. 76 in English, 21 in Hindi and 3 with an English question and a Hindi answer. One gets picked per turn by emotion and language. |
| `krishna_analysis.md` | Speech-pattern notes on mirrors, questions and metaphors. It gets loaded along with the system prompt. |

## The API

Two routes do the work. There's no sign-in, so the limits are counted per visitor address.

- `POST /chat` takes a message and the recent history. It returns the reply, any verse citations and an English subtitle. Each address gets 10 a minute.
- `POST /tts` turns text into speech through Kokoro. Each address gets 20 a minute. When Kokoro isn't running it returns a 503 and the browser falls back to its own voice.
- `GET /health` reports whether the knowledge base, FAISS, Gemini and Kokoro are ready.

Inputs are capped too. A message can be up to 2,000 characters. History can hold up to 60 messages of up to 6,000 characters each. Text for speech can be up to 6,000 characters. IPv6 visitors are counted per /56 network, so one household can't get round the limit by switching addresses.

On top of that there's a site-wide cap of 400 model calls a day, so the free Gemini quota never runs out. Once it's hit, ordinary chats get a calm "please come back tomorrow". Crisis messages still get the helpline.

All of these settings are listed in `.env.example`.

## What it costs

Nothing, right now. The backend runs on an Oracle Cloud Always Free VM behind Caddy, with a free Let's Encrypt certificate and a free DuckDNS name. The frontend is on Vercel's free Hobby plan. Gemini is on the free tier.

That holds at low traffic. The free Gemini tier has daily limits, which is why the 400 call cap exists. On a busy day Sakha stops answering ordinary chats until midnight UTC. Vercel's Hobby plan is meant for non-commercial projects. The Kokoro voice isn't deployed yet, so the live site speaks with your browser's voice.

## Running it locally

You need Python 3.11 or newer, Node 20 or newer, and a free Gemini key from [aistudio.google.com](https://aistudio.google.com).

**1. Backend.** Run these from the repo root.

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
copy .env.example .env
```

Mac or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
```

Put your key in `.env` as `GEMINI_API_KEY`. The install pulls PyTorch, which is about 200 MB.

Build the verse search index once. Without it, retrieval falls back to tag matching only.

```bash
python scripts/build_faiss.py
```

Then start the API. This command is the same on every OS.

```bash
uvicorn backend.main:app --reload --port 8000
```

Check it's up with `curl http://localhost:8000/health`.

**2. Frontend.**

```bash
cd web
npm install
npm run dev
```

It opens on `http://localhost:3000` and talks to `http://localhost:8000` unless you set `NEXT_PUBLIC_API_URL`.

**3. Voice (optional).** Speech works straight away with your browser's voice. For the Kokoro voice, run it in Docker.

```bash
docker compose -f docker/kokoro-compose.yml up -d
```

If Kokoro isn't running nothing breaks. The browser voice takes over.

## Tests

The automated tests fake the model, so they need no key and no network.

```bash
pip install pytest
python -m pytest tests
```

They cover the rate limits, the input caps, the daily cap, safe error messages, the crisis fallbacks and the one-language rule.

There are also some script checks. The last two call the running backend, which calls Gemini. Set `CHAT_RATE_PER_MINUTE=0` in `.env` first, or the rate limit will slow them down.

```bash
python scripts/validate_kb.py          # knowledge base integrity
python scripts/smoke_test_crisis.py    # crisis detection, offline, no server needed
python scripts/smoke_test_phase5.py    # safety and retrieval, needs the backend running
python scripts/eval_persona_suite.py   # multi-turn persona eval, needs the backend running
```

## Deploying

The backend runs in Docker on the Oracle VM and the frontend runs on Vercel. The steps are in [`DEPLOY.md`](DEPLOY.md).

## Limitations

- There are no accounts. Conversations live in your browser's local storage. The server only keeps session state in memory, and it's gone after a restart.
- Every message goes to Google's Gemini API so it can write the reply.
- Crisis detection is keyword based. It's tuned to fire too often rather than too rarely, because a false alarm is safer than a miss.
- The Gita knowledge base was built by hand. Its gaps and known issues are written up in [`knowledge/validation/`](knowledge/validation/).

## Where to look next

- [`docs/phases-roadmap.md`](docs/phases-roadmap.md) has the build order and where each phase stands.
- [`prompts/system_v1.txt`](prompts/system_v1.txt) is the system prompt, covering who Sakha is and what it will never do.
- [`knowledge/validation/`](knowledge/validation/) holds the gaps and checklists, kept honest on purpose.

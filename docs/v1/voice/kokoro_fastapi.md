# Voice: Kokoro-FastAPI (locked for now)

Repo: [remsky/Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)  
License path: Apache-2.0 wrapper around Kokoro-82M.

## Role in stack

| Direction | Tool |
|-----------|------|
| **STT (user speaks)** | Web Speech API (browser) |
| **TTS (companion speaks)** | **Kokoro-FastAPI** on port **8880** |
| Model | `kokoro` via OpenAI-compatible `/v1/audio/speech` |
| API key | `not-needed` (local service; add auth later if exposed) |

## Why this, not raw Kokoro

- Drop-in OpenAI speech client shape
- Docker images (CPU / NVIDIA / ROCm)
- Voice mixing (brand character from presets)
- Streaming, multiple formats (mp3/wav/opus…)
- Hindi + English in same service

## Local start (Windows)

Docker Desktop required. From any folder:

```powershell
# CPU (default for laptops without NVIDIA Docker)
docker run -d --name kokoro-tts -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest

# NVIDIA (if Docker GPU works)
# docker run -d --name kokoro-tts --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest
```

Or from this monorepo:

```powershell
docker compose -f docker/kokoro-compose.yml up -d
```

Check:
- API: http://localhost:8880/docs  
- Web UI: http://localhost:8880/web  
- Health sample: list voices `GET /v1/audio/voices`

Smoke test:

```powershell
python scripts/test_kokoro_tts.py
```

Writes `tmp/kokoro_sample.mp3` if the service is up.

## Env vars (app)

```bash
KOKORO_BASE_URL=http://localhost:8880/v1
KOKORO_API_KEY=not-needed
# Locked after bake-off — placeholders until you pick in /web
KOKORO_VOICE_EN=am_michael
KOKORO_VOICE_HI=hf_alpha
KOKORO_SPEED=0.9
```

Frontend never talks to Kokoro directly in production if CORS/auth is a concern preferred path:

```text
Browser → our FastAPI → Kokoro-FastAPI → audio bytes → browser
```

Local demos can hit `8880` from Next.js if CORS allows.

## OpenAI-compatible call shape

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8880/v1", api_key="not-needed")
speech = client.audio.speech.create(
    model="kokoro",
    voice="am_michael",  # or mix "am_michael(2)+am_fenrir(1)"
    input="I am a digital sevak — not God. Sit with that.",
    response_format="mp3",
    speed=0.9,
)
speech.stream_to_file("out.mp3")
```

Or raw HTTP `POST /v1/audio/speech` with the same JSON body.

## Brand voice bake-off (do once)

1. Open http://localhost:8880/web  
2. Paste lines from `docs/v1/persona/disclosure_scripts.md` + hard-truth stems from `voice_architecture.md`  
3. Try **warm male EN** presets and **Hindi `hf_*`**  
4. Optional mix for “our” timbre, e.g. `am_michael(2)+am_onyx(1)`  
5. Lock IDs into `KOKORO_VOICE_EN` / `KOKORO_VOICE_HI`  
6. Speed **0.85–0.95** for calm companion feel

Never market as “Krishna’s voice” — product voice / nimitta voice only.

## Deploy later

| Env | Notes |
|-----|--------|
| Dev | Docker on laptop, port 8880 |
| Prod | Separate container (not same process as chat FastAPI); pin image tag not only `:latest` |
| Free host | CPU is slow; cold starts hurt TTS latency — plan paid small instance if needed |

## Not in V1 Kokoro path

- Voice **cloning** of actors / film Krishnas  
- Spoken Sanskrit as divinity theatre  
- Public unauthenticated Kokoro on the open internet (rate-limit + internal network)

## Local voice without Docker (enabled in web/)

If Kokoro is down (`kokoro_reachable: false` on `/health`), the Next app still speaks:

```text
Prefer:  Browser → FastAPI POST /tts → Kokoro mp3
Fallback: Browser Speech Synthesis (system voices, no container)
```

- UI footer notes “Speaking with system voice…” when on fallback.
- Toggle **voice on / voice off** in the top bar; default is **on**.
- Mic (STT) is always browser Web Speech (Chrome/Edge best).

Install Docker + `docker compose -f docker/kokoro-compose.yml up -d` when you want the brand Kokoro voice instead of the OS TTS.

## End of V1 still true

STT stays browser Web Speech unless we add a better ASR later.

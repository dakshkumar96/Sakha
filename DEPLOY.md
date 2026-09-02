# Deploying Sakha

Everything that can be prepared in the repo is done: the root `Dockerfile`
(backend) and `web/` (frontend) are ready to point Hugging Face/Vercel at.
What's left requires your accounts — I can't create those or click through
dashboards for you. This is the exact order to do it in, because two of the
settings are circular (each service needs the other's URL) and doing it out
of order just means one extra redeploy, not a real problem.

**Scope of this deploy** (confirmed): Vercel (frontend, free) + a self-hosted
backend, soft-launch with no auth/message limits — anyone with the link can
use it, history stays browser-local only. Phase 4 (auth, encrypted
cross-device history) isn't built yet; this is intentional for now.

> **Backend moved off Render — twice.** Render's free tier (512MB RAM) was
> crash-looping under real use — torch + sentence-transformers kept getting
> the process killed mid-session, which showed up as random "can't reach the
> companion" errors that came and went. The original fix here was Hugging
> Face Spaces' free CPU Basic tier (16GB RAM), but **HF has since put Docker
> Spaces behind a paid PRO plan ($9/mo)** — confirmed live in the Space
> creation UI, not just docs. The genuinely-free path that's left is a
> self-hosted VM: see **[DEPLOY-ORACLE.md](DEPLOY-ORACLE.md)** (Oracle Cloud
> Always Free, real server admin instead of a git-push deploy). The
> Dockerfile below is shared by both the HF path (if you'd rather pay $9/mo
> for less setup effort) and the Oracle path. `render.yaml` is kept only as
> a fallback reference.

---

## 0. Push the repo

```bash
git push origin main
```

Everything after this step happens in the Vercel and Hugging Face dashboards.

---

## 1. Backend — pick one

**If you want $0/mo:** skip this section, follow
**[DEPLOY-ORACLE.md](DEPLOY-ORACLE.md)** instead, then come back to step 2
below once that backend URL is live.

**If you'd rather pay $9/mo for far less setup effort:** Hugging Face
Spaces, same Dockerfile, steps below.

1. [huggingface.co/new-space](https://huggingface.co/new-space) → **Space
   name**: `sakha-backend` (or anything) → **SDK: Docker** → **Docker
   template: Blank** → **Hardware: CPU basic — requires a PRO subscription
   ($9/mo)**, confirmed current as of this write-up; Static is the only SDK
   still free on this page → **Visibility**: your choice (public is fine;
   the app has no secrets baked into the image).
2. Create it, then push this repo to it as a second git remote:

   ```bash
   git remote add hf https://huggingface.co/spaces/<your-hf-username>/sakha-backend
   git push hf main
   ```

   Git will prompt for a username/password — use your HF username and an
   [access token](https://huggingface.co/settings/tokens) (write scope) as
   the password. The Space reads the root-level `Dockerfile` and builds
   automatically; watch progress under the Space's **Logs** tab.
3. In the Space → **Settings** → **Variables and secrets**, add:

   | Key | Type | Value |
   |---|---|---|
   | `GEMINI_API_KEY` | Secret | your key from [aistudio.google.com](https://aistudio.google.com) — free tier is fine |
   | `CORS_ORIGINS` | Variable | leave blank for now — comes back in step 3 |

   Everything else (`GEMINI_MODEL`, etc.) already has a sensible default in
   `backend/config.py`. Saving a variable restarts the Space automatically.
4. **Once it's live, check `https://<your-hf-username>-sakha-backend.hf.space/health`.**
   You want to see `"knowledge_loaded": true` and `"faiss_loaded": true` —
   with 16GB of headroom this should never come back `false` from memory
   pressure the way it did on Render.

Copy this URL for step 2. Note: PRO Spaces on CPU basic don't sleep the way
free tiers do, so this avoids the cold-start issue entirely — one of the
things you're paying for.

---

## 2. Frontend (`web/`) on Vercel

1. Vercel dashboard → **Add New** → **Project** → import this repo.
2. **Root Directory: set it to `web`.** This is the one setting that's easy
   to miss — without it, Vercel will try to build the whole monorepo root
   and fail.
3. Environment variable:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | your backend's URL from step 1 — `https://sakha-backend.duckdns.org` (Oracle) or `https://<your-hf-username>-sakha-backend.hf.space` (HF), no trailing slash |

4. Deploy. Framework preset (Next.js) and build command are auto-detected —
   nothing else to change.

Copy the resulting Vercel URL (`https://sakha-xxxx.vercel.app` or your custom
domain if you attach one).

---

## 3. Close the loop: set CORS on the backend

Set `CORS_ORIGINS` to `https://<your-vercel-url>`:

- **Oracle:** edit `CORS_ORIGINS` in `deploy/oracle/.env` on the VM, then
  `sudo docker compose up -d --build` to pick it up.
- **HF Spaces:** Space → **Settings** → **Variables and secrets** → edit
  `CORS_ORIGINS`. Saving restarts the Space automatically.

**This step is why the browser will show CORS errors if you test before
doing it.** Until `CORS_ORIGINS` is set, the frontend can't call the backend
at all.

To push future backend changes: on Oracle, `git pull` on the VM then
`docker compose up -d --build`; on HF, `git push hf main` (a second git
remote, alongside `origin`).

---

## 4. Verify end to end

Open the Vercel URL and send one message. Check:

- A reply comes back (confirms Gemini key + CORS are both right)
- It cites a real `BG_x_y` verse if the conversation reaches a teaching turn
- Voice: real Kokoro TTS isn't deployed yet (see below), so this will fall
  back to the browser's own speech synthesis automatically — that's expected
  for now, not a bug. Check the console for what `/tts` returned if unsure.

If something's wrong, `/health` on the backend is the fastest diagnostic —
it reports `knowledge_loaded`, `faiss_loaded`, `llm_configured`, and
`kokoro_reachable` individually.

---

## Optional: real Kokoro voice

`kokoro_reachable` in `/health` will show `false` until this is deployed —
until then, voice falls back to the browser's built-in speech synthesis,
which the app already handles gracefully. Real-time TTS inference wants
more memory/CPU than the backend alone, so if you're on the Oracle VM,
simplest is running Kokoro's public image as a third `docker compose`
service there (12GB is enough headroom for both) — add to
`deploy/oracle/docker-compose.yml`:

```yaml
  kokoro:
    image: ghcr.io/remsky/kokoro-fastapi-cpu:latest
    restart: always
    expose:
      - "8880"
```

then set `KOKORO_BASE_URL=http://kokoro:8880/v1` in the backend service's
environment and redeploy. (If you went the paid HF route instead, the same
image works as a second Space — Kokoro also needs the PRO-gated Docker SDK
there, so it's another $9/mo, not a free add-on.)

---

## Known risks — read before you're debugging blind

- **Cold starts — Oracle only avoids this by being a real always-on VM.**
  `restart: always` means the containers survive reboots and never sleep, so
  there's no idle-spin-down cold start at all on that path. (If you went the
  HF PRO route instead, CPU basic doesn't sleep either — you're paying to
  not have this problem, same as Oracle solves it by not being a shared
  platform in the first place.)
- **No auth, no message cap.** By design for this launch — anyone with the
  link has unlimited access. Revisit before sharing the link broadly.
- **Crisis routing still works with no LLM.** Worth knowing: the crisis
  detector and its fixed helpline response never depend on Gemini being up.
  Even in a worst-case outage, that path stays intact.
- **You are now the ops team.** Unlike Render/Vercel/HF, nothing on the
  Oracle VM auto-patches, auto-restarts on OOM, or alerts you if it goes
  down. `sudo docker compose logs -f` is your only visibility unless you set
  up something else.

---

## What Vercel/HF Space env vars map to

Full reference already lives in [`.env.example`](.env.example) — this file
only covers what changes between "works locally" and "works deployed."
`render.yaml` is kept in the repo as a fallback path back to Render if ever
needed, but isn't the current deploy target.

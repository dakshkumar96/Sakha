# Deploying Sakha

Everything that can be prepared in the repo is done: the root `Dockerfile`
(backend) and `web/` (frontend) are ready to point Hugging Face/Vercel at.
What's left requires your accounts — I can't create those or click through
dashboards for you. This is the exact order to do it in, because two of the
settings are circular (each service needs the other's URL) and doing it out
of order just means one extra redeploy, not a real problem.

**Scope of this deploy** (confirmed): Vercel + Hugging Face Spaces, free on
both, soft-launch with no auth/message limits — anyone with the link can use
it, history stays browser-local only. Phase 4 (auth, encrypted cross-device
history) isn't built yet; this is intentional for now.

> **Backend moved off Render.** Render's free tier (512MB RAM) was crash-
> looping under real use — torch + sentence-transformers kept getting the
> process killed mid-session, which showed up as random "can't reach the
> companion" errors that came and went. Hugging Face Spaces' free CPU Basic
> tier gives 16GB RAM for $0, which removes the actual cause. `render.yaml`
> is left in the repo for reference / as a fallback, but the steps below are
> the current path.

---

## 0. Push the repo

```bash
git push origin main
```

Everything after this step happens in the Vercel and Hugging Face dashboards.

---

## 1. Backend on Hugging Face Spaces

1. [huggingface.co/new-space](https://huggingface.co/new-space) → **Space
   name**: `sakha-backend` (or anything) → **SDK: Docker** → **Docker
   template: Blank** → **Hardware: CPU basic (free)** → **Visibility**: your
   choice (public is fine; the app has no secrets baked into the image).
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

Copy this URL for step 2. Note: free Spaces sleep after ~48h of no traffic
and cold-start on the next visit (same category as Render's free tier, just
a much longer idle window before it happens, and it won't crash mid-session
once it's up).

---

## 2. Frontend (`web/`) on Vercel

1. Vercel dashboard → **Add New** → **Project** → import this repo.
2. **Root Directory: set it to `web`.** This is the one setting that's easy
   to miss — without it, Vercel will try to build the whole monorepo root
   and fail.
3. Environment variable:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<your-hf-username>-sakha-backend.hf.space` (from step 1, no trailing slash) |

4. Deploy. Framework preset (Next.js) and build command are auto-detected —
   nothing else to change.

Copy the resulting Vercel URL (`https://sakha-xxxx.vercel.app` or your custom
domain if you attach one).

---

## 3. Close the loop: set CORS on the backend

Back in the HF Space → **Settings** → **Variables and secrets**:

| Key | Value |
|---|---|
| `CORS_ORIGINS` | `https://<your-vercel-url>` |

Save — the Space restarts automatically. **This step is why the browser will
show CORS errors if you test before doing it.** Until `CORS_ORIGINS` is set,
the frontend can't call the backend at all.

To push future backend changes: `git push origin main && git push hf main`
(both remotes), or just `git push hf main` if only the backend changed.

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
which the app already handles gracefully. To get real Kokoro voice, same
idea as the backend: a second free HF Space, Docker SDK, but pointing at the
public image directly instead of building from this repo — create it with
**Docker template: "From existing image"** and image
`ghcr.io/remsky/kokoro-fastapi-cpu:latest`. Once live, set
`KOKORO_BASE_URL` on the backend Space to `https://<that-space>.hf.space/v1`.
(`render.yaml` also still defines a Render version of this if you'd rather
keep it there — real-time TTS inference needs more memory than Render's free
tier reliably gives, so that one specifically was left on Render's paid
`starter` plan; free CPU Basic on HF should be worth trying first, especially
after seeing 16GB comfortably fix the backend's memory issue.)

---

## Known risks — read before you're debugging blind

- **Cold starts.** Free HF Spaces sleep after ~48 hours of no traffic; the
  first request after that can take 30–60+ seconds while it wakes. Not a
  bug — a real product would need a paid/always-on Space or a keep-alive
  ping to avoid this at 2am when it matters most.
- **No auth, no message cap.** By design for this launch — anyone with the
  link has unlimited access. Revisit before sharing the link broadly.
- **Crisis routing still works with no LLM.** Worth knowing: the crisis
  detector and its fixed helpline response never depend on Gemini being up.
  Even in a worst-case outage, that path stays intact.

---

## What Vercel/HF Space env vars map to

Full reference already lives in [`.env.example`](.env.example) — this file
only covers what changes between "works locally" and "works deployed."
`render.yaml` is kept in the repo as a fallback path back to Render if ever
needed, but isn't the current deploy target.

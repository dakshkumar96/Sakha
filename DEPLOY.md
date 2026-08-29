# Deploying Sakha

Everything that can be prepared in the repo is done: `render.yaml` (backend +
Kokoro) and the frontend are ready to point Vercel/Render at. What's left
requires your accounts — I can't create those or click through dashboards for
you. This is the exact order to do it in, because two of the settings are
circular (each service needs the other's URL) and doing it out of order just
means one extra redeploy, not a real problem.

**Scope of this deploy** (confirmed): Vercel + Render, Kokoro included,
soft-launch with no auth/message limits — anyone with the link can use it,
history stays browser-local only. Phase 4 (auth, encrypted cross-device
history) isn't built yet; this is intentional for now.

---

## 0. Push the repo

```bash
git push origin main
```

Everything after this step happens in the Vercel and Render dashboards.

---

## 1. Kokoro (voice) — deploy first, standalone

It has no dependency on anything else, so getting it running first means step
3 can point at a real URL instead of a placeholder.

1. Render dashboard → **New +** → **Blueprint**
2. Connect this GitHub repo. Render reads `render.yaml` and will offer to
   create **both** `sakha-backend` and `sakha-kokoro` — for now, only confirm
   `sakha-kokoro`. (Or create both here and just leave the backend's secrets
   unset until step 3 — either order works, this just keeps it simple.)
3. `sakha-kokoro` is on the `starter` plan in the blueprint, not free —
   real-time TTS inference is heavier than the free tier reliably handles,
   and free-tier services spin down after idle, which would mean the voice
   model reloading from scratch on every wake. **Check Render's current
   pricing for `starter` before confirming** — I can't see or commit to a
   dollar figure from here.
4. Once it's live, copy its URL (`https://sakha-kokoro-xxxx.onrender.com`).
   You'll need `<that-url>/v1` in step 3.

No environment variables needed for this service — it runs the public
`ghcr.io/remsky/kokoro-fastapi-cpu` image as-is.

---

## 2. Backend (`sakha-backend`) on Render

If you didn't create it alongside Kokoro in step 1, do it now the same way
(**New +** → **Blueprint**, same repo).

Set these in the service's **Environment** tab:

| Key | Value |
|---|---|
| `GEMINI_API_KEY` | your key from [aistudio.google.com](https://aistudio.google.com) — free tier is fine |
| `KOKORO_BASE_URL` | `https://sakha-kokoro-xxxx.onrender.com/v1` (from step 1) |
| `CORS_ORIGINS` | leave blank for now — comes back in step 4 |

Everything else (`GEMINI_MODEL`, voice names, etc.) already has a sensible
default in `render.yaml`.

**Deploy, then check `https://<your-backend>.onrender.com/health`.** You want
to see `"knowledge_loaded": true` and `"faiss_loaded": true`. If `faiss_loaded`
is `false`, the build step's `python scripts/build_faiss.py` either didn't run
or ran out of memory — see **Known risks** below.

Copy this backend's URL for step 3.

---

## 3. Frontend (`web/`) on Vercel

1. Vercel dashboard → **Add New** → **Project** → import this repo.
2. **Root Directory: set it to `web`.** This is the one setting that's easy
   to miss — without it, Vercel will try to build the whole monorepo root
   and fail.
3. Environment variable:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<your-backend>.onrender.com` (from step 2, no trailing slash) |

4. Deploy. Framework preset (Next.js) and build command are auto-detected —
   nothing else to change.

Copy the resulting Vercel URL (`https://sakha-xxxx.vercel.app` or your custom
domain if you attach one).

---

## 4. Close the loop: set CORS on the backend

Back in Render, on `sakha-backend` → **Environment**:

| Key | Value |
|---|---|
| `CORS_ORIGINS` | `https://<your-vercel-url>` |

Save — Render redeploys automatically. **This step is why the browser will
show CORS errors if you test before doing it.** Until `CORS_ORIGINS` is set,
the frontend can't call the backend at all.

---

## 5. Verify end to end

Open the Vercel URL and send one message. Check:

- A reply comes back (confirms Gemini key + CORS are both right)
- It cites a real `BG_x_y` verse if the conversation reaches a teaching turn
- Voice plays (confirms Kokoro's URL is wired correctly) — if it doesn't,
  the app falls back to browser speech automatically, so this alone won't
  break the experience, just check the browser console for what `/tts`
  returned

If something's wrong, `/health` on the backend is the fastest diagnostic —
it reports `knowledge_loaded`, `faiss_loaded`, `llm_configured`, and
`kokoro_reachable` individually.

---

## Known risks — read before you're debugging blind

- **Cold starts.** Render's free tier (the backend) sleeps after ~15 minutes
  idle; the first request after that can take 30–60+ seconds while it wakes.
  Not a bug — a real product would need a paid instance or a keep-alive ping
  to avoid this at 2am when it matters most.
- **Backend memory on the free tier.** `sentence-transformers` + `torch` are
  heavier than Render's free-tier RAM historically allows. The app is built
  to degrade gracefully if the embedding model fails to load — it falls back
  to tag-only retrieval instead of crashing — but you'll get worse verse
  matches, not an error. If `/health` shows `faiss_loaded: false`, this is
  almost certainly why; the fix is upgrading the backend's plan.
- **No auth, no message cap.** By design for this launch — anyone with the
  link has unlimited access. Revisit before sharing the link broadly.
- **Crisis routing still works with no LLM.** Worth knowing: the crisis
  detector and its fixed helpline response never depend on Gemini being up.
  Even in a worst-case outage, that path stays intact.

---

## What Vercel/Render env vars map to

Full reference already lives in [`.env.example`](.env.example) and
[`render.yaml`](render.yaml) — this file only covers what changes between
"works locally" and "works deployed."

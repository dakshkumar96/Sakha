# Deploying Sakha

Everything that can be prepared in the repo is done: the root `Dockerfile`
(backend) and `web/` (frontend) are ready to point Oracle Cloud/Vercel at.
What's left requires your accounts — I can't create those or click through
dashboards for you. This is the exact order to do it in, because two of the
settings are circular (each service needs the other's URL) and doing it out
of order just means one extra redeploy, not a real problem.

**Scope of this deploy** (confirmed): Vercel (frontend, free) + a
self-hosted backend on Oracle Cloud's Always Free tier, soft-launch with no
auth/message limits — anyone with the link can use it, history stays
browser-local only. Phase 4 (auth, encrypted cross-device history) isn't
built yet; this is intentional for now.

> **Why Oracle and not a platform-as-a-service.** Render's free tier
> (512MB RAM) crash-loops under real use — torch + sentence-transformers
> keep getting the process killed mid-session, which showed up as random
> "can't reach the companion" errors that came and went. Every platform
> that makes deploys a one-click affair — Render, Fly.io, Railway, Hugging
> Face's Docker Spaces — now gates real compute behind a paid plan. Oracle
> Cloud's Always Free tier is the one place left with real RAM (12GB) at
> genuinely $0 forever, but it's a raw VM, not a platform — this is real
> server admin, not a git push. Budget more time for this section than the
> Vercel one took.

---

## 0. Push the repo

```bash
git push origin main
```

Everything after this step happens in the Oracle Cloud and Vercel dashboards
(and one SSH session).

---

## 1. Create the Oracle Cloud account

1. [cloud.oracle.com/free](https://cloud.oracle.com/free) → sign up. It asks
   for a card for identity verification only — Always Free resources never
   charge it. Pick your **home region** carefully; you can't change it later
   and it affects Always Free capacity availability.
2. Known friction (not something I can work around): Oracle's signup
   sometimes fails identity verification for no clear reason, or a region
   reports "out of capacity" for the free ARM shape. If either happens,
   trying a different home region on a fresh signup is the usual fix — no
   real solution beyond retrying.

---

## 2. Create the VM

Console → **Compute** → **Instances** → **Create instance**.

| Setting | Value |
|---|---|
| Image | Canonical Ubuntu, **24.04**, **aarch64** (ARM) build |
| Shape | **VM.Standard.A1.Flex** (Ampere/ARM — this is the Always Free shape) |
| OCPUs / Memory | Max the slider allows for free (currently 2 OCPU / 12GB) |
| SSH keys | Let Oracle generate a key pair and download the private key, or paste your own public key |
| Networking | Leave default VCN/subnet, keep "Assign a public IPv4 address" checked |

Create it, then note the **public IP** shown on the instance's detail page.

---

## 3. Point a free subdomain at the VM (for HTTPS)

Caddy (step 5) needs a real domain name to get a Let's Encrypt certificate —
a bare IP can't get one. [duckdns.org](https://www.duckdns.org) gives a free
subdomain for exactly this:

1. Sign in with GitHub/Google (no cost).
2. Create a subdomain, e.g. `sakha-backend` → `sakha-backend.duckdns.org`.
3. Paste the VM's public IP from step 2 into the "current ip" field, save.

---

## 4. Open the firewall — two layers, both need a rule

Oracle blocks inbound traffic at **two** independent layers; missing either
one means "site can't be reached" with no obvious error.

**a) Cloud layer** — Console → your instance → **Subnet** link → **Security
Lists** → default security list → **Add Ingress Rules**:

| Source CIDR | Protocol | Port |
|---|---|---|
| `0.0.0.0/0` | TCP | 80 |
| `0.0.0.0/0` | TCP | 443 |

**b) OS layer** — Oracle's Ubuntu images also ship with `iptables` rules
that block these ports even when the Security List allows them. SSH in
(`ssh -i <your-key> ubuntu@<public-ip>`) and run:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || sudo apt-get install -y iptables-persistent
```

(If the image uses `ufw` instead, `sudo ufw allow 80,443/tcp` is the
equivalent — check `sudo ufw status` first; don't run both.)

---

## 5. Install Docker and run the backend

Still SSH'd into the VM:

```bash
curl -fsSL https://get.docker.com | sudo sh

git clone https://github.com/dakshkumar96/Sakha.git
cd Sakha/deploy/oracle
cp .env.example .env
nano .env   # fill in GEMINI_API_KEY, CORS_ORIGINS (comes back in step 7), DOMAIN

sudo docker compose up -d --build
```

The first build takes a few minutes — installs torch/faiss/sentence-
transformers, builds the FAISS index (same steps `Dockerfile` always ran).
Watch it with:

```bash
sudo docker compose logs -f backend
```

Caddy requests the Let's Encrypt cert automatically on first request to
`$DOMAIN` — no separate step needed.

**Once it's live, check `https://<your-domain>/health`** (from your own
machine, not the VM). You want `"knowledge_loaded": true` and
`"faiss_loaded": true` — with 12GB of headroom this should never come back
`false` from memory pressure the way it did on Render.

Copy this URL for step 6.

---

## 6. Frontend (`web/`) on Vercel

1. Vercel dashboard → **Add New** → **Project** → import this repo.
2. **Root Directory: set it to `web`.** This is the one setting that's easy
   to miss — without it, Vercel will try to build the whole monorepo root
   and fail.
3. Environment variable:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<your-domain>` (from step 5, no trailing slash) |

4. Deploy. Framework preset (Next.js) and build command are auto-detected —
   nothing else to change.

Copy the resulting Vercel URL (`https://sakha-xxxx.vercel.app` or your custom
domain if you attach one).

---

## 7. Close the loop: set CORS on the backend

Edit `CORS_ORIGINS` in `deploy/oracle/.env` on the VM to
`https://<your-vercel-url>`, then:

```bash
cd ~/Sakha/deploy/oracle
sudo docker compose up -d --build
```

**This step is why the browser will show CORS errors if you test before
doing it.** Until `CORS_ORIGINS` is set, the frontend can't call the backend
at all.

To push future backend changes: `git pull` on the VM, then
`sudo docker compose up -d --build` from `deploy/oracle/`.

---

## 8. Verify end to end

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
more memory/CPU than the backend alone, but 12GB is enough headroom for
both — add a third service to `deploy/oracle/docker-compose.yml`:

```yaml
  kokoro:
    image: ghcr.io/remsky/kokoro-fastapi-cpu:latest
    restart: always
    expose:
      - "8880"
```

then set `KOKORO_BASE_URL=http://kokoro:8880/v1` in the backend service's
environment and redeploy.

---

## Known risks — read before you're debugging blind

- **Cold starts.** None, by design: `restart: always` means both containers
  survive VM reboots and never sleep — there's no idle-spin-down cold start
  at all, unlike every free platform tier we tried before this.
- **No auth, no message cap.** By design for this launch — anyone with the
  link has unlimited access. Revisit before sharing the link broadly.
- **Crisis routing still works with no LLM.** Worth knowing: the crisis
  detector and its fixed helpline response never depend on Gemini being up.
  Even in a worst-case outage, that path stays intact.
- **You are now the ops team.** Unlike a managed platform, nothing on the
  Oracle VM auto-patches, auto-restarts on OOM, or alerts you if it goes
  down. `sudo docker compose logs -f` is your only visibility unless you set
  up something else.
- **The VM's public IP can change** if the instance is ever stopped and
  restarted (not just rebooted) unless you attach a **Reserved Public IP**
  (Networking → Reserved IPs — free, one per Always Free account, worth
  doing once so DuckDNS never goes stale). Nothing here auto-updates DuckDNS
  if the IP does change — re-paste the new IP into the DuckDNS dashboard if
  that ever happens.

---

## What Vercel/backend env vars map to

Full reference already lives in [`.env.example`](.env.example) and
[`deploy/oracle/.env.example`](deploy/oracle/.env.example) — this file only
covers what changes between "works locally" and "works deployed."

# Deploying the backend to Oracle Cloud (genuinely free)

Why this exists: Render's free tier crash-loops under real use (512MB RAM vs.
what torch + sentence-transformers actually need), and every platform that
makes deploys a one-click affair — Render, Fly.io, Railway, Hugging Face
Docker Spaces — now gates real compute behind a paid plan. Oracle Cloud's
**Always Free** tier is the one place left with real RAM (12GB) at genuinely
$0 forever, but it's a raw VM, not a platform — this is real server admin,
not a git push. Budget more time for this than Render/Vercel took.

**What you'll end up with:** an Ubuntu VM running the backend in Docker
behind Caddy, which gets free HTTPS automatically. Everything after VM
creation is one `docker compose up -d` — I've written the compose file and
reverse-proxy config already ([deploy/oracle/](deploy/oracle/)).

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

## 5. Install Docker and run it

Still SSH'd into the VM:

```bash
curl -fsSL https://get.docker.com | sudo sh

git clone https://github.com/dakshkumar96/Sakha.git
cd Sakha/deploy/oracle
cp .env.example .env
nano .env   # fill in GEMINI_API_KEY, CORS_ORIGINS (your Vercel URL), DOMAIN

sudo docker compose up -d --build
```

The first build takes a few minutes (same steps as the HF Spaces image —
installs torch/faiss/sentence-transformers, builds the FAISS index). Watch
it with:

```bash
sudo docker compose logs -f backend
```

Caddy requests the Let's Encrypt cert automatically on first request to
`$DOMAIN` — no separate step needed.

---

## 6. Verify

From your own machine (not the VM):

```bash
curl https://sakha-backend.duckdns.org/health
```

Expect `"knowledge_loaded": true` and `"faiss_loaded": true`.

Then, same as the Render/HF runbooks: set `NEXT_PUBLIC_API_URL` on Vercel to
`https://sakha-backend.duckdns.org` and redeploy the frontend.

---

## Keeping it running

- **Reboots:** `restart: always` in `docker-compose.yml` means both
  containers come back up automatically if the VM restarts.
- **Updates:** `cd ~/Sakha && git pull && cd deploy/oracle && sudo docker
  compose up -d --build` redeploys the latest code.
- **The VM's public IP can change** if the instance is ever stopped and
  restarted (not just rebooted) unless you attach a **Reserved Public IP**
  (Networking → Reserved IPs — free, one per Always Free account, worth
  doing once so DuckDNS never goes stale).
- Nothing here auto-updates DuckDNS if the IP does change — re-paste the new
  IP into the DuckDNS dashboard if that ever happens.

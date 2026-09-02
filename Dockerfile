# Backend image for Hugging Face Spaces (Docker SDK).
#
# Free CPU Basic hardware gives 16GB RAM / 2 vCPU — the actual fix for the
# OOM crash-loop we hit on Render's free tier (512MB), where torch +
# sentence-transformers kept getting the process killed mid-session.
#
# Build context is the repo root (matches render.yaml's buildCommand, which
# also runs `pip install -r backend/requirements.txt && python
# scripts/build_faiss.py` from root) — only backend/, prompts/, and the
# derived knowledge/ subfolders the app actually reads at runtime are
# copied in. web/ and the Phase 1 source material never enter the image.
#
# Follows HF's documented non-root pattern: Spaces containers run under a
# restricted user, so home/cache dirs must belong to uid 1000 from the start.
FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --user -r backend/requirements.txt

COPY --chown=user backend/ backend/
COPY --chown=user prompts/ prompts/
COPY --chown=user scripts/build_faiss.py scripts/build_faiss.py
COPY --chown=user knowledge/gita/ knowledge/gita/
COPY --chown=user knowledge/chunks/ knowledge/chunks/
COPY --chown=user knowledge/taxonomy/ knowledge/taxonomy/
COPY --chown=user knowledge/validation/ knowledge/validation/

# Builds knowledge/indices/{faiss.index,id_map.json} — gitignored (like on
# Render), regenerated fresh at image-build time from the chunks above.
RUN python scripts/build_faiss.py

# HF Docker Spaces expect the app on 7860 by default (see README.md frontmatter).
EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]

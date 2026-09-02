# Backend image — built and run on the Oracle Cloud Always Free VM via
# deploy/oracle/docker-compose.yml. Real RAM (12GB on that VM) is what
# actually fixes the OOM crash-loop this app used to hit on 512MB-tier free
# hosting, where torch + sentence-transformers kept getting the process
# killed mid-session.
#
# Build context is the repo root — only backend/, prompts/, and the derived
# knowledge/ subfolders the app actually reads at runtime are copied in.
# web/ and the Phase 1 source material never enter the image.
#
# Runs as a non-root user (uid 1000) as a matter of basic container
# hygiene, not because the host requires it.
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

# Builds knowledge/indices/{faiss.index,id_map.json} — gitignored,
# regenerated fresh at image-build time from the chunks above.
RUN python scripts/build_faiss.py

EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]

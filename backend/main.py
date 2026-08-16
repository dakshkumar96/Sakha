"""Krishna AI backend entrypoint (Phase 2 runtime core).

Run:
    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

import logging
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat import router as chat_router
from backend.api.tts import router as tts_router
from backend.config import get_settings
from backend.conversation.emotion_response_store import EmotionResponseStore
from backend.conversation.fewshot_store import FewshotStore
from backend.conversation.pipeline import ConversationPipeline
from backend.conversation.prompt_loader import load_system_prompt
from backend.conversation.response_generator import ResponseGenerator
from backend.memory.session_store import SessionStore
from backend.rag.citation_filter import load_allowlist
from backend.rag.embedder import Embedder
from backend.rag.retriever import Retriever
from backend.rag.taxonomy_store import TaxonomyStore
from backend.rag.verse_store import VerseStore
from backend.voice.kokoro_client import KokoroClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("krishna.main")

app = FastAPI(title="Krishna AI — Runtime Core", version="0.2.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    verse_store = VerseStore(settings.verses_path, settings.anchor_ids_path)
    taxonomy_store = TaxonomyStore(
        settings.emotions_path,
        settings.situations_path,
        settings.emotion_to_verses_path,
        settings.crisis_forbidden_path,
    )
    allowlist = load_allowlist(settings.allowlist_path)
    embedder = Embedder(settings.embedding_model)
    retriever = Retriever(
        verse_store=verse_store,
        taxonomy_store=taxonomy_store,
        embedder=embedder,
        faiss_index_path=settings.faiss_index_path,
        faiss_id_map_path=settings.faiss_id_map_path,
        top_k=settings.faiss_top_k,
    )
    # Warm the embedding model in the background. Loading it lazily stalled
    # the first teaching turn by several seconds — the worst possible moment
    # to make someone wait — but warming it inline would block startup and
    # /health along with it. A daemon thread gets both.
    if retriever.faiss_loaded:
        def _warm() -> None:
            try:
                embedder.encode(["warmup"])
                logger.info("Embedding model warm")
            except Exception:  # noqa: BLE001 - warmup is best-effort
                logger.exception("Embedder warmup failed; retrieval will load on demand")

        threading.Thread(target=_warm, name="embedder-warmup", daemon=True).start()

    system_prompt = load_system_prompt(
        constitution_path=settings.system_prompt_path,
        language_path=settings.krishna_language_path,
        analysis_path=settings.krishna_analysis_path,
    )
    fewshot_store = FewshotStore(settings.fewshot_path)
    emotion_store = EmotionResponseStore(settings.emotion_response_path)
    fallbacks = [
        m.strip()
        for m in (settings.gemini_fallback_models or "").split(",")
        if m.strip()
    ]
    generator = ResponseGenerator(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        system_prompt=system_prompt,
        fewshot_store=fewshot_store,
        emotion_store=emotion_store,
        fallback_models=fallbacks or None,
    )
    session_store = SessionStore(
        persist_dir=settings.session_persist_dir
        if settings.persist_sessions_locally
        else None
    )

    pipeline = ConversationPipeline(
        verse_store=verse_store,
        taxonomy_store=taxonomy_store,
        retriever=retriever,
        session_store=session_store,
        generator=generator,
        allowlist=allowlist,
        teach_gate_min_questions=settings.teach_gate_min_questions,
        max_verses_per_turn=settings.max_verses_per_turn,
        enable_knot_summarizer=settings.enable_knot_summarizer,
        enable_soft_classifier=settings.enable_soft_classifier,
        enable_deepen_pass=settings.enable_deepen_pass,
        soft_classifier_threshold=settings.soft_classifier_threshold,
        emotion_store=emotion_store,
    )

    kokoro = KokoroClient(
        base_url=settings.kokoro_base_url,
        api_key=settings.kokoro_api_key,
        voice_en=settings.kokoro_voice_en,
        voice_hi=settings.kokoro_voice_hi,
        speed=settings.kokoro_speed,
    )

    app.state.verse_store = verse_store
    app.state.taxonomy_store = taxonomy_store
    app.state.retriever = retriever
    app.state.generator = generator
    app.state.pipeline = pipeline
    app.state.kokoro = kokoro

    logger.info(
        "Krishna AI backend ready: %d verses, faiss=%s, gemini=%s model=%s, "
        "emotion_cards=%d, fewshots=%d",
        verse_store.count,
        retriever.faiss_loaded,
        generator.available,
        settings.gemini_model,
        len(emotion_store.ids()),
        len(fewshot_store.examples),
    )


@app.get("/health")
async def health() -> dict:
    verse_store: VerseStore | None = getattr(app.state, "verse_store", None)
    retriever: Retriever | None = getattr(app.state, "retriever", None)
    generator: ResponseGenerator | None = getattr(app.state, "generator", None)
    kokoro: KokoroClient | None = getattr(app.state, "kokoro", None)
    llm_ok = bool(generator) and generator.available
    return {
        "status": "ok" if verse_store else "starting",
        "knowledge_loaded": bool(verse_store) and verse_store.count > 0,
        "verse_count": verse_store.count if verse_store else 0,
        "faiss_loaded": bool(retriever) and retriever.faiss_loaded,
        "llm_provider": "gemini",
        "llm_configured": llm_ok,
        # legacy alias for older frontend types
        "groq_configured": llm_ok,
        "kokoro_reachable": bool(kokoro) and await kokoro.reachable(),
    }


app.include_router(chat_router)
app.include_router(tts_router)

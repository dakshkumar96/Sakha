"""Backend configuration.

Loads .env from the repo root (one level above backend/) and exposes
paths into the Phase 1 knowledge tree. backend/ never duplicates
knowledge — it only reads it.
"""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
PROMPTS_DIR = ROOT_DIR / "prompts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM (Gemini) ---
    # Prefer GEMINI_API_KEY. GROQ_* left only so old .env lines do not crash load.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    #: Comma-separated fallbacks tried on 429. Separate free-tier quotas per family.
    gemini_fallback_models: str = (
        "gemini-flash-lite-latest,gemini-2.0-flash-lite,"
        "gemini-flash-latest,gemini-2.0-flash"
    )
    groq_api_key: str = ""  # unused; ignored at runtime
    groq_model: str = ""

    # --- App ---
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001"
    )
    next_public_api_url: str = "http://localhost:8000"

    # --- Public API limits (per visitor address; 0 turns a rate limit off) ---
    chat_rate_per_minute: int = 10
    tts_rate_per_minute: int = 20
    #: IPv6 visitors are counted per network of this size, not per address.
    #: 56 is what most home connections are given.
    ipv6_rate_limit_prefix: int = 56
    #: Most model calls the whole site may make in one UTC day, across all
    #: visitors. Kept under the free tier's daily allowance (500 to 1,500 a day
    #: per Flash-Lite model in 2026, check AI Studio for yours) so the quota is
    #: never what runs out. One chat turn is usually 1 to 5 calls. 0 turns it off.
    gemini_daily_call_cap: int = 400
    #: Longest message /chat accepts, in characters. A long spoken thought is
    #: about 1,000 characters.
    max_message_chars: int = 2000
    #: Longest text /tts accepts. The longest reply is about 3,500 tokens.
    max_tts_chars: int = 6000
    #: Most messages, and longest single message, in the history /chat accepts.
    max_history_items: int = 60
    max_history_item_chars: int = 6000

    # --- Crisis ---
    #: Longest a crisis level 1 or 2 reply may take before the fixed helpline
    #: text is sent instead. Covers every model call on that path.
    crisis_reply_timeout_seconds: float = 25.0

    # --- Retrieval ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    faiss_top_k: int = 8
    max_verses_per_turn: int = 2

    # --- Persona / gates ---
    teach_gate_min_questions: int = 2

    # --- Phase 6 depth knobs ---
    #: Second LLM pass on teach turns (extra latency). Default off for Gemini speed.
    enable_deepen_pass: bool = False
    #: Structured "what is actually stuck" read between engines and planner.
    enable_knot_summarizer: bool = True
    #: Ask the LLM for emotion/intent only when lexicon returns no primary.
    enable_soft_classifier: bool = True
    #: Lexicon confidence below this triggers the soft classifier (if no primary).
    soft_classifier_threshold: float = 0.45    #: Local plaintext session dump for dev across restarts. NOT Phase 4 storage.
    persist_sessions_locally: bool = False

    # --- Kokoro TTS (Phase 3) ---
    # Browser never talks to Kokoro directly; it goes through POST /tts.
    kokoro_base_url: str = "http://localhost:8880/v1"
    kokoro_api_key: str = "not-needed"
    kokoro_voice_en: str = "am_michael"
    kokoro_voice_hi: str = "hf_alpha"
    kokoro_speed: float = 0.9

    # --- Paths (Phase 1 knowledge, read-only) ---
    verses_path: Path = KNOWLEDGE_DIR / "gita" / "verses.json"
    anchor_ids_path: Path = KNOWLEDGE_DIR / "gita" / "anchor_verse_ids.json"
    emotions_path: Path = KNOWLEDGE_DIR / "taxonomy" / "emotions_v1.json"
    situations_path: Path = KNOWLEDGE_DIR / "taxonomy" / "situations_v1.json"
    emotion_to_verses_path: Path = KNOWLEDGE_DIR / "taxonomy" / "emotion_to_verses.json"
    crisis_forbidden_path: Path = KNOWLEDGE_DIR / "taxonomy" / "crisis_forbidden.json"
    verse_chunks_path: Path = KNOWLEDGE_DIR / "chunks" / "gita_verse_chunks.jsonl"
    allowlist_path: Path = KNOWLEDGE_DIR / "validation" / "citation_allowlist.txt"
    system_prompt_path: Path = PROMPTS_DIR / "system_v1.txt"
    krishna_language_path: Path = PROMPTS_DIR / "krishna_language.md"
    krishna_analysis_path: Path = PROMPTS_DIR / "krishna_analysis.md"
    fewshot_path: Path = PROMPTS_DIR / "fewshot_v5.json"
    emotion_response_path: Path = PROMPTS_DIR / "emotion_response.json"
    faiss_index_path: Path = KNOWLEDGE_DIR / "indices" / "faiss.index"
    faiss_id_map_path: Path = KNOWLEDGE_DIR / "indices" / "id_map.json"
    session_persist_dir: Path = ROOT_DIR / "tmp" / "sessions"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

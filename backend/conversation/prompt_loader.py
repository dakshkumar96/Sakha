"""Compose the full system prompt: constitution + language bible + analysis.

The three prompts/ files stay editable sources of truth. The runtime concatenates
them once at startup so Gemini always receives the voice documents without a
second filesystem pass mid-turn.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("krishna.prompt_loader")

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

_CONSTITUTION = "system_v1.txt"
_LANGUAGE = "krishna_language.md"
_ANALYSIS = "krishna_analysis.md"


def _read(path: Path) -> str:
    if not path.exists():
        logger.warning("Prompt file missing: %s", path)
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_system_prompt(
    constitution_path: Path | None = None,
    language_path: Path | None = None,
    analysis_path: Path | None = None,
) -> str:
    """Return the full system message for ResponseGenerator.

    Order: constitution (law) → language bible (lexicon/registers) →
    analysis (craft). Clear banners so the model can locate sections.
    """
    constitution = _read(constitution_path or PROMPTS_DIR / _CONSTITUTION)
    language = _read(language_path or PROMPTS_DIR / _LANGUAGE)
    analysis = _read(analysis_path or PROMPTS_DIR / _ANALYSIS)

    if not constitution:
        raise FileNotFoundError(
            f"Required constitution missing: {constitution_path or PROMPTS_DIR / _CONSTITUTION}"
        )

    parts = [constitution]

    if language:
        parts.append(
            "\n\n"
            "══════════════════════════════════════════════════════════════\n"
            "LANGUAGE BIBLE — exact words, registers, address triggers, validation\n"
            "Source: prompts/krishna_language.md\n"
            "══════════════════════════════════════════════════════════════\n\n"
            f"{language}"
        )
    else:
        logger.warning("krishna_language.md not loaded — voice will be thinner")

    if analysis:
        parts.append(
            "\n\n"
            "══════════════════════════════════════════════════════════════\n"
            "SPEECH PATTERN ANALYSIS — craft, mirrors, questions, metaphors\n"
            "Source: prompts/krishna_analysis.md\n"
            "══════════════════════════════════════════════════════════════\n\n"
            f"{analysis}"
        )
    else:
        logger.warning("krishna_analysis.md not loaded — craft patterns thinner")

    parts.append(
        "\n\n"
        "══════════════════════════════════════════════════════════════\n"
        "END OF ATTACHMENTS — obey constitution §III over style if conflict.\n"
        "══════════════════════════════════════════════════════════════\n"
    )

    full = "\n".join(parts)
    logger.info(
        "System prompt composed: %d chars (constitution + language=%s + analysis=%s)",
        len(full),
        bool(language),
        bool(analysis),
    )
    return full


# Map planner turn_action → register hint for the per-turn wrapper.
REGISTER_FOR_ACTION: dict[str, str] = {
    "question": "DIAGNOSTIC",
    "witness": "DIAGNOSTIC or WARM if pure grief/exhaustion (no verse)",
    "validate": "Acknowledge; REBUKING only if clear self-deception, else pivot to TEACHING when allowed",
    "teach": "TEACHING (primary). Brief WARM only after the hard point if pain is acute.",
    "teach_warm": "WARM-weighted TEACHING — they have deepened disclosure this session. Specific stakes first; soft hard-truth; quiet citation.",
    "crisis_soft": "WARM + one real diagnostic check-in. No verse. No rebuke.",
    "crisis": "Safety routing only — no persona performance.",
}


def register_hint(turn_action: str) -> str:
    return REGISTER_FOR_ACTION.get(
        turn_action,
        "Choose one register from the LANGUAGE BIBLE that matches stage.",
    )

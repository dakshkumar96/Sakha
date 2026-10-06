"""Language detection for mirroring and few-shot selection.

Two reply languages, each kept to one language per reply:
  "hi" — Devanagari Hindi
  "en" — English

Users may still type Hindi in Roman letters. The reply is then in English,
or in Hindi if they chose Hindi.
"""

from __future__ import annotations

import re

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def detect_language(text: str) -> str:
    """Returns "hi" for mostly Devanagari text, otherwise "en"."""
    return "hi" if is_mostly_devanagari(text) else "en"


def is_mostly_devanagari(text: str, threshold: float = 0.3) -> bool:
    """True when alphabetic characters are mostly Devanagari."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    deva = sum(1 for c in letters if _DEVANAGARI.match(c))
    return (deva / len(letters)) > threshold


def mirror_instruction(lang: str) -> str:
    """One line telling the model which language to answer in."""
    if lang == "hi":
        return (
            "Reply in Hindi (Devanagari). The user chose Hindi as the spoken language. "
            "Do not answer in English. Do not answer in Roman/Latin script."
        )
    return (
        "Reply in English. The user chose English as the spoken language. "
        "Do not answer in Hindi/Devanagari, and do not mix Hindi words into English sentences."
    )


def resolve_reply_lang(message: str, preferred: str | None) -> str:
    """The UI speech preference wins; otherwise detect it from the message."""
    if preferred in ("en", "hi"):
        return preferred
    return detect_language(message)

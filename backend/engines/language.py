"""Language detection for mirroring and few-shot selection.

Three outcomes matter to the product:
  "hi"       — Devanagari Hindi
  "hinglish" — roman-script Hindi / code-switch (auto-detect only)
  "en"       — English

UI "Hinglish" preference resolves to "hi" for generation (Hindi voice);
captions/chat use code-switching Hinglish via text_en (roman_hinglish_ui).
"""

from __future__ import annotations

import re

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")

# High-signal roman Hindi function words. Deliberately common words rather
# than emotional vocabulary, so detection doesn't hinge on the topic.
_HINGLISH_MARKERS = {
    "main", "mai", "mera", "meri", "mujhe", "mujhko", "hoon", "hun", "hu",
    "hai", "hain", "tha", "thi", "nahi", "nahin", "nai", "kya", "kyun",
    "kyu", "kaise", "karna", "karta", "karti", "karun", "raha", "rahi",
    "rahe", "koi", "kuch", "sab", "bahut", "bohot", "aur", "lekin", "par",
    "yaar", "bhi", "ko", "se", "ka", "ke", "ki", "log", "ghar", "aaj",
    "abhi", "phir", "matlab", "chahiye", "chahta", "chahti", "gaya", "gayi",
    "hota", "hoti", "jata", "jati", "apne", "unko", "usko", "bata", "batao",
}

_WORD = re.compile(r"[a-z]+")


def detect_language(text: str) -> str:
    """Returns "hi" | "hinglish" | "en"."""
    letters = [c for c in text if c.isalpha()]
    if letters:
        deva = sum(1 for c in letters if _DEVANAGARI.match(c))
        if deva / len(letters) > 0.3:
            return "hi"

    words = _WORD.findall(text.casefold())
    if not words:
        return "en"

    hits = sum(1 for w in words if w in _HINGLISH_MARKERS)
    # Two markers, or a fifth of a short message, reads as Hinglish.
    if hits >= 2 or (hits >= 1 and hits / len(words) >= 0.2):
        return "hinglish"
    return "en"


def is_mostly_devanagari(text: str, threshold: float = 0.3) -> bool:
    """True when alphabetic characters are mostly Devanagari."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    deva = sum(1 for c in letters if _DEVANAGARI.match(c))
    return (deva / len(letters)) > threshold


def mirror_instruction(lang: str) -> str:
    """One line telling the model which register to answer in."""
    if lang == "hi":
        return (
            "Reply in Hindi (Devanagari). The user chose Hindi as the spoken language. "
            "Do not answer in English. Do not answer in Roman/Latin script."
        )
    if lang == "hinglish":
        return (
            "Reply in code-switching Hinglish — mix Roman Hindi and English in the "
            "same sentence (like 'I'm thoda busy right now', 'Scene kya hai?'). "
            "Do NOT switch them to pure formal English or to Devanagari."
        )
    return (
        "Reply in English. The user chose English as the spoken language. "
        "Do not answer in Hindi/Devanagari."
    )


def resolve_reply_lang(message: str, preferred: str | None) -> str:
    """UI speech preference wins; otherwise auto-detect from the message.

    UI "hinglish" means Hindi voice + code-switch Hinglish on-screen
    (roman_hinglish_ui), so generation uses Devanagari Hindi ("hi") —
    the same spoken path as UI "hi". Auto-detected Roman Hinglish still
    returns "hinglish" for Roman replies.
    """
    if preferred == "hinglish":
        return "hi"
    if preferred in ("en", "hi"):
        return preferred
    return detect_language(message)

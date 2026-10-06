"""Every reply is in one language: English or Devanagari Hindi. Hinglish mode is gone."""
from __future__ import annotations

import json
import re
from pathlib import Path

from backend.conversation.schemas import ChatRequest
from backend.engines.language import mirror_instruction, resolve_reply_lang

ROOT = Path(__file__).resolve().parents[1]
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
ROMAN_HINDI = re.compile(r"\b(hai|nahi|kya|mujhe|tum|tumhara|yaar|kuch|bhi|aur|raha|hoon|toh|matlab)\b", re.I)


def test_a_saved_hinglish_setting_is_treated_as_hindi():
    request = ChatRequest(message="hello", session_id="s1", reply_lang="hinglish")
    assert request.reply_lang == "hi"


def test_the_chosen_language_wins_and_roman_hindi_never_gets_a_mixed_reply():
    assert resolve_reply_lang("main bahut pareshan hoon yaar", "en") == "en"
    assert resolve_reply_lang("main bahut pareshan hoon yaar", "hi") == "hi"
    assert resolve_reply_lang("main bahut pareshan hoon yaar", None) == "en"
    assert resolve_reply_lang("मैं बहुत परेशान हूं", None) == "hi"
    assert "mix" in mirror_instruction("en").lower()


def test_no_few_shot_reply_or_turn_mixes_languages():
    examples = json.loads((ROOT / "prompts/fewshot_v5.json").read_text(encoding="utf-8"))["examples"]
    assert len(examples) == 100
    for ex in examples:
        assert ex["metadata"]["language"] in ("en", "hi", "mixed_en_query_hi_response")
        texts = [m["content"] for m in ex["messages"]] + [ex["krishna_response"]]
        for text in texts:
            if DEVANAGARI.search(text):
                assert not re.search(r"[A-Za-z]{4,}", re.sub(r"Bhagavad Gita|BG_\d+_\d+", "", text)), (ex["id"], text)
            else:
                assert len(set(ROMAN_HINDI.findall(text.lower()))) < 2, (ex["id"], text)


def test_the_prompts_no_longer_ask_for_hinglish():
    for name in ("system_v1.txt", "krishna_language.md", "fewshot_v5.json"):
        text = (ROOT / "prompts" / name).read_text(encoding="utf-8").lower()
        assert "hinglish" not in text, name
        assert "code-switching" not in text, name

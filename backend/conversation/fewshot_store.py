"""Few-shot exemplars from prompts/fewshot_v5.json (batch schema).

Schema (batch 1+):
  {
    "examples": [
      {
        "id": "fs_001",
        "messages": [{"role":"user","content":"..."}, ...],
        "krishna_response": "...",
        "metadata": {
          "emotion_primary": "...",
          "language": "en|hi|hinglish",
          "register": "diagnostic|teaching|warm|rebuking|...",
          "conversation_stage": "turn_1|...",
          "verse_used": "BG_2_47"|null
        }
      }
    ]
  }

Legacy schema (still supported): { "exemplars": [{ "id", "lang", "text" }] }
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger("krishna.fewshot")

_DEFAULT = Path(__file__).resolve().parents[2] / "prompts" / "fewshot_v5.json"

# Planner turn_action → preferred fewshot registers (ordered).
_REGISTER_PREFS: dict[str, list[str]] = {
    "question": ["diagnostic", "diagnostic_soft", "rebuking"],
    "witness": ["warm", "warm_with_boundary", "diagnostic", "diagnostic_soft"],
    "validate": ["validate_and_redirect", "rebuking", "diagnostic", "warm_with_boundary", "teaching"],
    "teach": ["teaching", "rebuking"],
    "teach_warm": ["warm", "teaching", "warm_with_boundary"],
    "crisis_soft": ["warm", "warm_with_boundary"],
    "crisis": [],  # never fewshot crisis into LLM generation
    # Special registers from fewshot metadata → similar planner actions
    "identity": ["identity_refusal", "validate_and_redirect", "warm"],
    "identity_refusal": ["identity_refusal", "validate_and_redirect"],
    "validate_and_redirect": ["validate_and_redirect", "warm_with_boundary", "diagnostic"],
    "rebuking": ["rebuking", "diagnostic", "teaching"],
    "warm_with_boundary": ["warm_with_boundary", "warm", "validate_and_redirect"],
    "diagnostic_soft": ["diagnostic_soft", "diagnostic", "warm"],
}


def _norm_lang(lang: str | None) -> str:
    if not lang:
        return "en"
    if lang in ("hi", "hinglish"):
        return lang
    return "en"


def _id_sort_key(eid: str) -> tuple[int, str]:
    """fs_001 → (1, 'fs_001') for numeric order with stable fallback."""
    try:
        parts = str(eid).split("_")
        return (int(parts[-1]), str(eid))
    except (ValueError, IndexError):
        return (10**9, str(eid))


def _extract_examples(doc: Any) -> list[dict[str, Any]]:
    """Normalize one decoded JSON value into the batch-schema example list."""
    if not isinstance(doc, dict):
        return []
    if "examples" in doc:
        return list(doc.get("examples") or [])
    # Legacy
    legacy: list[dict[str, Any]] = []
    for ex in doc.get("exemplars") or []:
        legacy.append(
            {
                "id": ex.get("id"),
                "messages": [],
                "krishna_response": ex.get("text", ""),
                "metadata": {
                    "language": ex.get("lang", "en"),
                    "register": "teaching",
                    "emotion_primary": None,
                    "_legacy": True,
                },
            }
        )
    return legacy


def _decode_all_json_docs(text: str) -> list[Any]:
    """Decode one or more adjacent JSON values (batch paste / multi-doc files)."""
    decoder = json.JSONDecoder()
    docs: list[Any] = []
    idx = 0
    n = len(text)
    while idx < n:
        while idx < n and text[idx].isspace():
            idx += 1
        if idx >= n:
            break
        obj, end = decoder.raw_decode(text, idx)
        docs.append(obj)
        idx = end
    return docs


def _load_examples(path_str: str, mtime_ns: int = 0) -> list[dict[str, Any]]:
    """Load fewshots; mtime_ns is only for cache busting when the file changes."""
    del mtime_ns  # used solely as lru_cache key component
    path = Path(path_str)
    if not path.exists():
        logger.warning("Fewshot file missing: %s", path)
        return []
    text = path.read_text(encoding="utf-8")
    try:
        docs = _decode_all_json_docs(text)
    except json.JSONDecodeError as exc:
        logger.warning("Fewshot file invalid JSON: %s (%s)", path, exc)
        return []

    by_id: dict[str, dict[str, Any]] = {}
    legacy_no_id: list[dict[str, Any]] = []
    for doc in docs:
        for ex in _extract_examples(doc):
            eid = ex.get("id")
            if eid:
                by_id[str(eid)] = ex  # later docs win on id collision
            else:
                legacy_no_id.append(ex)

    examples = [by_id[i] for i in sorted(by_id.keys(), key=_id_sort_key)]
    if legacy_no_id:
        examples.extend(legacy_no_id)

    schema = "batch" if any(isinstance(d, dict) and "examples" in d for d in docs) else "legacy"
    logger.info(
        "Fewshot store: %d examples (%s, %d json value(s)) from %s",
        len(examples),
        schema,
        len(docs),
        path,
    )
    return examples


@lru_cache(maxsize=8)
def _load_examples_cached(path_str: str, mtime_ns: int) -> list[dict[str, Any]]:
    return _load_examples(path_str, mtime_ns)


class FewshotStore:
    def __init__(self, path: Path | None = None):
        self.path = path or _DEFAULT
        mtime_ns = 0
        try:
            mtime_ns = self.path.stat().st_mtime_ns
        except OSError:
            pass
        self.examples = _load_examples_cached(str(self.path), mtime_ns)

    def format_example(self, ex: dict[str, Any]) -> str:
        """Render one example as a short dialogue for the model."""
        meta = ex.get("metadata") or {}
        head = (
            f"[EXEMPLAR id={ex.get('id')} emotion={meta.get('emotion_primary')} "
            f"register={meta.get('register')} lang={meta.get('language')} — "
            f"imitate DEPTH and RHYTHM, never copy wording or situation]\n"
        )
        lines: list[str] = []
        for m in ex.get("messages") or []:
            role = m.get("role", "user")
            label = "User" if role == "user" else "Companion"
            lines.append(f"{label}: {m.get('content', '')}")
        reply = ex.get("krishna_response") or ""
        if reply:
            # Gold replies use // as beat separators in batch 1 — keep as line breaks for readability.
            soft = reply.replace(" // ", "\n")
            lines.append(f"Companion: {soft}")
        if meta.get("_legacy") and not lines:
            return head + (ex.get("krishna_response") or "")
        return head + "\n".join(lines)

    def pick(
        self,
        *,
        emotion_id: str | None,
        lang: str = "en",
        turn_action: str = "question",
        max_examples: int = 2,
        extra_hints: list[str] | None = None,
    ) -> str | None:
        """Select 1–2 best matching exemplars. Crisis turns get none.

        `extra_hints`: additional emotion_primary-style ids to score against,
        alongside `emotion_id`. Exists because some gold exemplars are tagged
        by a signal a DIFFERENT engine detects (e.g. fs_021 is tagged
        "spiritual_bypassing_defence", which defence_detector produces —
        emotion_analyzer never does). Without this, that exemplar competed
        against unrelated emotion-matched examples on a coin-flip instead of
        being reliably selected exactly when it should be.
        """
        if turn_action == "crisis" or not self.examples:
            return None

        lang_n = _norm_lang(lang)
        prefs = _REGISTER_PREFS.get(turn_action, ["diagnostic", "teaching"])
        hint_ids = [h for h in (extra_hints or []) if h]

        scored: list[tuple[int, dict[str, Any]]] = []
        for ex in self.examples:
            meta = ex.get("metadata") or {}
            if meta.get("verse_used") and turn_action not in ("teach", "validate"):
                # Keep verse-bearing gold mainly for teach (and rebuking→teach arcs).
                pass

            ex_lang = _norm_lang(meta.get("language"))
            # lang match: hi↔hinglish partial credit
            lang_score = 0
            if ex_lang == lang_n:
                lang_score = 30
            elif {ex_lang, lang_n} <= {"hi", "hinglish"}:
                lang_score = 20
            elif lang_n == "en" and ex_lang == "en":
                lang_score = 30

            ex_em = meta.get("emotion_primary")

            def _score_against(target: str) -> int:
                if ex_em == target:
                    return 50
                if ex_em and str(target).split("_")[0] == str(ex_em).split("_")[0]:
                    return 15
                return 0

            em_score = _score_against(emotion_id) if emotion_id else 0
            for hint in hint_ids:
                em_score = max(em_score, _score_against(hint))

            reg = (meta.get("register") or "").lower()
            reg_score = 0
            for i, pref in enumerate(prefs):
                if reg == pref or reg.startswith(pref):
                    reg_score = 25 - i * 3
                    break
            if not prefs and turn_action == "crisis":
                continue

            total = lang_score + em_score + reg_score
            if total <= 0:
                continue
            scored.append((total, ex))

        if not scored:
            # Soft fallback: any matching language, any register.
            for ex in self.examples:
                meta = ex.get("metadata") or {}
                if _norm_lang(meta.get("language")) == lang_n or (
                    lang_n in ("hi", "hinglish")
                    and _norm_lang(meta.get("language")) in ("hi", "hinglish")
                ):
                    scored.append((1, ex))
                    break

        if not scored:
            return None

        scored.sort(key=lambda t: t[0], reverse=True)
        # Prefer diverse conversation stages when scores close.
        picked: list[dict[str, Any]] = []
        seen_stages: set[str] = set()
        for score, ex in scored:
            stage = (ex.get("metadata") or {}).get("conversation_stage") or ex.get("id")
            if stage in seen_stages and score < 40:
                continue
            picked.append(ex)
            seen_stages.add(str(stage))
            if len(picked) >= max_examples:
                break

        if not picked:
            picked = [scored[0][1]]

        blocks = [self.format_example(ex) for ex in picked]
        return "\n\n---\n\n".join(blocks)

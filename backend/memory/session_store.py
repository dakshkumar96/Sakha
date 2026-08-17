"""Session memory.

Phase 6 makes the model rich enough that Phase 4 can migrate it to Supabase
without redesign: the fields here are the fields that will be encrypted and
persisted per user.

Storage is still in-process, with an OPTIONAL local disk dump for multi-restart
development only. That dump is plaintext and lives under tmp/ — it is
explicitly NOT the Phase 4 encrypted store, and must never be pointed at real
user data.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger("krishna.session")


@dataclass
class SessionState:
    session_id: str
    turn_count: int = 0
    questions_asked: int = 0
    verses_delivered: set[str] = field(default_factory=set)
    last_crisis_level: str = "NONE"
    last_emotion: str | None = None

    # --- Phase 6 depth fields ---
    #: Structured read of what is actually stuck, from the knot summarizer.
    last_knot: dict | None = None
    #: emotion_id -> how many turns it has appeared in this session.
    themes: dict[str, int] = field(default_factory=dict)
    #: Whether the nimitta disclosure has already been made.
    disclosure_done: bool = False
    #: Last detected language ("en" | "hi" | "hinglish") for mirroring.
    user_language: str = "en"
    #: Soft delivery preference: sakha | guru | sarathi.
    mode_pref: str | None = None
    #: Turns where dependency/parasocial language appeared.
    dependency_hits: int = 0
    #: Metaphor-bank ids already spoken this session (anti-repeat).
    metaphors_delivered: set[str] = field(default_factory=set)
    #: Consecutive turns (ending with this one) where intent was pushing_back.
    #: Confirmed gap: without this, "you're right" followed by no actual
    #: change in behaviour repeats every time pushback recurs, because the
    #: planner had no memory of it having happened before.
    pushback_streak: int = 0

    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def recurring_theme(self, min_count: int = 3) -> str | None:
        """The emotion this session keeps returning to.

        Drives progressive depth: the third time someone circles the same
        shame, the teaching should go further than it did the first time.
        Never named aloud — persona rule is that the intelligence is invisible.
        """
        if not self.themes:
            return None
        top, count = max(self.themes.items(), key=lambda kv: kv[1])
        return top if count >= min_count else None

    def depth_level(self) -> int:
        """1-4, from how much ground this session has already covered."""
        if self.turn_count >= 10:
            return 4
        if self.turn_count >= 6:
            return 3
        if self.turn_count >= 3:
            return 2
        return 1

    # --- serialisation (local dev persistence only) ---

    def to_dict(self) -> dict:
        data = asdict(self)
        data["verses_delivered"] = sorted(self.verses_delivered)
        data["metaphors_delivered"] = sorted(self.metaphors_delivered)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        data = dict(data)
        data["verses_delivered"] = set(data.get("verses_delivered", []))
        data["metaphors_delivered"] = set(data.get("metaphors_delivered", []))
        known = {f for f in cls.__dataclass_fields__}  # tolerate older dumps
        return cls(**{k: v for k, v in data.items() if k in known})


class SessionStore:
    def __init__(self, persist_dir: Path | None = None):
        self._sessions: dict[str, SessionState] = {}
        self._persist_dir = persist_dir
        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)

    # --- lookup ---

    def get_or_create(self, session_id: str) -> SessionState:
        state = self._sessions.get(session_id)
        if state is not None:
            return state

        state = self._load(session_id) or SessionState(session_id=session_id)
        self._sessions[session_id] = state
        return state

    def record_turn(
        self,
        session_id: str,
        asked_question: bool,
        verses_used: list[str],
        crisis_level: str,
        emotion_primary: str | None = None,
        knot: dict | None = None,
        language: str | None = None,
        dependency: bool = False,
        metaphors_used: list[str] | None = None,
        pushback: bool = False,
    ) -> SessionState:
        state = self.get_or_create(session_id)
        state.turn_count += 1
        if asked_question:
            state.questions_asked += 1
        state.verses_delivered.update(verses_used)
        if metaphors_used:
            state.metaphors_delivered.update(metaphors_used)
        state.last_crisis_level = crisis_level
        state.pushback_streak = state.pushback_streak + 1 if pushback else 0

        if emotion_primary:
            state.last_emotion = emotion_primary
            state.themes[emotion_primary] = state.themes.get(emotion_primary, 0) + 1
        if knot:
            state.last_knot = knot
        if language:
            state.user_language = language
        if dependency:
            state.dependency_hits += 1

        state.updated_at = time.time()
        self._save(state)
        return state

    def mark_disclosure_done(self, session_id: str) -> None:
        state = self.get_or_create(session_id)
        state.disclosure_done = True
        self._save(state)

    # --- optional local persistence ---

    def _path(self, session_id: str) -> Path | None:
        if not self._persist_dir:
            return None
        # Session ids are client-supplied; keep them from escaping the dir.
        safe = "".join(c for c in session_id if c.isalnum() or c in "-_")[:80]
        if not safe:
            return None
        return self._persist_dir / f"{safe}.json"

    def _save(self, state: SessionState) -> None:
        path = self._path(state.session_id)
        if not path:
            return
        try:
            path.write_text(
                json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            logger.warning("Could not persist session %s", state.session_id, exc_info=True)

    def _load(self, session_id: str) -> SessionState | None:
        path = self._path(session_id)
        if not path or not path.exists():
            return None
        try:
            return SessionState.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            logger.warning("Could not restore session %s", session_id, exc_info=True)
            return None

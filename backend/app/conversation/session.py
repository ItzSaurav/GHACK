"""Session management for conversational eligibility checking."""

import time
import uuid

from pydantic import BaseModel, Field

from backend.app.schemes.models import CitizenFacts


class MessageRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user", "assistant", "system"
    text: str
    language: str = "hi"
    source: str = "text"  # "text", "voice"
    audio_confidence: float | None = None
    timestamp: float = Field(default_factory=time.time)


class ConversationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    language: str = "hi"  # "hi" or "en"
    facts: CitizenFacts = Field(default_factory=CitizenFacts)
    messages: list[MessageRecord] = Field(default_factory=list)
    current_question_key: str | None = None
    pending_confirmation_field: str | None = None
    created_at: float = Field(default_factory=time.time)
    last_active: float = Field(default_factory=time.time)
    is_completed: bool = False

    def update_activity(self) -> None:
        self.last_active = time.time()


class SessionStore:
    def __init__(self, session_ttl_seconds: int = 3600):
        self.ttl = session_ttl_seconds
        self._sessions: dict[str, ConversationSession] = {}

    def get_or_create(self, session_id: str | None = None, language: str = "hi") -> ConversationSession:
        self.cleanup_expired()
        if session_id and session_id in self._sessions:
            sess = self._sessions[session_id]
            sess.update_activity()
            return sess

        new_id = session_id or str(uuid.uuid4())
        new_session = ConversationSession(session_id=new_id, language=language)
        self._sessions[new_id] = new_session
        return new_session

    def get(self, session_id: str) -> ConversationSession | None:
        self.cleanup_expired()
        return self._sessions.get(session_id)

    def cleanup_expired(self) -> None:
        now = time.time()
        expired_keys = [k for k, v in self._sessions.items() if (now - v.last_active) > self.ttl]
        for k in expired_keys:
            del self._sessions[k]


session_store = SessionStore()

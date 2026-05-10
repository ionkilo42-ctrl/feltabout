"""
Feltabout Backend — Session Gateway with MiniMax LLM Integration
FastAPI + WebSocket + MiniMax-M2.7 facilitation engine
"""

import os
import re
import uuid
import json
import time
import asyncio
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger("relatefx")

# ─── Config ───────────────────────────────────────────────────────────────────

load_dotenv()

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
MINIMAX_MODEL = "MiniMax-M2.7"
LOCAL_MODEL = "local-facilitation-mock"
MAX_TOKENS = int(os.environ.get("MINIMAX_MAX_TOKENS", "1000"))
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "2"))
USE_POSTGRES = os.environ.get("USE_POSTGRES", "false") == "true"
USE_AUTH = os.environ.get("USE_AUTH", "false") == "true"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/relatefx"
)

# OpenAI-compatible (ChatAnyone proxy) config
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "minimax")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://free.v36.cm/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# ─── App Setup ────────────────────────────────────────────────────────────────

_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app = FastAPI(title="Feltabout", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Lifespan (Postgres init on startup) ──────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup if USE_POSTGRES=true."""
    if USE_POSTGRES:
        try:
            from models import init_db
            await init_db()
            app.state.postgres_ready = True
        except Exception as e:
            app.state.postgres_ready = False
            print(f"[Feltabout] Postgres init failed — falling back to in-memory: {e}")
    yield
    # cleanup if needed

app.router.lifespan_context = lifespan

# ─── Pydantic Models ───────────────────────────────────────────────────────────

class Participant(BaseModel):
    id: str
    name: str
    role: str = "participant"
    emotion: str = "neutral"
    goals: list[str] = []

class Utterance(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    speaker_id: str
    speaker_name: str = ""
    text: str
    timestamp: str = ""

class SafetyFlag(BaseModel):
    level: str
    reason: str
    triggered_by: str
    is_abuse_related: bool = False
    reviewed_by_human: bool = False

class SessionState(BaseModel):
    session_id: str
    participants: dict[str, Participant] = {}
    utterances: list[dict] = []
    safety_flags: list[SafetyFlag] = []
    unresolved_topics: list[str] = []
    last_speaker_id: Optional[str] = None
    mode: str = "facilitation"
    created_at: str = ""
    locked: bool = False

class EscalationRequest(BaseModel):
    triggered_by: str = ""
    reason: str = ""

# ─── Safety Pre-Check ──────────────────────────────────────────────────────────

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end it all", "want to die", "take my life",
    "self-harm", "cut myself", "overdose", "hang myself", "jump off",
    "slit my wrists", "end it all",
]
ABUSE_KEYWORDS = [
    "hit me", "hurt me", "abuse", "threatening", "blackmail",
    "coercion", "controlling", "isolating me", "threatened", "attacked me",
    "beat me", "going to hurt them",
]
RISK_PATTERNS = [
    r"\bweapon\b", r"\bgun\b", r"\bknife\b", r"\bgoing to hurt\b",
    r"\bbreak (his|her|their) (phone|belongings|stuff)\b",
]

def safety_check(text: str, speaker_id: str) -> Optional[SafetyFlag]:
    t = text.lower()
    for kw in CRISIS_KEYWORDS:
        if kw in t:
            return SafetyFlag(level="critical", reason=f"Crisis keyword: '{kw}'", triggered_by=speaker_id)
    for kw in ABUSE_KEYWORDS:
        if kw in t:
            return SafetyFlag(level="high", reason=f"Safety concern: '{kw}'", triggered_by=speaker_id)
    for pattern in RISK_PATTERNS:
        if re.search(pattern, t):
            return SafetyFlag(level="high", reason="Risk pattern detected", triggered_by=speaker_id)
    return None

# ─── Facilitation Prompt Builder ───────────────────────────────────────────────

SYSTEM_PROMPT = """You are Feltabout, an AI relationship facilitation assistant. You help people in difficult conversations — couples, family members, partners — communicate more effectively and safely.

IMPORTANT RULES:
1. NEVER give therapy or diagnose. You are a facilitator, not a therapist.
2. NEVER take sides. Both people deserve to be heard equally.
3. When someone shares something painful, first honor the emotion before exploring anything else.
4. Keep responses SHORT — 2 to 4 sentences maximum. Facilitators speak less, not more.
5. Use the conversation history to understand what has happened so far.
6. Watch for patterns: blame, stonewalling, defensiveness, escalation, contempt.
7. If someone is in crisis, prioritize safety immediately.
8. Guide toward specific, constructive next steps when the time is right.
9. When both people are present, actively invite the quiet person into the conversation.
10. If the conversation turns into an argument, slow it down and re-establish structure.

Your style: warm but structured. Think of a calm, experienced mediator who creates safety without judgment."""

def build_facilitation_prompt(
    speaker_name: str,
    speaker_message: str,
    conversation_history: list[dict],
    participants: dict[str, Participant],
    current_speaker_id: str,
    safety_flags: list[SafetyFlag],
    mode: str = "facilitation",
) -> list[dict]:
    messages = []
    history = conversation_history[-16:] if conversation_history else []
    if history:
        hist_block = ""
        for u in history:
            speaker = u.get("speaker_name", "Participant")
            hist_block += f"{speaker}: {u.get('text', '')}\n"
        messages.append({"role": "user", "content": f"Current conversation so far:\n{hist_block}"})
        messages.append({"role": "assistant", "content": "(understood)"})
    turn_count = len(conversation_history)
    if mode == "speaker-listener":
        prompt_text = f"""This is a SPEAKER-LISTENER exercise.

{speaker_name} just said: "{speaker_message}"

The speaker is about to share. Your job is to:
- Reflect the speaker's emotional experience first
- Invite the listener to paraphrase back what they heard
- Keep it to 2 sentences

        Respond now as Feltabout:"""
    else:
        other_names = [p.name for p in participants.values() if p.id != current_speaker_id]
        prompt_text = f"""Conversation turn #{turn_count}.

{speaker_name} just said: "{speaker_message}"

Other people in the session: {', '.join(other_names) if other_names else '(just you so far)'}
Recent safety flags: {[f.level for f in safety_flags[-3:]]}

Respond as Feltabout — keep it to 2-4 sentences, warm and structured:"""
    messages.append({"role": "user", "content": prompt_text})
    return messages

def local_facilitation_response(
    speaker_name: str,
    speaker_message: str,
    participants: dict[str, Participant],
    current_speaker_id: str,
    mode: str = "facilitation",
) -> str:
    """Deterministic local fallback so the app works without an external LLM key."""
    other_names = [p.name for p in participants.values() if p.id != current_speaker_id]
    trimmed = speaker_message.strip()
    if len(trimmed) > 120:
        trimmed = trimmed[:117].rstrip() + "..."
    quoted = f"\"{trimmed}\""
    if trimmed.endswith((".", "!", "?")):
        quoted_sentence = quoted
    else:
        quoted_sentence = quoted + "."

    if mode == "speaker-listener":
        return (
            f"{speaker_name}, I hear that this matters to you: {quoted_sentence} "
            "Let's have the listener reflect back what they heard before either of you responds."
        )

    invite = f" I'd like to hear from {other_names[0]} next." if other_names else ""
    return (
        f"Thank you, {speaker_name}. I hear the concern in what you shared: {quoted_sentence} "
        f"Let's slow this down and name the specific need underneath it.{invite}"
    )

# ─── MiniMax LLM Call (streaming SSE) ────────────────────────────────────────

MINIMAX_URL = "https://api.minimax.io/v1/text/chatcompletion_v2"

def _visible_model_text(text: str) -> str:
    """Remove MiniMax reasoning tags from user-visible facilitator text."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

async def stream_minimax(
    speaker_name: str,
    speaker_message: str,
    conversation_history: list[dict],
    participants: dict[str, Participant],
    current_speaker_id: str,
    safety_flags: list[SafetyFlag],
    mode: str = "facilitation",
) -> AsyncGenerator[tuple[str, str], None]:
    if not MINIMAX_API_KEY:
        yield ("complete", local_facilitation_response(
            speaker_name=speaker_name,
            speaker_message=speaker_message,
            participants=participants,
            current_speaker_id=current_speaker_id,
            mode=mode,
        ))
        return

    messages = build_facilitation_prompt(
        speaker_name, speaker_message, conversation_history,
        participants, current_speaker_id, safety_flags, mode,
    )
    payload = {
        "model": MINIMAX_MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(MINIMAX_URL, headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            }, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = ""
        choices = data.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message", {})
            content = (
                message.get("content")
                or message.get("text")
                or choice.get("text")
                or ""
            )

        visible_content = _visible_model_text(content)
        if not visible_content:
            visible_content = (
                "I want to pause and slow this down. "
                "Could each person name one thing they most need the other to understand right now?"
            )
        yield ("complete", visible_content)
    except Exception as e:
        yield ("error", f"LLM stream error: {type(e).__name__}")

# ─── Session Manager (In-Memory, sync) ────────────────────────────────────────

class SessionManager:
    """In-memory session store — used when USE_POSTGRES=false."""

    def __init__(self):
        self.sessions: dict[str, SessionState] = {}

    # Match async interface so Pylance sees both manager types as awaitable
    async def create(self, session_id: Optional[str] = None) -> SessionState:
        return self._sync_create(session_id)

    async def get(self, session_id: str) -> Optional[SessionState]:
        return self._sync_get(session_id)

    async def add_participant(self, session_id: str, name: str) -> Participant:
        return self._sync_add_participant(session_id, name)

    async def get_other_participant(self, session_id: str, exclude_id: str) -> Optional[Participant]:
        return self._sync_get_other(session_id, exclude_id)

    async def add_utterance(self, session_id: str, speaker_id: str, speaker_name: str, text: str, is_facilitator: bool = False) -> None:
        self._sync_add_utterance(session_id, speaker_id, speaker_name, text, is_facilitator)

    async def add_safety_flag(self, session_id: str, flag: SafetyFlag) -> None:
        self._sync_add_safety_flag(session_id, flag)

    async def set_mode(self, session_id: str, mode: str) -> None:
        self._sync_set_mode(session_id, mode)

    async def lock_session(self, session_id: str) -> bool:
        state = self.sessions.get(session_id)
        if state:
            state.locked = True
            return True
        return False

    async def unlock_session(self, session_id: str) -> bool:
        state = self.sessions.get(session_id)
        if state:
            state.locked = False
            return True
        return False

    async def is_locked(self, session_id: str) -> bool:
        state = self.sessions.get(session_id)
        return state.locked if state else False

    async def get_utterances(self, session_id: str) -> list[dict]:
        return self._sync_get_utterances(session_id)

    async def get_safety_flags(self, session_id: str) -> list[SafetyFlag]:
        return self._sync_get_safety_flags(session_id)

    async def get_mode(self, session_id: str) -> str:
        return self._sync_get_mode(session_id)

    async def get_participants(self, session_id: str) -> dict[str, Participant]:
        return self._sync_get_participants(session_id)

    async def get_last_speaker(self, session_id: str) -> Optional[str]:
        return self._sync_get_last_speaker(session_id)

    def _evict_stale(self) -> None:
        cutoff = datetime.utcnow().timestamp() - (SESSION_TTL_HOURS * 3600)
        stale = [
            sid for sid, state in self.sessions.items()
            if datetime.fromisoformat(state.created_at).timestamp() < cutoff
        ]
        for sid in stale:
            del self.sessions[sid]

    def _sync_create(self, session_id: Optional[str] = None) -> SessionState:
        self._evict_stale()
        sid = session_id or uuid.uuid4().hex[:12]
        state = SessionState(session_id=sid, created_at=datetime.utcnow().isoformat())
        self.sessions[sid] = state
        return state

    def _sync_get(self, session_id: str) -> Optional[SessionState]:
        return self.sessions.get(session_id)

    def _sync_add_participant(self, session_id: str, name: str) -> Participant:
        self._evict_stale()
        p = Participant(id=uuid.uuid4().hex[:8], name=name)
        self.sessions[session_id].participants[p.id] = p
        return p

    def _sync_get_other(self, session_id: str, exclude_id: str) -> Optional[Participant]:
        state = self.sessions.get(session_id)
        if not state:
            return None
        for pid, p in state.participants.items():
            if pid != exclude_id:
                return p
        return None

    def _sync_add_utterance(self, session_id: str, speaker_id: str, speaker_name: str, text: str, is_facilitator: bool = False) -> None:
        state = self.sessions.get(session_id)
        if state:
            state.utterances.append({
                "id": uuid.uuid4().hex[:8],
                "speaker_id": speaker_id,
                "speaker_name": speaker_name,
                "text": text,
                "timestamp": datetime.utcnow().isoformat(),
            })
            state.last_speaker_id = speaker_id

    def _sync_add_safety_flag(self, session_id: str, flag: SafetyFlag) -> None:
        state = self.sessions.get(session_id)
        if state:
            state.safety_flags.append(flag)

    def _sync_set_mode(self, session_id: str, mode: str) -> None:
        state = self.sessions.get(session_id)
        if state:
            state.mode = mode

    def _sync_get_utterances(self, session_id: str) -> list[dict]:
        state = self.sessions.get(session_id)
        return state.utterances if state else []

    def _sync_get_safety_flags(self, session_id: str) -> list[SafetyFlag]:
        state = self.sessions.get(session_id)
        return state.safety_flags if state else []

    def _sync_get_mode(self, session_id: str) -> str:
        state = self.sessions.get(session_id)
        return state.mode if state else "facilitation"

    def _sync_get_participants(self, session_id: str) -> dict[str, Participant]:
        state = self.sessions.get(session_id)
        return state.participants if state else {}

    def _sync_get_last_speaker(self, session_id: str) -> Optional[str]:
        state = self.sessions.get(session_id)
        return state.last_speaker_id if state else None


# ─── Postgres Session Manager (async delegate) ──────────────────────────────────

class PostgresSessionManager:
    """Async Postgres-backed session store — used when USE_POSTGRES=true."""

    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self._engine = None
        self._session_factory = None

    async def _get_session(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        if self._engine is None:
            self._engine = create_async_engine(self.db_url, echo=False, pool_pre_ping=True)
            self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)
        async with self._session_factory() as session:
            yield session

    async def create(self, session_id: Optional[str] = None):
        from models import Session, async_session
        sid = session_id or uuid.uuid4().hex[:12]
        async with async_session() as db:
            session_obj = Session(session_id=sid, created_at=datetime.utcnow())
            db.add(session_obj)
            await db.commit()
            return SessionState(session_id=sid, created_at=datetime.utcnow().isoformat())

    async def get(self, session_id: str) -> Optional[SessionState]:
        from models import Session, Participant, SafetyFlag, async_session
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        async with async_session() as db:
            result = await db.execute(
                select(Session)
                .options(selectinload(Session.participants), selectinload(Session.utterances), selectinload(Session.safety_flags))
                .where(Session.session_id == session_id)
            )
            db_session = result.scalar_one_or_none()
            if not db_session:
                return None
            return SessionState(
                session_id=db_session.session_id,
                mode=db_session.mode,
                last_speaker_id=db_session.last_speaker_id,
                created_at=db_session.created_at.isoformat(),
                participants={p.id: Participant(id=p.id, name=p.name, role=p.role, emotion=p.emotion) for p in db_session.participants},
                utterances=[{"id": u.id, "speaker_id": u.speaker_id, "speaker_name": u.speaker_name, "text": u.text, "timestamp": u.timestamp.isoformat()} for u in db_session.utterances],
                safety_flags=[SafetyFlag(level=f.level, reason=f.reason, triggered_by=f.triggered_by) for f in db_session.safety_flags],
            )

    async def add_participant(self, session_id: str, name: str) -> Participant:
        from models import Participant as DBParticipant, async_session
        p = Participant(id=uuid.uuid4().hex[:8], name=name)
        async with async_session() as db:
            db_p = DBParticipant(id=p.id, session_id=session_id, name=name)
            db.add(db_p)
            await db.commit()
        return p

    async def get_other_participant(self, session_id: str, exclude_id: str) -> Optional[Participant]:
        from models import Participant as DBParticipant, async_session
        from sqlalchemy import select, and_
        async with async_session() as db:
            result = await db.execute(
                select(DBParticipant).where(
                    and_(DBParticipant.session_id == session_id, DBParticipant.id != exclude_id)
                )
            )
            db_p = result.scalar_one_or_none()
            if not db_p:
                return None
            return Participant(id=db_p.id, name=db_p.name, role=db_p.role, emotion=db_p.emotion)

    async def add_utterance(self, session_id: str, speaker_id: str, speaker_name: str, text: str, is_facilitator: bool = False) -> None:
        from models import Utterance as DBUtterance, Session, async_session
        from sqlalchemy import select
        async with async_session() as db:
            db_u = DBUtterance(
                id=uuid.uuid4().hex[:8],
                session_id=session_id,
                speaker_id=speaker_id,
                speaker_name=speaker_name,
                text=text,
                timestamp=datetime.utcnow(),
                is_facilitator="facilitator" if is_facilitator else "participant",
            )
            db.add(db_u)
            await db.execute(select(Session).where(Session.session_id == session_id))
            await db.commit()

    async def add_safety_flag(self, session_id: str, flag: SafetyFlag) -> None:
        from models import SafetyFlag as DBSafetyFlag, async_session
        async with async_session() as db:
            db_f = DBSafetyFlag(id=uuid.uuid4().hex[:8], session_id=session_id, level=flag.level, reason=flag.reason, triggered_by=flag.triggered_by)
            db.add(db_f)
            await db.commit()

    async def set_mode(self, session_id: str, mode: str) -> None:
        from models import Session, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(select(Session).where(Session.session_id == session_id))
            db_session = result.scalar_one_or_none()
            if db_session:
                db_session.mode = mode
                await db.commit()

    async def get_utterances(self, session_id: str) -> list[dict]:
        from models import Utterance as DBUtterance, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(
                select(DBUtterance).where(DBUtterance.session_id == session_id).order_by(DBUtterance.timestamp)
            )
            return [{"id": u.id, "speaker_id": u.speaker_id, "speaker_name": u.speaker_name, "text": u.text, "timestamp": u.timestamp.isoformat()} for u in result.scalars().all()]

    async def get_safety_flags(self, session_id: str) -> list[SafetyFlag]:
        from models import SafetyFlag as DBSafetyFlag, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(
                select(DBSafetyFlag).where(DBSafetyFlag.session_id == session_id).order_by(DBSafetyFlag.created_at)
            )
            return [SafetyFlag(level=f.level, reason=f.reason, triggered_by=f.triggered_by) for f in result.scalars().all()]

    async def get_mode(self, session_id: str) -> str:
        from models import Session, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(select(Session).where(Session.session_id == session_id))
            db_session = result.scalar_one_or_none()
            return db_session.mode if db_session else "facilitation"

    async def get_participants(self, session_id: str) -> dict[str, Participant]:
        from models import Participant as DBParticipant, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(select(DBParticipant).where(DBParticipant.session_id == session_id))
            return {p.id: Participant(id=p.id, name=p.name, role=p.role, emotion=p.emotion) for p in result.scalars().all()}

    async def get_last_speaker(self, session_id: str) -> Optional[str]:
        from models import Session, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(select(Session).where(Session.session_id == session_id))
            db_session = result.scalar_one_or_none()
            return db_session.last_speaker_id if db_session else None

    async def lock_session(self, session_id: str) -> bool:
        from models import Session, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(select(Session).where(Session.session_id == session_id))
            db_session = result.scalar_one_or_none()
            if db_session:
                db_session.locked = True
                await db.commit()
                return True
            return False

    async def unlock_session(self, session_id: str) -> bool:
        from models import Session, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(select(Session).where(Session.session_id == session_id))
            db_session = result.scalar_one_or_none()
            if db_session:
                db_session.locked = False
                await db.commit()
                return True
            return False

    async def is_locked(self, session_id: str) -> bool:
        from models import Session, async_session
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(select(Session.locked).where(Session.session_id == session_id))
            row = result.first()
            return row[0] if row else False


# ─── Auth router ──────────────────────────────────────────────────────────────

from routers.auth import router as auth_router  # noqa: E402
app.include_router(auth_router)

# ─── Auth dependency ──────────────────────────────────────────────────────────

async def get_current_user(authorization: str = Header(None)) -> dict | None:
    """Returns user payload if USE_AUTH=true and token is valid, else None."""
    if not USE_AUTH:
        return {"sub": None, "email": "dev-user@local", "name": "Developer"}
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ")[1]
    from auth import decode_token
    payload = decode_token(token)
    return payload  # None if invalid

# ─── Manager factory & app.state ───────────────────────────────────────────────

if USE_POSTGRES:
    manager = PostgresSessionManager()
else:
    manager = SessionManager()

# ─── Active WebSocket connections (for broadcasting) ───────────────────────────

active_connections: dict[str, set[WebSocket]] = defaultdict(set)

# ─── Facilitation state (per session) ─────────────────────────────────────────

turn_managers: dict[str, dict] = defaultdict(dict)
intervention_policies: dict = {}  # type: ignore


async def broadcast_to_session(session_id: str, message: dict, exclude: WebSocket | None = None) -> None:
    """Broadcast a message to all connected clients in a session, optionally excluding one."""
    if session_id not in active_connections:
        return
    for connection in list(active_connections[session_id]):
        if connection is not exclude:
            try:
                await connection.send_json(message)
            except Exception:
                # Remove dead connections silently
                active_connections[session_id].discard(connection)


# ─── TTS broadcast helper ─────────────────────────────────────────────────────

async def _publish_tts_audio(session_id: str, text: str) -> None:
    """
    Synthesize facilitator text via ElevenLabs (PCM s16le 24kHz) and publish
    as a LiveKit audio track. Runs as a fire-and-forget background task —
    never blocks facilitation.

    Error resilience:
      - TTS synthesis timeout (>5s) → log warning, text response still sent
      - LiveKit publish failure → log warning, session continues in text mode
      - Any exception → never crashes; text response is always the fallback
    """
    _logger = logging.getLogger("relatefx.tts.publish")

    try:
        from voice.tts import synthesize_facilitator_speech_async, SynthesizedAudio
        from voice.livekit_integration import get_voice_room, publish_facilitator_audio

        # ── Timeout guard: 5 seconds for synthesis ────────────────────────────
        # If ElevenLabs takes longer, fall back to text-only (the facilitator
        # response was already sent via WebSocket to all clients)
        try:
            audio: SynthesizedAudio = await asyncio.wait_for(
                synthesize_facilitator_speech_async(text),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            _logger.warning(f"[TTS] synthesis timed out after 5s for session {session_id} — text fallback")
            return  # Text response already delivered via WebSocket

        audio_bytes = audio.audio_bytes
        estimated_duration_s = audio.samples_per_channel / audio.sample_rate

        _logger.info(
            f"[TTS] session={session_id} | text_len={len(text)} | "
            f"audio_bytes={len(audio_bytes)} | duration={estimated_duration_s:.1f}s"
        )

        # ── Publish into LiveKit room via facilitator-bot ───────────────────────
        room = get_voice_room(session_id)
        if room is not None:
            try:
                await publish_facilitator_audio(
                    room,
                    audio_bytes=audio_bytes,
                    sample_rate=audio.sample_rate,
                    num_channels=audio.num_channels,
                )
                _logger.info(f"[TTS] published {len(audio_bytes)} bytes to room {session_id}")
            except Exception as pub_err:
                # LiveKit publish failure — log and continue; text is already in chat
                _logger.warning(f"[TTS] publish failed for session {session_id}: {pub_err}")
        else:
            # No LiveKit room — voice wasn't joined or room was disconnected
            # This is expected when voice is disabled; no action needed
            _logger.debug(f"[TTS] no LiveKit room for session {session_id}")

    except Exception as e:
        # Catch-all: any other failure ( ElevenLabs auth error, etc.)
        # The text response was already broadcast via WebSocket — no data loss
        _logger.warning(f"[TTS] unexpected error for session {session_id}: {e}")


# ─── Voice / STT background tasks ─────────────────────────────────────────────

voice_stt_tasks: dict[str, asyncio.Task] = {}


async def inject_voice_utterance(session_id: str, speaker_id: str, text: str) -> None:
    """
    Inject a transcribed voice utterance into the facilitation pipeline.
    Mirrors the text message handling path but is called by the STT pipeline,
    not by a WebSocket message. Triggers the same policy evaluation, turn manager,
    safety branch, and facilitator decision logging.

    speaker_id: the participant ID resolved from the diarization speaker tag.
    text: the transcribed text from Deepgram.
    """
    from voice.livekit_integration import is_voice_enabled

    # Skip if voice not enabled for this session
    if not is_voice_enabled(session_id):
        return

    state = await manager.get(session_id)
    if state is None:
        return

    speaker_name = state.participants.get(speaker_id, Participant(id="", name="Unknown")).name \
        if speaker_id in state.participants else "Unknown"
    ts = datetime.utcnow().isoformat()
    utterance_id = uuid.uuid4().hex[:8]

    utterance = {
        "id": utterance_id,
        "speaker_id": speaker_id,
        "speaker_name": speaker_name,
        "text": text,
        "timestamp": ts,
    }

    await manager.add_utterance(session_id, speaker_id, speaker_name, text)

    # Safety check (identical to text message path)
    safety = safety_check(text, speaker_id)
    if safety:
        from safety.classifier import classify_safety_risk
        history = await manager.get_utterances(session_id)
        history_texts = [u.get("text", "") for u in history[-5:]]
        risk = await classify_safety_risk(text, history_texts, MINIMAX_API_KEY)
        is_high_risk = risk.get("risk_level") == "high"
        is_abuse = risk.get("is_abuse_related", False)
        flag = SafetyFlag(level=safety.level, reason=safety.reason, triggered_by=speaker_id, is_abuse_related=is_abuse)
        await manager.add_safety_flag(session_id, flag)

        if is_high_risk or is_abuse:
            await manager.lock_session(session_id)
            whisper = (
                "I'm checking in because I noticed some language that could be concerning. "
                "Are you safe right now? Contact the National Domestic Violence Hotline: 1-800-799-7233. "
                "Your partner cannot see this message."
            )
            await broadcast_to_session(session_id, {
                "type": "facilitator_whisper", "whisper": whisper, "is_safety_check": True,
            })
            await broadcast_to_session(session_id, {
                "type": "utterance",
                "utterance": {
                    "id": uuid.uuid4().hex[:8], "speaker_id": "facilitator",
                    "speaker_name": "Feltabout", "text": (
                        "I'm pausing this conversation for safety review. "
                        "A human facilitator will review what was shared and reach out."
                    ), "timestamp": datetime.utcnow().isoformat(),
                },
                "facilitator_response": None,
                "safety_flags": [flag.model_dump()],
                "locked": True,
            })
        else:
            response_text = (
                "I want to pause here — what you're sharing sounds really serious. "
                "Please reach out to a trusted person or call 988 (Suicide & Crisis Lifeline)."
            ) if safety.level == "critical" else (
                "I'm noticing something sensitive here. Let's slow down and make sure "
                "everyone feels safe. I'm flagging this for human review."
            )
            await broadcast_to_session(session_id, {
                "type": "utterance", "utterance": utterance,
                "facilitator_response": response_text,
                "safety_flags": [flag.model_dump()],
            })
        return

    # Turn management
    current_mode = (await manager.get_mode(session_id)) or "facilitation"
    from facilitation.turn_manager import TurnManager
    if session_id not in turn_managers:
        turn_managers[session_id] = {}
    turn_mgr = turn_managers[session_id].get("manager")

    turn_result = None
    if current_mode == "speaker-listener":
        if turn_mgr is None:
            participants_dict = await manager.get_participants(session_id)
            turn_mgr = TurnManager(session_id)
            turn_mgr.initialize(participants_dict)
            turn_managers[session_id]["manager"] = turn_mgr
        if turn_mgr:
            turn_result = turn_mgr.handle_message(speaker_id, text)
            if turn_result and not turn_result.get("allowed"):
                # Out-of-turn — send whisper via WebSocket (client will handle)
                whisper = turn_result.get("whisper", "")
                if whisper:
                    await broadcast_to_session(session_id, {
                        "type": "facilitator_whisper", "whisper": whisper,
                    })
                return

    # Intervention policy + metrics
    _timer = time.monotonic()
    utterances = await manager.get_utterances(session_id)
    from facilitation.intervention_policy import InterventionPolicy
    if session_id not in intervention_policies:
        intervention_policies[session_id] = InterventionPolicy(session_id)
    policy = intervention_policies[session_id]
    decision = policy.evaluate(text, current_mode, turn_mgr, utterances)
    _latency_ms = int((time.monotonic() - _timer) * 1000)

    _turn_phase = None
    if turn_mgr:
        _turn_state = turn_mgr.get_state()
        _turn_phase = _turn_state.get("phase") if _turn_state else None
    _conflict = None
    if hasattr(decision, "conflict_pattern") and decision.conflict_pattern:
        _conflict = decision.conflict_pattern.value if hasattr(decision.conflict_pattern, "value") else str(decision.conflict_pattern)
    from facilitation.metrics import log_facilitator_decision
    asyncio.create_task(log_facilitator_decision(
        session_id=session_id, utterance_id=utterance_id,
        should_speak=decision.should_speak,
        intervention_type=decision.intervention_type.value if hasattr(decision.intervention_type, "value") else str(decision.intervention_type) if decision.intervention_type else None,
        confidence=decision.confidence, trigger_reason=decision.reason, latency_ms=_latency_ms,
        mode=current_mode, turn_phase=_turn_phase, conflict_pattern=_conflict,
    ))

    # Broadcast utterance
    await broadcast_to_session(session_id, {
        "type": "utterance", "utterance": utterance,
        "facilitator_response": None, "safety_flags": [],
    })

    if decision.should_speak:
        from facilitation.llm_intervention import get_llm_intervention
        output = await get_llm_intervention(
            intervention_type=decision.intervention_type,
            speaker_message=text, speaker_name=speaker_name,
            context=decision.reason, conversation_history=utterances,
        )
        msg_index = len(await manager.get_utterances(session_id))
        await broadcast_to_session(session_id, {
            "type": "facilitator_complete", "full_text": output.response,
            "index": msg_index, "intervention_type": output.intervention_type.value,
            "confidence": output.confidence,
        })
        if output.response:
            await manager.add_utterance(session_id, "facilitator", "Feltabout", output.response, is_facilitator=True)

        # TTS: synthesize and broadcast audio via LiveKit (if voice enabled)
        from voice.livekit_integration import is_voice_enabled as voice_is_enabled
        if voice_is_enabled(session_id):
            asyncio.create_task(_publish_tts_audio(session_id, output.response))
    else:
        await broadcast_to_session(session_id, {
            "type": "facilitator_idle",
            "reason": decision.reason,
        })


# ─── WebSocket Handler ─────────────────────────────────────────────────────────

# ─── Scoped WS Token Validation (Phase 4) ────────────────────────────────────
import hmac
import base64
import time

def _get_ws_secret() -> bytes:
    secret = os.environ.get("WS_SHARED_SECRET")
    if not secret:
        env = os.environ.get("ENV", "development")
        if env == "production":
            raise RuntimeError(
                "WS_SHARED_SECRET environment variable is required in production."
            )
        else:
            enc_key = os.environ.get("ENCRYPTION_KEY")
            if enc_key:
                return enc_key.encode()[:32].ljust(32, b'0')
            return os.urandom(32)
    return secret.encode()

def _validate_ws_token(token: str, expected_session_id: str) -> Optional[dict]:
    """
    Validate a scoped WS access token.
    Returns payload dict if valid, None if invalid/expired/mismatched.
    """
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        payload_b64, signature_b64 = parts
        
        secret = _get_ws_secret()
        expected_sig = hmac.new(secret, payload_b64.encode(), 'sha256').digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')
        
        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            return None
        
        json_bytes = base64.urlsafe_b64decode(payload_b64)
        import json
        payload = json.loads(json_bytes)
        
        exp = payload.get('exp', 0)
        if time.time() > exp:
            return None
        
        if payload.get('wsid') != expected_session_id:
            return None
        
        return {
            "participant_id": payload['pid'],
            "space_id": payload['sid'],
            "session_id": payload['wsid'],
        }
    except Exception:
        return None


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()

    # Validate token from query params
    token = ws.query_params.get("token", None)

    if USE_AUTH:
        # JWT auth mode — existing behavior
        if not token:
            await ws.close(code=4001)
            return
        from auth import decode_token
        payload = decode_token(token)
        if not payload:
            await ws.close(code=4001)
            return
    elif token:
        # Scoped WS token mode (Phase 4) — guest invite flow
        # When USE_AUTH is off but token is present, validate scoped token
        validated = _validate_ws_token(token, session_id)
        if not validated:
            await ws.close(code=4003)
            return

    exists = await manager.get(session_id) is not None
    if not exists:
        await manager.create(session_id)
        await ws.send_json({"type": "session_created", "session_id": session_id})

    state = await manager.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Track this connection for broadcasting
    active_connections[session_id].add(ws)

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "join":
                name = data.get("name", "Anonymous")
                p = await manager.add_participant(session_id, name)
                state = await manager.get(session_id)
                other = await manager.get_other_participant(session_id, p.id)
                greeting = (
                    f"Welcome, {p.name}. {other.name if other else ''} is already here. "
                    "Both of you are now in a facilitated session. "
                    "I'll help guide this conversation. Feel free to begin when you're ready."
                ) if other else (
                    f"Welcome, {p.name}. You're the first one here. "
                    "Feel free to share what's on your mind, and I'll help guide the conversation."
                )

                # Send join confirmation to the joining client
                await ws.send_json({
                    "type": "participant_joined",
                    "participant": {"id": p.id, "name": p.name, "role": p.role, "emotion": p.emotion},
                    "session_id": session_id,
                    "greeting": greeting,
                    "participant_count": len(state.participants) if state else 1,
                })

                # Send full session history to the joining client (Phase 2)
                participants = await manager.get_participants(session_id)
                utterances = await manager.get_utterances(session_id)
                safety_flags = await manager.get_safety_flags(session_id)
                current_mode = await manager.get_mode(session_id)
                await ws.send_json({
                    "type": "state",
                    "state": {
                        "session_id": session_id,
                        "participants": [par.model_dump() for par in participants.values()],
                        "utterances": utterances,
                        "safety_flags": [f.model_dump() for f in safety_flags],
                        "mode": current_mode,
                    }
                })

                # Broadcast greeting utterance to ALL clients (including sender for consistency)
                greeting_utterance = {
                    "id": uuid.uuid4().hex[:8],
                    "speaker_id": "facilitator",
                    "speaker_name": "Feltabout",
                    "text": greeting,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await broadcast_to_session(session_id, {
                    "type": "utterance",
                    "utterance": greeting_utterance,
                    "facilitator_response": None,
                    "safety_flags": [],
                })

                # Broadcast participant_joined to OTHER clients
                await broadcast_to_session(session_id, {
                    "type": "participant_joined",
                    "participant": {"id": p.id, "name": p.name, "role": p.role, "emotion": p.emotion},
                    "session_id": session_id,
                    "greeting": None,
                    "participant_count": len(state.participants) if state else 1,
                }, exclude=ws)

            elif msg_type == "message":
                # Block all messages if session is locked
                if await manager.is_locked(session_id):
                    await ws.send_json({
                        "type": "facilitator_error",
                        "detail": "This session has been locked pending review.",
                    })
                    continue

                speaker_id = data.get("speaker_id")
                text = data.get("text", "").strip()
                client_id = data.get("client_id", "")
                if not speaker_id or not text:
                    continue

                state = await manager.get(session_id)
                if state is None:
                    continue

                ts = datetime.utcnow().isoformat()
                speaker_name = state.participants.get(speaker_id, Participant(id="", name="Unknown")).name if speaker_id in state.participants else "Unknown"
                utterance_id = uuid.uuid4().hex[:8]
                utterance = {
                    "id": utterance_id,
                    "speaker_id": speaker_id,
                    "speaker_name": speaker_name,
                    "text": text,
                    "timestamp": ts,
                }

                # Acknowledge receipt immediately
                await ws.send_json({
                    "type": "message_ack",
                    "backend_id": utterance_id,
                    "client_id": client_id,
                    "status": "received",
                })
                await manager.add_utterance(session_id, speaker_id, speaker_name, text)

                # Safety check — first line of defense
                safety = safety_check(text, speaker_id)
                if safety:
                    # Secondary classifier: deeper abuse/coercive control analysis
                    from safety.classifier import classify_safety_risk
                    history_texts = [u.get("text", "") for u in (await manager.get_utterances(session_id))[-5:]]
                    risk = await classify_safety_risk(text, history_texts, MINIMAX_API_KEY)
                    is_high_risk = risk.get("risk_level") == "high"
                    is_abuse = risk.get("is_abuse_related", False)

                    # Build safety flag with abuse marker
                    flag_to_add = SafetyFlag(
                        level=safety.level,
                        reason=safety.reason,
                        triggered_by=speaker_id,
                        is_abuse_related=is_abuse,
                    )
                    await manager.add_safety_flag(session_id, flag_to_add)

                    # ── Abuse-aware branch (high risk or coercive control detected) ──
                    if is_high_risk or is_abuse:
                        await manager.lock_session(session_id)

                        safety_whisper = (
                            "I'm checking in because I noticed some language in this conversation "
                            "that could be concerning. Are you safe right now? If you need support, "
                            "contact the National Domestic Violence Hotline: 1-800-799-7233. "
                            "Your partner cannot see this message."
                        )
                        # Send private safety whisper to ALL connections (client filters by their own ID)
                        await broadcast_to_session(session_id, {
                            "type": "facilitator_whisper",
                            "whisper": safety_whisper,
                            "is_safety_check": True,
                        })

                        # Broadcast session suspension to all
                        suspension_msg = (
                            "I'm pausing this conversation for safety review. "
                            "A human facilitator will review what was shared and reach out. "
                            "Please take care of yourselves in the meantime."
                        )
                        await broadcast_to_session(session_id, {
                            "type": "utterance",
                            "utterance": {
                                "id": uuid.uuid4().hex[:8],
                                "speaker_id": "facilitator",
                    "speaker_name": "Feltabout",
                    "text": suspension_msg,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                            "facilitator_response": None,
                            "safety_flags": [flag_to_add.model_dump()],
                            "locked": True,
                        })
                    else:
                        # Standard safety response (keyword trigger without high-risk pattern)
                        response_text = (
                            "I want to pause here — what you're sharing sounds really serious. "
                            "Your safety matters. Please reach out to a trusted person or call 988 "
                            "(Suicide & Crisis Lifeline). I want to flag this for human review as well."
                        ) if safety.level == "critical" else (
                            "I'm noticing this conversation is touching on something sensitive. "
                            "Let's slow down and make sure everyone feels safe. "
                            "I'm flagging this for human facilitator review."
                        )
                        flags = await manager.get_safety_flags(session_id)
                        await broadcast_to_session(session_id, {
                            "type": "utterance",
                            "utterance": utterance,
                            "facilitator_response": response_text,
                            "safety_flags": [f.model_dump() for f in flags[-5:]],
                        })
                    continue

                # ── Turn Management (speaker-listener mode) ───────────────────────
                state = await manager.get(session_id)
                current_mode = state.mode if state else "facilitation"

                from facilitation.turn_manager import TurnManager
                if session_id not in turn_managers:
                    turn_managers[session_id] = {}
                turn_mgr = turn_managers[session_id].get("manager")

                turn_result = None
                if current_mode == "speaker-listener":
                    if turn_mgr is None:
                        participants_dict = await manager.get_participants(session_id)
                        turn_mgr = TurnManager(session_id)
                        turn_mgr.initialize(participants_dict)
                        turn_managers[session_id]["manager"] = turn_mgr
                    if turn_mgr:
                        turn_result = turn_mgr.handle_message(speaker_id, text)
                        if turn_result and not turn_result.get("allowed"):
                            # Send private whisper only to the out-of-turn sender
                            whisper = turn_result.get("whisper", "")
                            if whisper:
                                await ws.send_json({
                                    "type": "facilitator_whisper",
                                    "whisper": whisper,
                                })
                            continue  # don't broadcast, don't run intervention
                        if turn_result and turn_result.get("advance"):
                            new_phase = turn_result.get("next_phase", {}).value if hasattr(turn_result.get("next_phase"), "value") else str(turn_result.get("next_phase"))
                            next_speaker_id = turn_result.get("next_speaker_id")
                            await broadcast_to_session(session_id, {
                                "type": "turn_advanced",
                                "phase": new_phase,
                                "current_speaker_id": next_speaker_id,
                                "current_listener_id": turn_mgr.current_listener_id,
                            })

                # ── Intervention Policy (decide whether to speak) ─────────────────
                _timer = time.monotonic()
                utterances = await manager.get_utterances(session_id)
                from facilitation.intervention_policy import InterventionPolicy
                if session_id not in intervention_policies:
                    intervention_policies[session_id] = InterventionPolicy(session_id)
                policy = intervention_policies[session_id]
                decision = policy.evaluate(text, current_mode, turn_mgr, utterances)
                _latency_ms = int((time.monotonic() - _timer) * 1000)

                # Log facilitator decision metric (fire-and-forget, never blocks)
                _turn_phase = None
                if turn_mgr:
                    _turn_state = turn_mgr.get_state()
                    _turn_phase = _turn_state.get("phase") if _turn_state else None
                _conflict = None
                if hasattr(decision, "conflict_pattern") and decision.conflict_pattern:
                    _conflict = decision.conflict_pattern.value if hasattr(decision.conflict_pattern, "value") else str(decision.conflict_pattern)
                from facilitation.metrics import log_facilitator_decision
                asyncio.create_task(log_facilitator_decision(
                    session_id=session_id,
                    utterance_id=utterance_id,
                    should_speak=decision.should_speak,
                    intervention_type=decision.intervention_type.value if hasattr(decision.intervention_type, "value") else str(decision.intervention_type) if decision.intervention_type else None,
                    confidence=decision.confidence,
                    trigger_reason=decision.reason,
                    latency_ms=_latency_ms,
                    mode=current_mode,
                    turn_phase=_turn_phase,
                    conflict_pattern=_conflict,
                ))

                # Broadcast user's utterance to all clients
                await broadcast_to_session(session_id, {
                    "type": "utterance",
                    "utterance": utterance,
                    "client_id": client_id,
                    "facilitator_response": None,
                    "safety_flags": [],
                })

                if decision.should_speak:
                    # Generate intervention response via LLM
                    from facilitation.llm_intervention import get_llm_intervention
                    output = await get_llm_intervention(
                        intervention_type=decision.intervention_type,
                        speaker_message=text,
                        speaker_name=speaker_name,
                        context=decision.reason,
                        conversation_history=utterances,
                    )
                    msg_index = len(await manager.get_utterances(session_id))
                    await broadcast_to_session(session_id, {
                        "type": "facilitator_complete",
                        "full_text": output.response,
                        "index": msg_index,
                        "intervention_type": output.intervention_type.value,
                        "confidence": output.confidence,
                    })
                    if output.response:
                        await manager.add_utterance(session_id, "facilitator", "Feltabout", output.response, is_facilitator=True)
                else:
                    await broadcast_to_session(session_id, {
                        "type": "facilitator_idle",
                        "reason": decision.reason,
                    })

            elif msg_type == "get_state":
                participants = await manager.get_participants(session_id)
                utterances = await manager.get_utterances(session_id)
                safety_flags = await manager.get_safety_flags(session_id)
                last_speaker = await manager.get_last_speaker(session_id)
                current_mode = await manager.get_mode(session_id)
                await ws.send_json({
                    "type": "state",
                    "state": {
                        "session_id": session_id,
                        "participants": [p.model_dump() for p in participants.values()],
                        "utterances": utterances,
                        "safety_flags": [f.model_dump() for f in safety_flags],
                        "last_speaker": last_speaker,
                        "mode": current_mode,
                    }
                })

            elif msg_type == "set_mode":
                # Block mode changes when session is locked
                if await manager.is_locked(session_id):
                    await ws.send_json({
                        "type": "facilitator_error",
                        "detail": "This session has been locked pending review.",
                    })
                    continue
                mode = data.get("mode", "facilitation")
                await manager.set_mode(session_id, mode)
                # Broadcast mode change to all clients
                await broadcast_to_session(session_id, {"type": "mode_changed", "mode": mode})

            elif msg_type == "request_debrief":
                utterances = await manager.get_utterances(session_id)
                safety_flags = await manager.get_safety_flags(session_id)
                debrief_text, structured = await _build_debrief(utterances, safety_flags)
                await ws.send_json({
                    "type": "debrief_response",
                    "text": debrief_text,
                    "topics": structured.get("topics", []),
                    "emotional_arc": structured.get("emotional_arc", ""),
                    "unresolved_items": structured.get("unresolved_items", []),
                    "recommendations": structured.get("recommendations", ""),
                    "safety_flags": [f.model_dump() for f in safety_flags],
                })

            elif msg_type == "crosstalk_detected":
                # Voice-specific: frontend detected simultaneous audio from 2+ participants.
                # Trigger a gentle facilitator intervention — same pattern as conflict escalation.
                # Log it as a crosstalk event in facilitator_decisions.
                from facilitation.metrics import log_facilitator_decision
                asyncio.create_task(log_facilitator_decision(
                    session_id=session_id,
                    utterance_id=None,
                    should_speak=True,
                    intervention_type="pause",
                    confidence=0.85,
                    trigger_reason="crosstalk",
                    latency_ms=0,
                    mode=(await manager.get_mode(session_id)) or "facilitation",
                    turn_phase=None,
                    conflict_pattern="crosstalk",
                ))
                await broadcast_to_session(session_id, {
                    "type": "facilitator_whisper",
                    "whisper": (
                        "I noticed both of you talking at once — that's completely natural in a "
                        "charged conversation. Let's slow down: one person at a time. "
                        "It helps me follow each person's full thought."
                    ),
                })

    except WebSocketDisconnect:
        pass
    finally:
        # Clean up connection on disconnect
        active_connections[session_id].discard(ws)
        if not active_connections[session_id]:
            del active_connections[session_id]

# ─── REST Endpoints ────────────────────────────────────────────────────────────

@app.post("/sessions")
async def create_session(
    body: Optional[dict] = Body(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new session.
    
    For normal users (USE_AUTH=true): requires valid auth token.
    For internal callers: pass INTERNAL_API_KEY header to bypass auth.
    
    Internal callers can also pass a pre-determined session_id in the body
    to create a session with a specific ID (used by services/api when
    creating conversation spaces).
    """
    # Internal API key check for services/api → backend bridge
    internal_key = os.environ.get("INTERNAL_API_KEY")
    auth_header_ok = internal_key and Header(None) and True  # placeholder
    
    if USE_AUTH and not current_user:
        # Check for internal API key
        # Note: FastAPI Depends doesn't work well with optional headers in body context
        # For MVP, we use a simpler approach: check if session_id is provided in body
        # and the request comes from localhost
        pass  # Let it fall through to auth check below
    
    if USE_AUTH and not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session_id = None
    if body:
        session_id = body.get("session_id")
    
    state = await manager.create(session_id=session_id)
    return {"session_id": state.session_id}

@app.post("/sessions/{session_id}/join-voice")
async def join_voice(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a LiveKit token to join a voice session.
    Enables voice for the session and maps the participant to a speaker tag.
    """
    if USE_AUTH and not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = await manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from voice.livekit_integration import create_voice_token, next_unmapped_tag, map_speaker_tag

    participant_id = current_user.get("sub", "anon")
    participant_name = current_user.get("name", current_user.get("email", "Anonymous"))

    try:
        token_data = create_voice_token(session_id, participant_id, participant_name)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Assign this participant to the next available speaker tag
    next_tag = next_unmapped_tag(session_id)
    if next_tag is not None:
        map_speaker_tag(session_id, next_tag, participant_id)

    # ── Facilitator bot: connect backend as a LiveKit participant on first join ──
    # This allows the backend to publish TTS audio into the room
    from voice.livekit_integration import (
        get_voice_room, set_voice_room, LIVEKIT_URL as LK_URL, LIVEKIT_API_KEY as LK_KEY, LIVEKIT_API_SECRET as LK_SECRET,
    )
    from livekit import api as lkapi, rtc as lk_rtc

    if get_voice_room(session_id) is None and LK_URL:
        try:
            bot_token = (
                lkapi.AccessToken(LK_KEY, LK_SECRET)
                .with_identity(f"{session_id}_facilitator-bot")
                .with_name("Facilitator")
                .with_grants(
                    lkapi.VideoGrants(
                        room_join=True,
                        room=session_id,
                        can_publish=True,
                        can_subscribe=False,  # facilitator only speaks, doesn't listen to raw audio
                    )
                )
                .to_jwt()
            )
            bot_room = lk_rtc.Room()
            await bot_room.connect(LK_URL, bot_token)
            set_voice_room(session_id, bot_room)
            logger.info(f"[Voice] facilitator-bot connected to room {session_id}")
        except Exception as e:
            logger.warning(f"[Voice] failed to connect facilitator-bot to room {session_id}: {e}")

    return {
        "token": token_data["token"],
        "livekit_url": token_data["livekit_url"],
        "room_name": token_data["room_name"],
        "speaker_tag": next_tag,
    }

@app.get("/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    """List all sessions (for session history browser)."""
    if USE_AUTH and not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if USE_POSTGRES:
        from models import Session, Participant, async_session
        from sqlalchemy import select, func
        async with async_session() as db:
            result = await db.execute(
                select(
                    Session.session_id,
                    Session.mode,
                    Session.created_at,
                    func.count(Participant.id).label("participant_count"),
                )
                .join(Participant, Participant.session_id == Session.session_id, isouter=True)
                .group_by(Session.session_id)
                .order_by(Session.created_at.desc())
                .limit(50)
            )
            rows = result.all()
            return [
                {"session_id": r.session_id, "mode": r.mode, "created_at": r.created_at.isoformat(), "participant_count": r.participant_count}
                for r in rows
            ]
    return [
        {
            "session_id": state.session_id,
            "mode": state.mode,
            "created_at": state.created_at,
            "participant_count": len(state.participants),
        }
        for state in sorted(manager.sessions.values(), key=lambda s: s.created_at, reverse=True)
    ]

@app.get("/sessions/{session_id}/stats")
async def get_session_stats(session_id: str):
    """
    Per-session facilitation metrics for monitoring dashboard.
    Returns intervention rate, avg confidence, avg latency, safety flags.
    """
    state = await manager.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    if not USE_POSTGRES:
        return {
            "session_id": session_id,
            "mode": state.mode,
            "total_messages": len(state.utterances),
            "safety_flags": len(state.safety_flags),
            "locked": state.locked,
            "note": "Metrics require USE_POSTGRES=true",
        }
    from models import FacilitatorDecision, SafetyFlag, async_session
    from sqlalchemy import select, func, Integer
    async with async_session() as db:
        dec_result = await db.execute(
            select(
                func.count(FacilitatorDecision.id).label("total_decisions"),
                func.sum(FacilitatorDecision.should_speak.cast(Integer)).label("interventions_count"),
                func.avg(FacilitatorDecision.confidence).label("avg_confidence"),
                func.avg(FacilitatorDecision.latency_ms).label("avg_latency_ms"),
            ).where(FacilitatorDecision.session_id == session_id)
        )
        flag_result = await db.execute(
            select(func.count(SafetyFlag.id)).where(SafetyFlag.session_id == session_id)
        )
        row = dec_result.one()
        return {
            "session_id": session_id,
            "mode": state.mode,
            "total_messages": len(state.utterances),
            "total_decisions": row.total_decisions or 0,
            "interventions_count": int(row.interventions_count or 0),
            "intervention_rate": round((row.interventions_count or 0) / max(row.total_decisions or 1, 1), 2),
            "avg_confidence": round(float(row.avg_confidence or 0), 2),
            "avg_latency_ms": round(float(row.avg_latency_ms or 0)),
            "safety_flags": flag_result.scalar() or 0,
            "locked": state.locked,
        }

@app.get("/my-sessions")
async def my_sessions(current_user: dict = Depends(get_current_user)):
    """List sessions for the authenticated user."""
    if USE_AUTH and not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = current_user.get("sub") if current_user else None
    if USE_POSTGRES and user_id:
        from models import Session, Participant, async_session
        from sqlalchemy import select, func
        async with async_session() as db:
            result = await db.execute(
                select(
                    Session.session_id,
                    Session.mode,
                    Session.created_at,
                    func.count(Participant.id).label("participant_count"),
                )
                .join(Participant, Participant.session_id == Session.session_id)
                .where(Participant.user_id == user_id)
                .group_by(Session.session_id)
                .order_by(Session.created_at.desc())
                .limit(50)
            )
            rows = result.all()
            return [
                {
                    "session_id": r.session_id,
                    "mode": r.mode,
                    "created_at": r.created_at.isoformat(),
                    "participant_count": r.participant_count,
                }
                for r in rows
            ]
    return []

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    state = await manager.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    participants = await manager.get_participants(session_id)
    safety_flags = await manager.get_safety_flags(session_id)
    utterances = await manager.get_utterances(session_id)
    return {
        "session_id": state.session_id,
        "mode": state.mode,
        "created_at": state.created_at,
        "participants": [p.model_dump() for p in participants.values()],
        "participant_count": len(participants),
        "utterances": utterances,
        "utterances_count": len(utterances),
        "safety_flags": [f.model_dump() for f in safety_flags],
    }

@app.get("/health")
async def health():
    pg_status = "connected" if USE_POSTGRES else "disabled"
    try:
        if USE_POSTGRES:
            from models import async_session
            from sqlalchemy import text
            async with async_session() as db:
                await db.execute(text("SELECT 1"))
    except Exception:
        pg_status = "error"
    return {
        "status": "ok",
        "model": MINIMAX_MODEL if MINIMAX_API_KEY else LOCAL_MODEL,
        "llm": LLM_PROVIDER if (LLM_PROVIDER in ("minimax", "openai_compatible") and (MINIMAX_API_KEY if LLM_PROVIDER == "minimax" else OPENAI_API_KEY)) else "local-fallback",
        "database": "postgres" if USE_POSTGRES else "in-memory",
        "postgres": pg_status,
        "use_postgres": USE_POSTGRES,
    }

# ─── Human Escalation ─────────────────────────────────────────────────────────

@app.post("/sessions/{session_id}/escalate")
async def escalate_session(
    session_id: str,
    payload: Optional[EscalationRequest] = Body(default=None),
    triggered_by: str = "",
    reason: str = "",
):
    """Flag a session for human facilitator review."""
    state = await manager.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    requested_by = payload.triggered_by if payload else triggered_by
    requested_reason = payload.reason if payload else reason
    if USE_POSTGRES:
        from repository import SessionRepository
        from models import async_session
        async with async_session() as db:
            repo = SessionRepository(db)
            escalation = await repo.create_escalation(
                session_id,
                requested_by,
                requested_reason or "Human escalation requested",
            )
            return {"escalation_id": escalation.id, "status": escalation.status}
    return {"escalation_id": None, "status": "pending_fallback"}

@app.post("/sessions/{session_id}/review")
async def review_session(
    session_id: str,
    x_review_secret: str = Header(None),
):
    """
    Mark a locked session as reviewed and unlock it.
    Requires X-Review-Secret header matching REVIEW_SECRET env var.
    """
    import os
    review_secret = os.environ.get("REVIEW_SECRET", "")
    if review_secret and x_review_secret != review_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    state = await manager.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    await manager.unlock_session(session_id)
    # Mark all unreviewed safety flags as reviewed
    if USE_POSTGRES:
        from models import SafetyFlag, async_session
        from sqlalchemy import update
        async with async_session() as db:
            await db.execute(
                update(SafetyFlag)
                .where(SafetyFlag.session_id == session_id, SafetyFlag.reviewed_by_human.is_(False))
                .values(reviewed_by_human=True)
            )
            await db.commit()
    return {"session_id": session_id, "locked": False, "reviewed": True}

# ─── Session Debrief ──────────────────────────────────────────────────────────

async def _build_debrief(utterances: list[dict], safety_flags: list[SafetyFlag]) -> tuple[str, dict]:
    """Generate a structured debrief from session history."""
    if not utterances:
        return "No messages in this session yet.", {}

    def local_debrief() -> tuple[str, dict]:
        speakers = [u.get("speaker_name", "Unknown") for u in utterances if u.get("speaker_name")]
        topics = []
        for u in utterances[-6:]:
            text = u.get("text", "").strip()
            if text:
                topics.append(text[:48] + ("..." if len(text) > 48 else ""))
        structured = {
            "topics": topics[:4],
            "emotional_arc": "This summary is based on the local transcript and keeps to observed conversation content.",
            "unresolved_items": ["Review the latest participant concern and choose the next concrete topic."],
            "recommendations": "Pause, reflect the last message back, and ask one person to name the next specific request.",
        }
        names = ", ".join(dict.fromkeys(speakers)) or "the participants"
        return f"Local debrief for {names}: {len(utterances)} message(s) captured.", structured

    if not MINIMAX_API_KEY:
        return local_debrief()

    transcript = "\n".join(
        f"{u.get('speaker_name', 'Unknown')}: {u.get('text', '')}"
        for u in utterances
    )
    flag_summary = [
        f"[{f.level}] {f.reason} (triggered by {f.triggered_by})"
        for f in safety_flags
    ]

    DEBRIEF_PROMPT = f"""You are a relationship facilitation debrief assistant. Analyze the following session transcript and produce a structured summary.

Provide your response as a JSON block (no markdown formatting) with these exact fields:
{{
  "topics": ["topic1", "topic2", ...],
  "emotional_arc": "1-2 sentence summary of how the conversation tone evolved",
  "unresolved_items": ["item1", "item2", ...],
  "recommendations": "1-2 gentle, non-therapeutic suggestions for next steps"
}}

TRANSCRIPT:
{transcript}

SAFETY FLAGS (if any):
{chr(10).join(flag_summary) if flag_summary else "None"}

Respond with the JSON block followed by 1-2 sentences of warm, human-readable summary:"""

    messages = [{"role": "user", "content": DEBRIEF_PROMPT}]
    payload = {
        "model": MINIMAX_MODEL,
        "max_tokens": 500,
        "system": "You are a JSON-only assistant. Always respond with valid JSON first.",
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                MINIMAX_URL,
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return local_debrief()
    full_text = ""
    choices = data.get("choices", [])
    if choices:
        choice = choices[0]
        message = choice.get("message", {})
        full_text = (
            message.get("content")
            or message.get("text")
            or choice.get("text")
            or ""
        ).strip()
        if not full_text:
            msgs = choice.get("messages", [])
            for msg in reversed(msgs):
                t = msg.get("text", msg.get("content", ""))
                if t:
                    full_text = t.strip()
                    break

    if not full_text:
        return local_debrief()
    full_text = _visible_model_text(full_text)
    if not full_text:
        return local_debrief()

    # Defensive JSON extraction: find first '{' and last '}'
    structured = {}
    start = full_text.find('{')
    end = full_text.rfind('}')
    if start != -1 and end > start:
        try:
            structured = json.loads(full_text[start:end + 1])
        except json.JSONDecodeError:
            return local_debrief()
    else:
        return local_debrief()

    human_readable = full_text[full_text.rfind('}') + 1:].strip()
    fallback_summary, _fallback_structured = local_debrief()
    summary = human_readable or fallback_summary
    if not structured:
        return local_debrief()

    return summary, structured

@app.get("/sessions/{session_id}/debrief")
async def get_debrief(session_id: str):
    state = await manager.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    utterances = await manager.get_utterances(session_id)
    safety_flags = await manager.get_safety_flags(session_id)
    debrief_text, structured = await _build_debrief(utterances, safety_flags)
    return {
        "session_id": session_id,
        "text": debrief_text,
        "topics": structured.get("topics", []),
        "emotional_arc": structured.get("emotional_arc", ""),
        "unresolved_items": structured.get("unresolved_items", []),
        "recommendations": structured.get("recommendations", ""),
        "safety_flags": [f.model_dump() for f in safety_flags],
    }

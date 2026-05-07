"""
RelateFX — SQLAlchemy async models + database configuration
"""

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Boolean, Float, Integer,
    Enum as SQLEnum, Index, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

Base = declarative_base()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/relatefx"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ─── Models ──────────────────────────────────────────────────────────────────────

class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(32), primary_key=True)
    mode = Column(String(32), default="facilitation")
    last_speaker_id = Column(String(16), nullable=True)
    locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    participants = relationship("Participant", back_populates="session", cascade="all, delete-orphan")
    utterances = relationship("Utterance", back_populates="session", cascade="all, delete-orphan")
    safety_flags = relationship("SafetyFlag", back_populates="session", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="session", cascade="all, delete-orphan")
    facilitator_decisions = relationship("FacilitatorDecision", back_populates="session", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(16), primary_key=True)
    email = Column(String(256), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    name = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Participant(Base):
    __tablename__ = "participants"

    id = Column(String(16), primary_key=True)
    session_id = Column(String(32), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    role = Column(String(32), default="participant")
    emotion = Column(String(32), default="neutral")
    goals = Column(JSON, default=list)
    user_id = Column(String(16), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    session = relationship("Session", back_populates="participants")


class Utterance(Base):
    __tablename__ = "utterances"

    id = Column(String(16), primary_key=True)
    session_id = Column(String(32), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    speaker_id = Column(String(16), nullable=False)
    speaker_name = Column(String(128), default="")
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_facilitator = Column(SQLEnum("participant", "facilitator", name="speaker_type"), default="participant")

    session = relationship("Session", back_populates="utterances")

    __table_args__ = (
        Index("ix_utterances_session_timestamp", "session_id", "timestamp"),
    )


class SafetyFlag(Base):
    __tablename__ = "safety_flags"

    id = Column(String(16), primary_key=True)
    session_id = Column(String(32), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    level = Column(String(16), nullable=False)  # "low" | "medium" | "high" | "critical"
    reason = Column(Text, nullable=False)
    triggered_by = Column(String(16), nullable=False)
    is_abuse_related = Column(Boolean, default=False)
    reviewed_by_human = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="safety_flags")


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String(16), primary_key=True)
    session_id = Column(String(32), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    triggered_by = Column(String(16), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(32), default="pending")  # "pending" | "reviewed" | "resolved"
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="escalations")


class FacilitatorDecision(Base):
    __tablename__ = "facilitator_decisions"

    id = Column(String(16), primary_key=True)
    session_id = Column(String(32), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    utterance_id = Column(String(16), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    should_speak = Column(Boolean, nullable=False)
    intervention_type = Column(String(32), nullable=True)
    confidence = Column(Float, nullable=True)
    trigger_reason = Column(String(128), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    mode = Column(String(32), nullable=True)
    turn_phase = Column(String(32), nullable=True)
    conflict_pattern = Column(String(32), nullable=True)
    # Voice-specific metrics (Phase 8 — latency monitoring)
    voice_latency_ms = Column(Integer, nullable=True)      # end-to-end voice latency
    is_voice_utterance = Column(Boolean, default=False)   # true if from STT pipeline

    session = relationship("Session", back_populates="facilitator_decisions")


# ─── Helpers ───────────────────────────────────────────────────────────────────

async def init_db():
    """Create all tables. Call once on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """FastAPI dependency for an async DB session."""
    async with async_session() as session:
        yield session

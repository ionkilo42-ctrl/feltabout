"""Core Memory Service — CRUD operations and user consent flow."""

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.models.core_memory import CoreMemory, FeelFlowEvent
from app.schemas.core_memory import CreateCoreMemoryRequest, UpdateCoreMemoryRequest


# ─── Dismissed Candidates Table ───────────────────────────────────────────────

class DismissedCandidate(Base):
    """Tracks dismissed memory candidates for learning."""
    __tablename__ = "dismissed_candidates"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    candidate_key = Column(String(256), nullable=False)  # Hash of memory content
    reason = Column(String(32), default="user_dismissed")  # dismissal reason
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Core Memory Service ───────────────────────────────────────────────────────

class CoreMemoryService:
    """Service for Core Memory CRUD operations.
    
    All operations require user confirmation before saving.
    Memories are isolated by user — no shared memory in MVP 2.
    """

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        data: CreateCoreMemoryRequest,
    ) -> CoreMemory:
        """Create a user-confirmed Core Memory."""
        memory = CoreMemory(
            user_id=user_id,
            title=data.title,
            summary=data.summary,
            emotions_json=json.dumps([e.model_dump() for e in data.emotions]),
            needs=json.dumps([n.value for n in data.needs]),
            privacy=data.privacy.value,
            source_reflection_id=data.source_reflection_id,
            user_confirmed=True,  # Always True — user confirmed before creation
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        return memory

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: str) -> list[CoreMemory]:
        """List all Core Memories for a user, ordered by recency."""
        result = await db.execute(
            select(CoreMemory)
            .where(CoreMemory.user_id == user_id)
            .order_by(CoreMemory.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        memory_id: str,
        user_id: str,
    ) -> Optional[CoreMemory]:
        """Get a Core Memory by ID, verifying ownership."""
        result = await db.execute(
            select(CoreMemory)
            .where(CoreMemory.id == memory_id)
            .where(CoreMemory.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        memory: CoreMemory,
        data: UpdateCoreMemoryRequest,
    ) -> CoreMemory:
        """Update a Core Memory's fields."""
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "privacy" and value:
                setattr(memory, field, value.value)
            else:
                setattr(memory, field, value)
        
        memory.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(memory)
        return memory

    @staticmethod
    async def delete(db: AsyncSession, memory: CoreMemory) -> None:
        """Delete a Core Memory and its associated FeelFlow events."""
        await db.delete(memory)
        await db.commit()

    @staticmethod
    async def save_feel_flow_events(
        db: AsyncSession,
        user_id: str,
        reflection_id: Optional[str],
        emotions: list[dict],
    ) -> list[FeelFlowEvent]:
        """Save emotion events from a reflection to the Feel Flow timeline."""
        events = []
        for emotion_data in emotions:
            event = FeelFlowEvent(
                user_id=user_id,
                reflection_id=reflection_id,
                emotion=emotion_data.get("name", "unknown"),
                intensity=emotion_data.get("intensity", 0.5),
                source_text=emotion_data.get("source_text", ""),
                confidence_score=emotion_data.get("confidence_score", 0.0),
            )
            db.add(event)
            events.append(event)
        
        await db.commit()
        return events

    @staticmethod
    async def dismiss_candidate(
        db: AsyncSession,
        user_id: str,
        candidate_key: str,
        reason: str = "user_dismissed",
    ) -> None:
        """Record a dismissed memory candidate to prevent repeated suggestions."""
        dismissed = DismissedCandidate(
            id=uuid.uuid4().hex[:16],
            user_id=user_id,
            candidate_key=candidate_key,
            reason=reason,
        )
        db.add(dismissed)
        await db.commit()

    @staticmethod
    async def get_dismissed_candidates(
        db: AsyncSession,
        user_id: str,
    ) -> set[str]:
        """Get set of dismissed candidate keys for a user."""
        result = await db.execute(
            select(DismissedCandidate.candidate_key)
            .where(DismissedCandidate.user_id == user_id)
        )
        return set(result.scalars().all())

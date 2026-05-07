"""
RelateFX — Database-backed SessionRepository
Replaces the in-memory SessionManager with async Postgres operations.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Session, Participant, Utterance, SafetyFlag, Escalation


class SessionRepository:
    """Async Postgres implementation of session storage."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._ttl_hours = 2

    # ─── Session lifecycle ──────────────────────────────────────────────────────

    async def create(self, session_id: Optional[str] = None) -> Session:
        await self._evict_stale()
        sid = session_id or uuid.uuid4().hex[:12]
        session = Session(session_id=sid, created_at=datetime.utcnow())
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get(self, session_id: str) -> Optional[Session]:
        result = await self.db.execute(
            select(Session)
            .options(
                selectinload(Session.participants),
                selectinload(Session.utterances),
                selectinload(Session.safety_flags),
            )
            .where(Session.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def _evict_stale(self) -> None:
        cutoff = datetime.utcnow() - timedelta(hours=self._ttl_hours)
        await self.db.execute(
            delete(Session).where(Session.created_at < cutoff)
        )

    # ─── Participants ──────────────────────────────────────────────────────────

    async def add_participant(self, session_id: str, name: str) -> Participant:
        await self._evict_stale()
        p = Participant(
            id=uuid.uuid4().hex[:8],
            session_id=session_id,
            name=name,
        )
        self.db.add(p)
        await self.db.commit()
        await self.db.refresh(p)
        return p

    async def get_participant(self, session_id: str, participant_id: str) -> Optional[Participant]:
        result = await self.db.execute(
            select(Participant).where(
                and_(
                    Participant.session_id == session_id,
                    Participant.id == participant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_other_participant(self, session_id: str, exclude_id: str) -> Optional[Participant]:
        result = await self.db.execute(
            select(Participant).where(
                and_(
                    Participant.session_id == session_id,
                    Participant.id != exclude_id,
                )
            )
        )
        return result.scalar_one_or_none()

    # ─── Utterances ────────────────────────────────────────────────────────────

    async def add_utterance(
        self,
        session_id: str,
        speaker_id: str,
        speaker_name: str,
        text: str,
        is_facilitator: bool = False,
    ) -> Utterance:
        u = Utterance(
            id=uuid.uuid4().hex[:8],
            session_id=session_id,
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            text=text,
            timestamp=datetime.utcnow(),
            is_facilitator="facilitator" if is_facilitator else "participant",
        )
        self.db.add(u)
        await self.db.commit()
        await self.db.refresh(u)
        return u

    async def get_utterances(self, session_id: str) -> list[Utterance]:
        result = await self.db.execute(
            select(Utterance)
            .where(Utterance.session_id == session_id)
            .order_by(Utterance.timestamp)
        )
        return list(result.scalars().all())

    # ─── Safety flags ──────────────────────────────────────────────────────────

    async def add_safety_flag(
        self,
        session_id: str,
        level: str,
        reason: str,
        triggered_by: str,
    ) -> SafetyFlag:
        f = SafetyFlag(
            id=uuid.uuid4().hex[:8],
            session_id=session_id,
            level=level,
            reason=reason,
            triggered_by=triggered_by,
        )
        self.db.add(f)
        await self.db.commit()
        await self.db.refresh(f)
        return f

    async def get_safety_flags(self, session_id: str) -> list[SafetyFlag]:
        result = await self.db.execute(
            select(SafetyFlag)
            .where(SafetyFlag.session_id == session_id)
            .order_by(SafetyFlag.created_at)
        )
        return list(result.scalars().all())

    # ─── Mode ──────────────────────────────────────────────────────────────────

    async def set_mode(self, session_id: str, mode: str) -> None:
        result = await self.db.execute(
            select(Session).where(Session.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.mode = mode
            session.updated_at = datetime.utcnow()
            await self.db.commit()

    # ─── Escalations ───────────────────────────────────────────────────────────

    async def create_escalation(
        self,
        session_id: str,
        triggered_by: str,
        reason: str,
    ) -> Escalation:
        e = Escalation(
            id=uuid.uuid4().hex[:8],
            session_id=session_id,
            triggered_by=triggered_by,
            reason=reason,
            status="pending",
        )
        self.db.add(e)
        await self.db.commit()
        await self.db.refresh(e)
        return e

    async def get_escalations(self, session_id: str) -> list[Escalation]:
        result = await self.db.execute(
            select(Escalation)
            .where(Escalation.session_id == session_id)
            .order_by(Escalation.created_at)
        )
        return list(result.scalars().all())

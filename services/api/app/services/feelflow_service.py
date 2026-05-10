"""FeelFlow Service — emotion timeline and summary data."""

from collections import Counter
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core_memory import FeelFlowEvent


class FeelFlowService:
    """Service for FeelFlow emotion tracking and timeline."""

    @staticmethod
    async def save_events(
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
    async def get_timeline(
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
    ) -> list[FeelFlowEvent]:
        """Get recent emotion events for a user's timeline."""
        result = await db.execute(
            select(FeelFlowEvent)
            .where(FeelFlowEvent.user_id == user_id)
            .order_by(FeelFlowEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        user_id: str,
        days: int = 30,
    ) -> dict:
        """Get emotion distribution summary over time.
        
        Returns emotion counts without clinical interpretation.
        Tone remains calm, practical, non-judgmental.
        """
        from datetime import datetime, timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(FeelFlowEvent.emotion, func.count(FeelFlowEvent.id))
            .where(FeelFlowEvent.user_id == user_id)
            .where(FeelFlowEvent.created_at >= cutoff)
            .group_by(FeelFlowEvent.emotion)
        )
        
        emotion_counts = {}
        for emotion, count in result.all():
            emotion_counts[emotion] = count
        
        # Calculate total events and intensity stats
        total_result = await db.execute(
            select(
                func.count(FeelFlowEvent.id),
                func.avg(FeelFlowEvent.intensity),
            )
            .where(FeelFlowEvent.user_id == user_id)
            .where(FeelFlowEvent.created_at >= cutoff)
        )
        row = total_result.one()
        total_events = row[0] or 0
        avg_intensity = float(row[1]) if row[1] else 0.0
        
        return {
            "emotion_counts": emotion_counts,
            "total_events": total_events,
            "avg_intensity": round(avg_intensity, 2),
            "period_days": days,
        }

    @staticmethod
    async def get_events_by_reflection(
        db: AsyncSession,
        user_id: str,
        reflection_id: str,
    ) -> list[FeelFlowEvent]:
        """Get emotion events for a specific reflection."""
        result = await db.execute(
            select(FeelFlowEvent)
            .where(FeelFlowEvent.user_id == user_id)
            .where(FeelFlowEvent.reflection_id == reflection_id)
            .order_by(FeelFlowEvent.created_at.asc())
        )
        return list(result.scalars().all())

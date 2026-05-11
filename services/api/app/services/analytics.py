"""
Lightweight analytics service for Phase 1E.

Tracks aggregate metrics WITHOUT logging raw emotional data.
All functions are privacy-safe by design.
"""

from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.v2 import EmotionalMemory, Entity, Need, Feeling
from app.models.user import User


class AnalyticsService:
    """Privacy-safe analytics for internal observability."""

    def __init__(self, db: Session):
        self.db = db

    def get_extraction_stats(self) -> dict:
        """Count extractions by safety status (no text)."""
        total_memories = self.db.query(EmotionalMemory).count()
        
        # Count entities and needs created
        total_entities = self.db.query(Entity).count()
        total_needs = self.db.query(Need).count()
        
        return {
            "total_memories": total_memories,
            "total_entities": total_entities,
            "total_needs": total_needs,
        }

    def get_save_stats(self) -> dict:
        """Count saves/confirmations by time period."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        saves_this_week = self.db.query(EmotionalMemory).filter(
            EmotionalMemory.created_at >= week_ago
        ).count()
        
        saves_this_month = self.db.query(EmotionalMemory).filter(
            EmotionalMemory.created_at >= month_ago
        ).count()
        
        return {
            "saves_this_week": saves_this_week,
            "saves_this_month": saves_this_month,
        }

    def get_safety_stats(self) -> dict:
        """
        Estimate safety flag frequency.
        We don't persist flagged responses, but we can track
        if the safety classifier was invoked.
        """
        # This would require incrementing a counter when safety check runs
        # For now, return placeholder - would need instrumentation
        return {
            "safety_checks_total": 0,  # Requires instrumentation
            "safety_flags_total": 0,   # Requires instrumentation
            "note": "Safety stats require instrumentation in safety service",
        }

    def get_api_failure_stats(self) -> dict:
        """Track API failures (no sensitive data)."""
        # This would require logging at the router level
        return {
            "api_failures_total": 0,  # Requires logging instrumentation
            "note": "API failure stats require logging instrumentation",
        }

    def get_user_stats(self) -> dict:
        """User count and activity stats."""
        total_users = self.db.query(User).count()
        active_users_week = self.db.query(User).join(EmotionalMemory).filter(
            EmotionalMemory.created_at >= datetime.utcnow() - timedelta(days=7)
        ).distinct().count()
        
        return {
            "total_users": total_users,
            "active_users_this_week": active_users_week,
        }

    def get_full_stats(self) -> dict:
        """Return all analytics in one call."""
        return {
            "extractions": self.get_extraction_stats(),
            "saves": self.get_save_stats(),
            "safety": self.get_safety_stats(),
            "api_failures": self.get_api_failure_stats(),
            "users": self.get_user_stats(),
            "generated_at": datetime.utcnow().isoformat(),
        }


def get_analytics(db: Session) -> AnalyticsService:
    """Factory function for dependency injection."""
    return AnalyticsService(db)
"""FeelFlow schemas for user-facing API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FeelFlowEventResponse(BaseModel):
    """Single emotion event in the timeline."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    reflection_id: Optional[str] = None
    emotion: str
    intensity: float
    source_text: str
    confidence_score: float
    created_at: datetime


class FeelFlowTimelineResponse(BaseModel):
    """Timeline of recent emotion events."""
    events: list[FeelFlowEventResponse]
    total: int
    limit: int


class FeelFlowSummaryResponse(BaseModel):
    """Emotion distribution summary over time.
    
    Returns raw emotion counts only — no clinical interpretation.
    Tone remains calm, practical, non-judgmental.
    """
    emotion_counts: dict[str, int]  # emotion name -> count
    total_events: int
    avg_intensity: float
    period_days: int


class FeelFlowReflectionEventsResponse(BaseModel):
    """Emotion events for a specific reflection."""
    reflection_id: str
    events: list[FeelFlowEventResponse]
    total: int

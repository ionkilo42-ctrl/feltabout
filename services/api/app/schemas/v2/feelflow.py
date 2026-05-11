"""Pydantic schemas for FeelFlow and FeelMap analytics."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FeelFlowQuery(BaseModel):
    """Query parameters for feel-flow endpoint."""
    entity_id: Optional[str] = None
    time_bucket: str = Field(default="day")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class FeelFlowDataPoint(BaseModel):
    """Single data point in feel-flow time series."""
    date: str
    joy: float = 0
    sadness: float = 0
    anger: float = 0
    fear: float = 0
    disgust: float = 0


class FeelFlowResponse(BaseModel):
    """FeelFlow time series response."""
    data: List[FeelFlowDataPoint]
    time_bucket: str
    emotion_totals: dict  # {"joy": total, "sadness": total, ...}
    average_intensity: float


class FeelMapEmotionGroup(BaseModel):
    """Emotion group in feel-map treemap."""
    emotion: str
    color: str
    total_weight: float
    feelings: List["FeelMapFeeling"]


class FeelMapFeeling(BaseModel):
    """Feeling in feel-map."""
    label: str
    weight: float
    about: str
    intensity: float


class FeelMapResponse(BaseModel):
    """FeelMap composition response."""
    emotion_groups: List[FeelMapEmotionGroup]
    dominant_emotion: str
    total_feelings: int
    average_intensity: float


# Forward refs for nested types
FeelMapEmotionGroup.model_rebuild()
"""Pydantic schemas for Topic model."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.v2.feeling import FeelingResponse


class TopicResponse(BaseModel):
    """Schema for topic response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    title: str
    description: str
    is_public_topic: bool
    created_at: datetime


class TopicWithRelations(TopicResponse):
    """Topic with related feelings."""
    feelings: List[FeelingResponse] = Field(default_factory=list)
    feelings_count: int = Field(default=0)
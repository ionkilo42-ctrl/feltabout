"""Pydantic schemas for Entity model."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.v2.feeling import FeelingResponse


class EntityResponse(BaseModel):
    """Schema for entity response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    canonical_name: str
    user_id: Optional[str]
    entity_type: str
    privacy_level: str
    is_connection: bool
    created_at: datetime


class EntityWithRelations(EntityResponse):
    """Entity with related feelings, needs, topics."""
    feelings: List[FeelingResponse] = Field(default_factory=list)
    needs_count: int = Field(default=0)
    topics_count: int = Field(default=0)
    memories_count: int = Field(default=0)
"""Pydantic schemas for Need model."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.v2.feeling import FeelingResponse


class NeedResponse(BaseModel):
    """Schema for need response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    name: str
    description: str
    created_at: datetime


class NeedWithRelations(NeedResponse):
    """Need with related feelings."""
    feelings: List[FeelingResponse] = Field(default_factory=list)
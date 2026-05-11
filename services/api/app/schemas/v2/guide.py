"""Pydantic schemas for Guide model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GuideCreate(BaseModel):
    """Schema for creating a guide."""
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., description="Guide name like 'Aimee', 'Coach'")
    tone: str = Field(default="warm")
    warmth_level: float = Field(default=7.0, ge=1, le=10)
    directness_level: float = Field(default=5.0, ge=1, le=10)
    personality_description: str = Field(default="")
    belief_adaptation_enabled: bool = Field(default=True)


class GuideResponse(BaseModel):
    """Schema for guide response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    name: str
    tone: str
    warmth_level: float
    directness_level: float
    personality_description: str
    belief_adaptation_enabled: bool
    created_at: datetime
    updated_at: datetime
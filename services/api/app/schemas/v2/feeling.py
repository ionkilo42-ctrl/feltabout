"""Pydantic schemas for Feeling model."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class FeelingNeedResponse(BaseModel):
    """Need within a feeling response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    name: str
    description: str
    created_at: datetime


class FeelingEntityResponse(BaseModel):
    """Entity within a feeling response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    canonical_name: str
    user_id: Optional[str]
    entity_type: str
    privacy_level: str
    is_connection: bool
    created_at: datetime


class FeelingTopicResponse(BaseModel):
    """Topic within a feeling response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    title: str
    description: str
    is_public_topic: bool
    created_at: datetime


class FeelingCreate(BaseModel):
    """Schema for creating a feeling."""
    model_config = ConfigDict(extra="forbid")
    
    primary_emotion: str = Field(..., description="One of: joy, sadness, anger, fear, disgust")
    label: str = Field(..., description="User-facing label like 'frustrated', 'hurt', 'anxious'")
    intensity: float = Field(..., ge=1, le=10, description="Intensity from 1-10")
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_text: str = Field(default="")
    occurred_at: Optional[datetime] = None
    
    # Relationships (can be created with or without IDs)
    need_ids: List[str] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    topic_ids: List[str] = Field(default_factory=list)


class FeelingResponse(BaseModel):
    """Schema for feeling response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    primary_emotion: str
    label: str
    intensity: float
    confidence: float
    source_text: str
    memory_id: Optional[str]
    occurred_at: datetime
    created_at: datetime


class FeelingWithRelations(FeelingResponse):
    """Feeling with related needs, entities, topics."""
    needs: List[FeelingNeedResponse] = Field(default_factory=list)
    entities: List[FeelingEntityResponse] = Field(default_factory=list)
    topics: List[FeelingTopicResponse] = Field(default_factory=list)
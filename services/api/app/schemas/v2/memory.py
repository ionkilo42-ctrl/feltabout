"""Pydantic schemas for Memory model."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class CreateFeelingInput(BaseModel):
    """Nested feeling within memory creation."""
    model_config = ConfigDict(extra="forbid")
    
    primary_emotion: str
    label: str
    intensity: float = Field(..., ge=1, le=10)
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_text: str = Field(default="")
    occurred_at: Optional[datetime] = None


class CreateMemoryRequest(BaseModel):
    """Schema for creating a memory with nested objects."""
    model_config = ConfigDict(extra="forbid")
    
    title: str = Field(..., description="Memory title")
    narrative: str = Field(default="", description="Original story/context")
    ai_summary: str = Field(default="", description="AI-generated summary")
    occurred_at: Optional[datetime] = None
    privacy_level: str = Field(default="private")
    
    # Nested objects
    feelings: List[CreateFeelingInput] = Field(default_factory=list)
    need_names: List[str] = Field(default_factory=list, description="Need names to create/link")
    entity_names: List[str] = Field(default_factory=list, description="Entity names to create/link")
    topic_titles: List[str] = Field(default_factory=list, description="Topic titles to create/link")


class MemoryResponse(BaseModel):
    """Schema for memory response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    title: str
    narrative: str
    ai_summary: str
    occurred_at: datetime
    privacy_level: str
    created_at: datetime
    updated_at: datetime


# Import nested response types here to avoid circular imports
from app.schemas.v2.feeling import FeelingWithRelations
from app.schemas.v2.need import NeedResponse
from app.schemas.v2.entity import EntityResponse
from app.schemas.v2.topic import TopicResponse


class MemoryWithRelations(MemoryResponse):
    """Memory with related feelings."""
    feelings: List[FeelingWithRelations] = Field(default_factory=list)


class NestedMemoryResponse(BaseModel):
    """Full memory response with all nested relationships."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    title: str
    narrative: str
    ai_summary: str
    occurred_at: datetime
    privacy_level: str
    created_at: datetime
    updated_at: datetime
    
    # Full nested objects
    feelings: List[FeelingWithRelations] = Field(default_factory=list)
    needs: List[NeedResponse] = Field(default_factory=list)
    entities: List[EntityResponse] = Field(default_factory=list)
    topics: List[TopicResponse] = Field(default_factory=list)
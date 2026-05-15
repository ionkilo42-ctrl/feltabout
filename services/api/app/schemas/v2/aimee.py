"""Aimee extraction schemas for v2 emotional graph.

Aimee proposes emotional meaning from free-form text.
User confirms. Only confirmed data gets saved.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NeedStatus(str, Enum):
    """Status of need identification."""
    IDENTIFIED = "identified"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"


class PrimaryEmotion(str, Enum):
    """Valid primary emotions for extraction."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    DISGUST = "disgust"


# ─── Extraction Request/Response ───────────────────────────────────────────────

class ExtractionRequest(BaseModel):
    """Request for Aimee to extract emotional meaning from text."""
    model_config = ConfigDict(extra="forbid")
    
    text: str = Field(..., min_length=1, description="User's free-form text to analyze")


class ExtractedEntity(BaseModel):
    """Entity identified in the text."""
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(default="person", description="Type: person, company, etc.")


class ExtractedTopic(BaseModel):
    """Topic/theme identified in the text."""
    model_config = ConfigDict(extra="forbid")
    
    title: str = Field(..., description="Topic title")


class ExtractedNeed(BaseModel):
    """Need identified in the text (NVC framework)."""
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., description="Need name")
    status: NeedStatus = Field(default=NeedStatus.IDENTIFIED, description="Need status")


class ExtractedFeeling(BaseModel):
    """A single feeling extracted from text."""
    model_config = ConfigDict(extra="forbid")
    
    primary_emotion: PrimaryEmotion = Field(..., description="One of: joy, sadness, anger, fear, disgust")
    label: str = Field(..., description="User-facing label like 'frustrated', 'hurt', 'anxious'")
    intensity: float = Field(..., ge=1, le=10, description="Intensity from 1-10")
    confidence: float = Field(default=0.8, ge=0, le=1)
    entities: List[ExtractedEntity] = Field(default_factory=list)
    topics: List[ExtractedTopic] = Field(default_factory=list)
    needs: List[ExtractedNeed] = Field(default_factory=list)
    
    @field_validator('primary_emotion', mode='before')
    @classmethod
    def validate_emotion(cls, v):
        if isinstance(v, str):
            v = v.lower().strip()
            valid = {"joy", "sadness", "anger", "fear", "disgust"}
            if v not in valid:
                raise ValueError(f"Primary emotion must be one of: {valid}")
        return v


class ExtractionResponse(BaseModel):
    """Response from Aimee extraction."""
    model_config = ConfigDict(extra="forbid")
    
    feelings: List[ExtractedFeeling] = Field(default_factory=list, description="Extracted feelings")
    suggested_memory_title: str = Field(..., description="Suggested title for the memory")
    suggested_response: str = Field(..., description="Aimee's empathetic response")
    safety_status: Literal["safe", "flagged"] = Field(default="safe", description="Safety check result")


# ─── Confirmation Request/Response ────────────────────────────────────────────

class ConfirmedFeeling(BaseModel):
    """User-confirmed feeling to save."""
    model_config = ConfigDict(extra="forbid")
    
    primary_emotion: PrimaryEmotion
    label: str
    intensity: float = Field(..., ge=1, le=10)
    confidence: float = Field(default=0.8, ge=0, le=1)
    source_text: str = Field(default="")
    
    # Confirmed entity names (will be created/linked)
    entity_names: List[str] = Field(default_factory=list)
    
    # Confirmed topic titles (will be created/linked)
    topic_titles: List[str] = Field(default_factory=list)
    
    # Confirmed need names (will be created/linked)
    need_names: List[str] = Field(default_factory=list)
    
    occurred_at: Optional[datetime] = None


class ConfirmRequest(BaseModel):
    """Request to save confirmed extraction to emotional graph."""
    model_config = ConfigDict(extra="forbid")
    
    source_text: str = Field(..., description="Original user text")
    memory_title: str = Field(..., description="User-confirmed memory title")
    memory_narrative: str = Field(default="", description="Memory narrative")
    occurred_at: Optional[datetime] = None
    feelings: List[ConfirmedFeeling] = Field(..., min_length=1, description="Confirmed feelings to save")


class ConfirmResponse(BaseModel):
    """Response from confirm endpoint."""
    model_config = ConfigDict(from_attributes=True)
    
    memory_id: str = Field(..., description="ID of created memory")
    feelings_count: int = Field(..., description="Number of feelings saved")
    status: str = Field(default="saved", description="Save status")


# ─── Chat Request/Response ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request for free-form conversational chat with Aimee."""
    model_config = ConfigDict(extra="forbid")
    
    message: str = Field(..., min_length=1, description="User's message")
    conversation_context: Optional[str] = Field(
        default=None,
        description="Recent conversation history for context"
    )
    participant_context: Optional[str] = Field(
        default=None,
        description="Information about session participants for shared session context"
    )


class ChatResponse(BaseModel):
    """Response from Aimee conversational chat."""
    model_config = ConfigDict(extra="forbid")
    
    reply: str = Field(..., description="Aimee's conversational reply")
    safety_status: Literal["safe", "flagged"] = Field(default="safe", description="Safety check result")
    should_offer_review: bool = Field(
        default=False,
        description="True when the user appears done and the UI should offer review/save",
    )

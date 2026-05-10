"""Core Memory schemas for user-facing API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.emotional_analysis import EmotionSignal, MemoryCandidate, NeedCategory, PrivacyLevel


# ─── Request Schemas ─────────────────────────────────────────────────────────

class CreateCoreMemoryRequest(BaseModel):
    """Request to create a Core Memory from a candidate."""
    model_config = ConfigDict(extra="forbid")

    title: str
    summary: str
    emotions: list[EmotionSignal] = []
    needs: list[NeedCategory] = []
    privacy: PrivacyLevel = PrivacyLevel.PRIVATE
    source_reflection_id: Optional[str] = None


class UpdateCoreMemoryRequest(BaseModel):
    """Request to update a Core Memory."""
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    summary: Optional[str] = None
    privacy: Optional[PrivacyLevel] = None


# ─── Response Schemas ─────────────────────────────────────────────────────────

class CoreMemoryResponse(BaseModel):
    """Response schema for Core Memory."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    summary: str
    emotions_json: str  # JSON string of EmotionSignal list
    needs: str  # JSON string of NeedCategory list
    privacy: str  # "private" or "shared"
    source_reflection_id: Optional[str] = None
    user_confirmed: bool = True
    created_at: datetime
    updated_at: datetime


class CoreMemoryListResponse(BaseModel):
    """Response schema for list of Core Memories."""
    model_config = ConfigDict(from_attributes=True)

    memories: list[CoreMemoryResponse]
    total: int


# ─── Memory Suggestion (from analysis) ───────────────────────────────────────

class MemorySuggestionRequest(BaseModel):
    """Request to convert a MemoryCandidate to saveable memory."""
    model_config = ConfigDict(extra="forbid")

    candidate: MemoryCandidate
    reflection_id: str
    user_title: Optional[str] = None
    user_summary: Optional[str] = None


class MemorySuggestionResponse(BaseModel):
    """User-facing memory suggestion from AI analysis."""
    title: str
    summary: str
    emotions_preview: list[str]  # Just emotion names, not full objects
    needs_preview: list[str]  # Just need names
    reason: str  # Human-readable explanation
    privacy_default: PrivacyLevel = PrivacyLevel.PRIVATE


# ─── Core Memory + Emotion Distribution (for GenerateResponse) ─────────────────

class CoreMemorySummary(BaseModel):
    """Minimal memory info for mobile display."""
    id: str
    title: str


class CoreMemorySuggestionResponse(BaseModel):
    """Memory suggestion to include in GenerateResponse."""
    title: str
    summary: str
    reason: str

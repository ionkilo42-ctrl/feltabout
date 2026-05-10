"""Pydantic schemas for reflection API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CreateReflectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    situation: str = ""
    feelings: str = ""
    interpretation: str = ""
    needs: str = ""
    fears: str = ""
    desired_outcome: str = ""
    message_draft: str = ""


class UpdateReflectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    situation: Optional[str] = None
    feelings: Optional[str] = None
    interpretation: Optional[str] = None
    needs: Optional[str] = None
    fears: Optional[str] = None
    desired_outcome: Optional[str] = None
    message_draft: Optional[str] = None
    status: Optional[str] = None


class GeneratePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reflection_id: str


class ReflectionOutputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reflection_id: str
    emotional_summary: str
    needs_summary: str
    assumptions: str
    reframe: str
    avoid_saying: str
    conversation_opener: str
    followup_questions: str
    repair_statement: str
    created_at: datetime


class ReflectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    situation: str
    feelings: str
    interpretation: str
    needs: str
    fears: str
    desired_outcome: str
    message_draft: str
    status: str
    created_at: datetime
    updated_at: datetime
    output: Optional[ReflectionOutputResponse] = None


class MemorySuggestionData(BaseModel):
    """Memory suggestion from AI analysis — user can save or dismiss."""
    title: str
    summary: str
    reason: str
    reflection_id: str


class GenerateResponse(BaseModel):
    is_crisis: bool
    severity: str
    message: str
    resources: list[str]
    output: Optional[ReflectionOutputResponse] = None
    memory_suggestion: Optional[MemorySuggestionData] = None


# ─── Feedback Schemas ──────────────────────────────────────────────────────────

class CreateFeedbackRequest(BaseModel):
    """
    Feedback request after viewing a conversation plan.
    
    Questions:
    1. Do you feel more prepared for the conversation?
    2. Do you feel less reactive than before?
    3. What was most helpful? (optional)
    
    Scores: 1=No, 2=Somewhat, 3=Yes
    """
    model_config = ConfigDict(extra="forbid")
    
    prepared_score: int
    less_reactive_score: int
    helpful_text: str = ""


class ReflectionFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    reflection_id: str
    user_id: str
    prepared_score: int
    less_reactive_score: int
    helpful_text: str
    conversation_went_better: int
    created_at: datetime


class UpdateFeedbackRequest(BaseModel):
    """Update feedback — used for the follow-up question after the conversation."""
    model_config = ConfigDict(extra="forbid")
    
    conversation_went_better: Optional[int] = None


ReflectionResponse.model_rebuild()

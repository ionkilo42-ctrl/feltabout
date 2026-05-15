"""Pydantic schemas for Guide Me session API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ─── Enums ────────────────────────────────────────────────────────────────────

class GuideStage(str, Enum):
    """All Guide Me conversation stages.

    Stages advance in order. Aimee stays in a stage until the user
    provides usable input, then advances. Users can go back.
    """
    SAFE_OPENING = "safe_opening"
    FIRST_EXPRESSION = "first_expression"
    FEELING_IDENTIFICATION = "feeling_identification"
    INTENSITY_CAPTURE = "intensity_capture"
    VALIDATION = "validation"
    ABOUT_MAPPING = "about_mapping"
    MEMORY_DISCOVERY = "memory_discovery"
    MEANING_DISCOVERY = "meaning_discovery"
    NEED_DISCOVERY = "need_discovery"
    PURPOSE_OF_FEELING = "purpose_of_feeling"
    CONSTRUCTIVE_PATH = "constructive_path"
    REFLECTION_REVIEW = "reflection_review"
    SAVE_OR_SIGNUP = "save_or_signup"


# ─── Conversation Message ─────────────────────────────────────────────────────

class ConversationMessage(BaseModel):
    speaker: str  # "aimee" | "user"
    text: str
    ts: str  # ISO datetime string


# ─── Collected Feeling ────────────────────────────────────────────────────────

class CollectedFeeling(BaseModel):
    name: str
    intensity: float  # 1-10
    validated: bool = False


# ─── Collected About Link ─────────────────────────────────────────────────────

class AboutLinkType(str, Enum):
    ENTITY = "entity"
    TOPIC = "topic"
    EVENT = "event"


class CollectedAboutLink(BaseModel):
    type: AboutLinkType
    label: str


# ─── Collected Need ────────────────────────────────────────────────────────────

class CollectedNeed(BaseModel):
    category: str
    text: str  # How the user expressed this need


# ─── Reflection Card ───────────────────────────────────────────────────────────

class ReflectionCardFeelings(BaseModel):
    name: str
    intensity: float  # 1-10


class ReflectionCardAboutLinks(BaseModel):
    type: str
    label: str


class ReflectionCard(BaseModel):
    """The full reflection card output from Guide Me.

    Contains all fields the user reviews and verifies before saving.
    """
    title: str
    feelings: list[ReflectionCardFeelings]
    about_links: list[ReflectionCardAboutLinks]
    needs: list[str]
    memory_summary: str
    purpose_of_feeling: str
    constructive_path: str
    suggested_words: list[str]  # Including simple_opener


# ─── API Schemas ───────────────────────────────────────────────────────────────

class CreateGuideSessionRequest(BaseModel):
    """Request to start a new Guide Me session."""
    model_config = ConfigDict(extra="forbid")

    # Optional: user-supplied title for the session
    title: Optional[str] = None


class GuideSessionResponse(BaseModel):
    """Full guide session state (for GET)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: str
    current_stage: str
    conversation_history: list[ConversationMessage]
    collected_feelings: list[CollectedFeeling]
    collected_about_links: list[CollectedAboutLink]
    collected_needs: list[CollectedNeed]
    collected_context: dict
    reflection_card: Optional[ReflectionCard] = None
    created_at: datetime
    updated_at: datetime


class AimeeReplyResponse(BaseModel):
    """Response after sending a message in Guide Me.

    Returns Aimee's reply and updated session state.
    """
    reply: str  # Aimee's conversational response
    session: GuideSessionResponse
    stage_advanced: bool  # Whether we moved to a new stage
    new_stage: Optional[str] = None  # Name of new stage if advanced
    is_crisis: bool = False  # True if safety check triggered
    safety_resources: list[str] = []  # Crisis resources if is_crisis=True


class GenerateCardResponse(BaseModel):
    """Response after generating a Reflection Card."""
    card: ReflectionCard
    session: GuideSessionResponse


class UpdateCardRequest(BaseModel):
    """Request to edit the Reflection Card before saving."""
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    feelings: Optional[list[ReflectionCardFeelings]] = None
    about_links: Optional[list[ReflectionCardAboutLinks]] = None
    needs: Optional[list[str]] = None
    memory_summary: Optional[str] = None
    purpose_of_feeling: Optional[str] = None
    constructive_path: Optional[str] = None
    suggested_words: Optional[list[str]] = None


class SaveSessionRequest(BaseModel):
    """Request to save the verified Reflection Card as a Reflection."""
    model_config = ConfigDict(extra="forbid")

    # Whether to save or skip saving (for save_or_signup stage)
    save: bool = True
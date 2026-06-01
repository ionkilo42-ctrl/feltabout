"""Guide Session model for structured Guide Me reflection flow."""

from datetime import datetime
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Column
from sqlalchemy.orm import relationship

from app.models.base import Base


class GuideSession(Base):
    """A single Guide Me conversation session.

    Tracks Aimee's stage-by-stage guided reflection. Each session goes through
    these stages: safe_opening → first_expression → feeling_identification →
    intensity_capture → validation → about_mapping → memory_discovery →
    meaning_discovery → need_discovery → purpose_of_feeling →
    constructive_path → reflection_review → save_or_signup

    The conversation_history stores the full message thread for audit/debug.
    collected_* fields accumulate data through each stage.
    reflection_card is null until generate-card is called.
    """
    __tablename__ = "guide_sessions"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Session state
    status = Column(String(32), default="active")  # active | completed | abandoned
    current_stage = Column(String(48), default="safe_opening")

    # Full message log (speaker + text + timestamp)
    # [{'speaker': 'aimee' | 'user', 'text': str, 'ts': str}]
    conversation_history = Column(Text, default="[]")

    # Stage-gated data collection
    # Feelings: [{'name': str, 'intensity': float, 'validated': bool}]
    collected_feelings = Column(Text, default="[]")
    # About links: [{'type': 'entity' | 'topic' | 'event', 'label': str}]
    collected_about_links = Column(Text, default="[]")
    # Needs: [{'category': str, 'text': str}]
    collected_needs = Column(Text, default="[]")

    # Other collected context
    # Free-form notes Aimee gathers at various stages
    collected_context = Column(Text, default="{}")

    # The generated Reflection Card (null until generate-card called)
    # Full ReflectionCard structure as JSON string
    reflection_card = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="guide_sessions")


# ─── Reverse relationship on User ─────────────────────────────────────────────

from app.models.user import User  # noqa: E402, F401

User.guide_sessions = relationship(
    "GuideSession",
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="selectin",
)
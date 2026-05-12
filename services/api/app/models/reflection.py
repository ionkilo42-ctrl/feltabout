"""Reflection models for feltabout."""

from datetime import datetime
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Column, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base


class Reflection(Base):
    __tablename__ = "reflections"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(256), default="")
    situation = Column(Text, default="")
    feelings = Column(Text, default="")
    interpretation = Column(Text, default="")  # "What story are you telling yourself?"
    needs = Column(Text, default="")
    fears = Column(Text, default="")
    desired_outcome = Column(Text, default="")
    message_draft = Column(Text, default="")
    status = Column(String(32), default="draft")  # draft | completed | archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="reflections")
    output = relationship(
        "ReflectionOutput",
        back_populates="reflection",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    safety_events = relationship("SafetyEvent", back_populates="reflection", cascade="all, delete-orphan")
    feedback = relationship(
        "ReflectionFeedback",
        back_populates="reflection",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ReflectionOutput(Base):
    __tablename__ = "reflection_outputs"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    reflection_id = Column(String(36), ForeignKey("reflections.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Primary output: one clear thing to say
    simple_opener = Column(Text, default="")

    # Full analysis (internal/hidden from primary view)
    emotional_summary = Column(Text, default="")
    needs_summary = Column(Text, default="")
    assumptions = Column(Text, default="")
    reframe = Column(Text, default="")
    avoid_saying = Column(Text, default="")
    conversation_opener = Column(Text, default="")
    followup_questions = Column(Text, default="")
    repair_statement = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Generation metadata — enables outcome comparison by version
    prompt_version = Column(String(64), default="facilitation_mvp1_v1")
    model_provider = Column(String(32), default="openai")
    model_name = Column(String(64), default="gpt-4o-mini")
    generation_mode = Column(String(32), default="single_call_plan")
    safety_version = Column(String(32), default="safety_rules_v1")
    
    # Human review status for internal quality review loop
    # Values: pending_review | approved | flagged | excellent | needs_prompt_revision
    human_review_status = Column(String(32), default="pending_review")

    reflection = relationship("Reflection", back_populates="output")


class ReflectionFeedback(Base):
    """
    User feedback on conversation plan effectiveness.
    
    Tracks whether feltabout actually helped the user prepare for their conversation.
    This is the primary MVP 1 product telemetry signal.
    """
    __tablename__ = "reflection_feedback"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    reflection_id = Column(String(36), ForeignKey("reflections.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # prepared_score: 1=No, 2=Somewhat, 3=Yes
    prepared_score = Column(Integer, nullable=False)
    
    # less_reactive_score: 1=No, 2=Somewhat, 3=Yes
    less_reactive_score = Column(Integer, nullable=False)
    
    # Optional free text about what was most helpful
    helpful_text = Column(Text, default="")
    
    # Follow-up question: did the actual conversation go better?
    # 0 = not answered yet (user hasn't had the conversation), 1=No, 2=Somewhat, 3=Yes
    conversation_went_better = Column(Integer, default=0)
    
    # New: "How did it go?" after the conversation
    # 1=Better than expected, 2=About the same, 3=Worse, 4=Didn't have it
    how_did_it_go = Column(Integer, nullable=True)

    # Follow-up text describing what happened
    what_happened = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)

    reflection = relationship("Reflection", back_populates="feedback")


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reflection_id = Column(String(36), ForeignKey("reflections.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False)  # low | medium | high | critical
    model_response = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    reflection = relationship("Reflection", back_populates="safety_events")

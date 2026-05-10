"""Core Memory and FeelFlow models for emotional intelligence."""

from datetime import datetime
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Column, Float, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base


class CoreMemory(Base):
    """
    A Core Memory is a significant emotional event that the user chooses to save
    and remember for future conversations.
    
    Core Memories are the IFS "parts" system integration. They capture emotionally
    significant events that may affect future communication patterns.
    """
    __tablename__ = "core_memories"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    title = Column(String(256), nullable=False)
    summary = Column(Text, default="")
    
    # Emotional data — stored as JSON strings for flexibility
    emotions_json = Column(Text, default="[]")  # JSON array of EmotionSignal
    needs = Column(Text, default="[]")  # JSON array of NeedCategory
    
    # Privacy and source
    privacy = Column(String(16), default="private")  # "private" or "shared"
    source_reflection_id = Column(String(36), ForeignKey("reflections.id", ondelete="SET NULL"), nullable=True)
    
    # User confirmation — ensures memories are intentionally saved
    user_confirmed = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="core_memories")
    source_reflection = relationship("Reflection", foreign_keys=[source_reflection_id])
    feel_flow_events = relationship("FeelFlowEvent", back_populates="core_memory", cascade="all, delete-orphan")


class FeelFlowEvent(Base):
    """
    A single emotional event recorded in the user's Feel Flow timeline.
    
    These events track emotional patterns over time and connect to Core Memories.
    Used for simple emotion visualization in the mobile app.
    """
    __tablename__ = "feel_flow_events"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reflection_id = Column(String(36), ForeignKey("reflections.id", ondelete="CASCADE"), nullable=True)
    core_memory_id = Column(String(36), ForeignKey("core_memories.id", ondelete="CASCADE"), nullable=True)
    
    # Emotion data
    emotion = Column(String(32), nullable=False)  # EmotionCategory value
    intensity = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Source text — verbatim from user input that triggered this emotion
    source_text = Column(Text, default="")
    
    # AI confidence score — how certain the AI is about this emotion detection
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="feel_flow_events")
    reflection = relationship("Reflection", foreign_keys=[reflection_id])
    core_memory = relationship("CoreMemory", back_populates="feel_flow_events")

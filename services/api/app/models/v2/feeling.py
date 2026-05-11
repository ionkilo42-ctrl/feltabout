"""Feeling model for emotional graph v2.

A Feeling is a single emotional record that captures:
- What emotion was felt (primary_emotion, label)
- How intense it was (intensity 1-10)
- What text triggered it (source_text)
- What memory it's part of (memory_id)
- When it occurred (occurred_at)
- What needs it relates to (many-to-many)
- What entities it's about (many-to-many)
- What topics it covers (many-to-many)
"""

from datetime import datetime
import uuid
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, Column, Float, Boolean, Table, CheckConstraint
from sqlalchemy.orm import relationship

from app.models.v2.base import Base


class PrimaryEmotion(str, enum.Enum):
    """Valid primary emotions for the emotional graph."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    DISGUST = "disgust"


# Association table for feelings <-> needs
feeling_needs = Table(
    "v2_feelings_needs",
    Base.metadata,
    Column("feeling_id", String(36), ForeignKey("v2_feelings.id", ondelete="CASCADE"), primary_key=True),
    Column("need_id", String(36), ForeignKey("v2_needs.id", ondelete="CASCADE"), primary_key=True),
    Column("confidence", Float, default=0.5),
    Column("user_confirmed", Boolean, default=False),
)

# Association table for feelings <-> entities
feeling_entities = Table(
    "v2_feelings_entities",
    Base.metadata,
    Column("feeling_id", String(36), ForeignKey("v2_feelings.id", ondelete="CASCADE"), primary_key=True),
    Column("entity_id", String(36), ForeignKey("v2_entities.id", ondelete="CASCADE"), primary_key=True),
    Column("relationship_type", String(64), default="about"),
    Column("confidence", Float, default=0.5),
    Column("user_confirmed", Boolean, default=False),
)

# Association table for feelings <-> topics
feeling_topics = Table(
    "v2_feelings_topics",
    Base.metadata,
    Column("feeling_id", String(36), ForeignKey("v2_feelings.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", String(36), ForeignKey("v2_topics.id", ondelete="CASCADE"), primary_key=True),
    Column("confidence", Float, default=0.5),
    Column("user_confirmed", Boolean, default=False),
)


class FeelingNeed(Base):
    """Association model for feelings-needs with metadata."""
    __tablename__ = "v2_feeling_needs_detail"
    
    feeling_id = Column(String(36), ForeignKey("v2_feelings.id", ondelete="CASCADE"), primary_key=True)
    need_id = Column(String(36), ForeignKey("v2_needs.id", ondelete="CASCADE"), primary_key=True)
    confidence = Column(Float, default=0.5)
    user_confirmed = Column(Boolean, default=False)


class Feeling(Base):
    """A single emotional record in the user's emotional graph."""
    __tablename__ = "v2_feelings"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core emotion data
    primary_emotion = Column(String(32), nullable=False)
    label = Column(String(128), nullable=False)
    intensity = Column(Float, nullable=False)
    
    # Confidence and source
    confidence = Column(Float, default=0.5)
    source_text = Column(Text, default="")
    
    # Memory relationship
    memory_id = Column(String(36), ForeignKey("v2_memories.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    occurred_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    memory = relationship("Memory", back_populates="feelings")
    needs = relationship("Need", secondary=feeling_needs, back_populates="feelings")
    entities = relationship("Entity", secondary=feeling_entities, back_populates="feelings")
    topics = relationship("Topic", secondary=feeling_topics, back_populates="feelings")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("intensity >= 1 AND intensity <= 10", name="v2_feeling_intensity_range"),
    )
    
    def __repr__(self):
        return f"<Feeling {self.id}: {self.label} ({self.primary_emotion}) intensity={self.intensity}>"
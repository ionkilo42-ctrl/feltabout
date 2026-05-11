"""Memory model for emotional graph v2.

A Memory is a saved emotional event that contains multiple feelings,
connected to entities, needs, and topics. This is the primary unit
for storing confirmed emotional data from Aimee extractions.
"""

from datetime import datetime
import uuid
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, Column
from sqlalchemy.orm import relationship

from app.models.v2.base import Base


class MemoryPrivacy(str, enum.Enum):
    """Privacy levels for memories."""
    PRIVATE = "private"
    CONNECTIONS = "connections"
    SHARED = "shared"


class Memory(Base):
    """A saved emotional event containing multiple feelings and their relationships."""
    __tablename__ = "v2_memories"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    narrative = Column(Text, default="")
    ai_summary = Column(Text, default="")
    occurred_at = Column(DateTime, default=datetime.utcnow)
    privacy_level = Column(String(32), nullable=False, default=MemoryPrivacy.PRIVATE.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    feelings = relationship("Feeling", back_populates="memory", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Memory {self.id}: {self.title}>"
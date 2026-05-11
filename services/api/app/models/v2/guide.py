"""Guide model for emotional graph v2.

Guides are AI personas that the user can customize. Each guide has
a distinct tone, warmth level, and directness level.
"""

from datetime import datetime
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Column, Float, Boolean
from sqlalchemy.orm import relationship

from app.models.v2.base import Base


class Guide(Base):
    """An AI guide persona for the user."""
    __tablename__ = "v2_guides"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    tone = Column(String(32), default="warm")
    warmth_level = Column(Float, default=7.0)
    directness_level = Column(Float, default=5.0)
    personality_description = Column(Text, default="")
    belief_adaptation_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<Guide {self.id}: {self.name}>"
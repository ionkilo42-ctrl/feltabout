"""Topic model for emotional graph v2.

Topics are clusters of related themes that feelings can be about.
They help organize and aggregate feelings by theme.
"""

from datetime import datetime
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Column, Boolean
from sqlalchemy.orm import relationship

from app.models.v2.base import Base
from app.models.v2.feeling import feeling_topics


class Topic(Base):
    """A topic/theme that feelings can be about."""
    __tablename__ = "v2_topics"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, default="")
    is_public_topic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    feelings = relationship("Feeling", secondary=feeling_topics, back_populates="topics")
    
    def __repr__(self):
        return f"<Topic {self.id}: {self.title}>"
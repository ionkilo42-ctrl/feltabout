"""Need model for emotional graph v2.

Needs represent what feelings are asking for. They follow the NVC framework
and are connected to feelings that arise when they are met or unmet.
"""

from datetime import datetime
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Column
from sqlalchemy.orm import relationship

from app.models.v2.base import Base
from app.models.v2.feeling import feeling_needs


class Need(Base):
    """A need entry in the user's need framework.
    
    Needs are shared across the emotional graph. Multiple feelings can 
    connect to the same need. Needs are user-specific but can be 
    pre-populated from the standard NVC need categories.
    """
    __tablename__ = "v2_needs"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    feelings = relationship("Feeling", secondary=feeling_needs, back_populates="needs")
    
    def __repr__(self):
        return f"<Need {self.id}: {self.name}>"
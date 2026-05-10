"""Participant model for conversation space membership."""

from datetime import datetime
import uuid

from sqlalchemy import String, DateTime, ForeignKey, Column, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base


class Participant(Base):
    """
    A participant in a conversation space.
    
    Can be either:
    - A registered user (user_id is set)
    - A guest (user_id is NULL, display_name only)
    
    Access control: A participant can only access the conversation space
    they are enrolled in. They cannot see the owner's reflection library.
    """
    
    __tablename__ = "participants"
    
    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    conversation_space_id = Column(
        String(36), 
        ForeignKey("conversation_spaces.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # NULL for guests (they don't have an account)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Display name shown in the conversation
    display_name = Column(String(128), nullable=False)
    
    # Whether this participant is the owner of the space
    is_owner = Column(Boolean, default=False)
    
    # When they joined
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation_space = relationship("ConversationSpace", back_populates="participants")
    user = relationship("User")
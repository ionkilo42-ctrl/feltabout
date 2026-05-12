"""SessionMessage model for conversation space messages."""

from datetime import datetime
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Column, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base


class SessionMessage(Base):
    """
    A message in a conversation space session.
    
    Messages can be from:
    - A participant (participant_id set)
    - Aimee (is_aimee=True, participant_id NULL)
    
    The is_aimee flag distinguishes AI facilitator messages from human messages.
    """
    
    __tablename__ = "session_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    
    # The conversation space this message belongs to
    conversation_space_id = Column(
        String(36), 
        ForeignKey("conversation_spaces.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # For human messages - NULL for Aimee's messages
    participant_id = Column(
        String(36), 
        ForeignKey("participants.id", ondelete="CASCADE"), 
        nullable=True
    )
    
    # Display name at time of message (denormalized for history)
    sender_name = Column(String(128), nullable=False)
    
    # Whether this is a message from Aimee (AI facilitator)
    is_aimee = Column(Boolean, default=False)
    
    # The message content
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    conversation_space = relationship("ConversationSpace")
    participant = relationship("Participant")
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "id": self.id,
            "conversation_space_id": self.conversation_space_id,
            "participant_id": self.participant_id,
            "sender_name": self.sender_name,
            "is_aimee": self.is_aimee,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
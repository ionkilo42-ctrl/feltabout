"""Conversation space model for private, secure conversation rooms."""

from datetime import datetime
import uuid
import hashlib
import secrets

from sqlalchemy import String, Text, DateTime, ForeignKey, Column, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base


def hash_invite_token(token: str) -> str:
    """Create SHA256 hash of invite token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_websocket_session_id() -> str:
    """Generate a secure session ID for the WebSocket backend."""
    return uuid.uuid4().hex[:12]


class ConversationSpace(Base):
    """
    A private conversation space that can be shared via secure invite links.
    
    Security:
    - Invite tokens are hashed (never stored raw)
    - WebSocket session IDs are generated server-side
    - Access is controlled by owner + participant relationships
    
    WebSocket bridge:
    - websocket_session_id maps to a live session in backend/main.py
    - Created when the conversation space is created
    - Both participants connect to the same underlying session
    """
    
    __tablename__ = "conversation_spaces"
    
    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    owner_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Optional private label (not visible to invitee until they join)
    name = Column(Text, nullable=True)
    
    # WebSocket bridge - internal ID for backend/main.py session
    websocket_session_id = Column(String(64), nullable=True, unique=True, index=True)
    
    # Invite token (hashed)
    invite_token_hash = Column(String(64), nullable=True, index=True)
    invite_token_created_at = Column(DateTime, default=datetime.utcnow)
    
    # Access control
    max_participants = Column(Integer, default=2)
    
    # Status
    status = Column(String(16), default="active")  # active | completed | archived
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Optional link to a reflection
    linked_reflection_id = Column(String(36), ForeignKey("reflections.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    owner = relationship("User")
    participants = relationship("Participant", back_populates="conversation_space", cascade="all, delete-orphan")
    linked_reflection = relationship("Reflection", foreign_keys=[linked_reflection_id])
    
    @classmethod
    def create(cls, owner_user_id: str, name: str = None) -> tuple["ConversationSpace", str]:
        """
        Create a new conversation space with a secure invite token.
        
        Returns: (conversation_space, raw_invite_token)
        The raw token must be sent to the frontend; only the hash is stored.
        """
        raw_token = secrets.token_urlsafe(32)  # ~43 chars
        
        space = cls(
            owner_user_id=owner_user_id,
            name=name,
            invite_token_hash=hash_invite_token(raw_token),
            websocket_session_id=generate_websocket_session_id(),
        )
        
        return space, raw_token
    
    def regenerate_invite_token(self) -> str:
        """Regenerate the invite token, invalidating the old one."""
        raw_token = secrets.token_urlsafe(32)
        self.invite_token_hash = hash_invite_token(raw_token)
        self.invite_token_created_at = datetime.utcnow()
        return raw_token
    
    def verify_invite_token(self, raw_token: str) -> bool:
        """Verify an invite token using constant-time comparison."""
        if not self.invite_token_hash:
            return False
        incoming_hash = hash_invite_token(raw_token)
        import hmac
        return hmac.compare_digest(self.invite_token_hash, incoming_hash)
    
    def is_invite_expired(self, hours: int = 168) -> bool:  # Default 7 days
        """Check if the invite link has expired."""
        if not self.invite_token_created_at:
            return True
        expiry = self.invite_token_created_at.timestamp() + (hours * 3600)
        return datetime.utcnow().timestamp() > expiry
    
    @property
    def participant_count(self) -> int:
        """Get current participant count."""
        return len(self.participants) if self.participants else 0
    
    def is_full(self) -> bool:
        """Check if the conversation space is at max capacity."""
        return self.participant_count >= self.max_participants
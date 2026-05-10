"""Magic link token model for email-based authentication."""

from datetime import datetime, timedelta
import uuid
import hashlib

from sqlalchemy import String, DateTime, Column

from app.models.base import Base


def normalize_email(email: str) -> str:
    """Normalize email to lowercase and stripped."""
    return email.lower().strip()


def hash_email(email: str) -> str:
    """Create SHA256 hash of email for rate limiting lookups."""
    return hashlib.sha256(normalize_email(email).encode()).hexdigest()


def hash_token(token: str) -> str:
    """Create SHA256 hash of raw token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class MagicLinkToken(Base):
    """
    Magic link tokens for email-based authentication.
    
    Security:
    - Raw tokens are never stored (only SHA256 hash)
    - Tokens expire after 15 minutes
    - Tokens can only be used once (marked after verification)
    - Email is stored for user creation/lookup
    - email_hash enables rate limiting by email
    """
    
    __tablename__ = "magic_link_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    
    # Email (normalized) — needed for user creation after token verification
    email = Column(String(256), nullable=False, index=True)
    
    # SHA256 hashes for security
    email_hash = Column(String(64), nullable=False, index=True)  # For rate limiting
    token_hash = Column(String(64), nullable=False, index=True)  # For token lookup
    
    # Timing
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)  # NULL = unused
    
    @classmethod
    def create(cls, email: str, token: str, expires_minutes: int = 15) -> "MagicLinkToken":
        """Create a new magic link token."""
        normalized_email = normalize_email(email)
        now = datetime.utcnow()
        expiry = now + timedelta(minutes=expires_minutes)
        
        return cls(
            email=normalized_email,
            email_hash=hash_email(normalized_email),
            token_hash=hash_token(token),
            expires_at=expiry,
        )
    
    def is_valid(self) -> bool:
        """Check if token is still valid (not expired, not used)."""
        if self.used_at is not None:
            return False
        exp = self.expires_at
        if exp.tzinfo is not None:
            exp = exp.replace(tzinfo=None)
        return bool(datetime.utcnow() < exp)
    
    def mark_used(self) -> None:
        """Mark token as used."""
        self.used_at = datetime.utcnow()
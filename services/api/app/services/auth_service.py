"""
Authentication service for Feltabout.

Handles:
- Magic link token generation and verification
- User creation/finding by email
- JWT session token generation
- Conversation access tokens for guests
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.models.user import User
from app.models.magic_link_token import MagicLinkToken, hash_token

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MIN_PASSWORD_LENGTH = 8

# JWT Configuration
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # 7 days for session tokens
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")

# Magic Link Configuration
MAGIC_LINK_TOKEN_BYTES = 32  # ~43 chars base64


def create_session_token(user_id: str, email: str, name: str) -> str:
    """Create a JWT session token for an authenticated user."""
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "type": "session",
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_conversation_token(
    user_id: Optional[str],
    conversation_space_id: str,
    participant_id: str,
    display_name: str,
    is_guest: bool = False,
) -> str:
    """
    Create a short-lived token for joining a conversation space.

    This token is scoped only to the specific conversation space and
    includes participant info for the WebSocket connection.
    """
    payload = {
        "sub": user_id or "guest",
        "conversation_space_id": conversation_space_id,
        "participant_id": participant_id,
        "display_name": display_name,
        "type": "conversation",
        "is_guest": is_guest,
        "exp": datetime.utcnow() + timedelta(hours=24),  # Valid for 24 hours
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_magic_link_token() -> str:
    """Generate a cryptographically secure magic link token."""
    return secrets.token_urlsafe(MAGIC_LINK_TOKEN_BYTES)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def request_magic_link(self, email: str, next: Optional[str] = None) -> tuple[str, str]:
        """
        Create a magic link token and return the raw token.
        The raw token is logged to console (email sending deferred).

        Returns: (raw_token, invite_url)
        """
        # Normalize and validate email
        normalized_email = email.lower().strip()

        # Delete any existing unused tokens for this email
        existing = await self.db.execute(
            select(MagicLinkToken).where(
                MagicLinkToken.email == normalized_email,
                MagicLinkToken.used_at.is_(None),
            )
        )
        for token in existing.scalars():
            token.used_at = datetime.utcnow()  # Invalidate old tokens

        # Create new magic link token
        raw_token = create_magic_link_token()
        magic_token = MagicLinkToken.create(normalized_email, raw_token)

        self.db.add(magic_token)
        await self.db.commit()

        # Generate the invite URL (include next redirect if provided)
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        invite_url = f"{frontend_url}/verify?token={raw_token}"
        if next:
            invite_url += f"&next={next}"

        # Log the magic link (email sending deferred to later)
        logger.info(f"🔗 Magic link for {normalized_email}: {invite_url}")
        print(f"🔗 Magic link for {normalized_email}: {invite_url}")

        return raw_token, invite_url

    async def verify_magic_link(self, raw_token: str) -> Optional[User]:
        """
        Verify a magic link token and return the user.

        Flow:
        1. Hash the raw token
        2. Find unused, unexpired token with matching hash
        3. Use constant-time comparison for security
        4. Create or find user by email
        5. Mark token as used
        6. Return user
        """
        token_hash = hash_token(raw_token)

        # Find the token
        result = await self.db.execute(
            select(MagicLinkToken).where(
                MagicLinkToken.token_hash == token_hash,
                MagicLinkToken.used_at.is_(None),
            )
        )
        magic_token = result.scalar_one_or_none()

        if not magic_token:
            logger.warning("Magic link token not found or already used")
            return None

        # Check if valid
        if not magic_token.is_valid():
            logger.warning("Magic link token expired or invalid")
            return None

        # Get email from token
        email = magic_token.email

        # Create or find user
        user = await self._get_or_create_user(email)

        # Mark token as used
        magic_token.mark_used()
        await self.db.commit()

        return user

    async def _get_or_create_user(self, email: str) -> User:
        """Get existing user by email or create new one."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create new user with temporary name (can be updated later)
            user = User(
                email=email,
                display_name=email.split("@")[0],  # Use email prefix as default name
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Created new user: {email}")

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user_name(self, user_id: str, name: str) -> Optional[User]:
        """Update user's display name."""
        user = await self.get_user_by_id(user_id)
        if user:
            user.display_name = name
            await self.db.commit()
            await self.db.refresh(user)
        return user

    # ─── Password-based Auth ──────────────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        normalized = email.lower().strip()
        result = await self.db.execute(
            select(User).where(User.email == normalized)
        )
        return result.scalar_one_or_none()

    async def register_user(self, email: str, password: str, display_name: str) -> tuple[Optional[User], Optional[str]]:
        """
        Register a new user with email and password.

        Returns: (user, error_message)
        - On success: (user, None)
        - On error: (None, error_message)
        """
        # Normalize email
        normalized_email = email.lower().strip()

        # Check if email already exists
        existing = await self.get_user_by_email(normalized_email)
        if existing:
            return None, "An account with this email already exists"

        # Validate password length
        if len(password) < MIN_PASSWORD_LENGTH:
            return None, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

        # Validate display name
        if not display_name or len(display_name.strip()) < 1:
            display_name = normalized_email.split("@")[0]

        # Create user with hashed password
        user = User(
            email=normalized_email,
            display_name=display_name.strip(),
            password_hash=self.hash_password(password),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Registered new user: {normalized_email}")
        return user, None

    async def login_user(self, email: str, password: str) -> tuple[Optional[User], Optional[str]]:
        """
        Authenticate a user with email and password.

        Returns: (user, error_message)
        - On success: (user, None)
        - On error: (None, error_message)
        """
        # Normalize email
        normalized_email = email.lower().strip()

        # Find user by email
        user = await self.get_user_by_email(normalized_email)
        if not user:
            # Use generic error to not reveal if email exists
            return None, "Invalid email or password"

        # Check if user has password set
        if not user.password_hash:
            # User exists but only has magic link auth
            return None, "Invalid email or password"

        # Verify password
        if not self.verify_password(password, user.password_hash):
            return None, "Invalid email or password"

        logger.info(f"User logged in: {normalized_email}")
        return user, None

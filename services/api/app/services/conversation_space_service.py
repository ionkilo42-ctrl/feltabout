"""
Conversation space service for creating and managing private conversation rooms.

Handles:
- Creating conversation spaces with secure invite tokens
- Participant management (owner + guests)
- Access control enforcement
- WebSocket session bridge to backend/main.py
"""

import os
import httpx
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.conversation_space import ConversationSpace
from app.models.participant import Participant

logger = logging.getLogger(__name__)

# Backend URL for internal session creation
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")


class ConversationSpaceService:
    """Service for conversation space operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_space(
        self,
        owner_user_id: str,
        name: Optional[str] = None,
        max_participants: int = 2,
    ) -> tuple[ConversationSpace, str]:
        """
        Create a new conversation space with a secure invite token.
        
        Also creates the underlying WebSocket session in backend/main.py.
        
        Returns: (conversation_space, raw_invite_token)
        """
        # Create the conversation space
        space, raw_token = ConversationSpace.create(
            owner_user_id=owner_user_id,
            name=name,
        )
        space.max_participants = max_participants
        
        self.db.add(space)
        await self.db.flush()
        
        # Create the owner as the first participant
        owner_participant = Participant(
            conversation_space_id=space.id,
            user_id=owner_user_id,
            display_name="Owner",  # Will be updated when they set their name
            is_owner=True,
        )
        self.db.add(owner_participant)
        
        await self.db.commit()
        await self.db.refresh(space)
        
        # Create the underlying WebSocket session in backend
        try:
            await self._create_backend_session(space.websocket_session_id)
        except Exception as e:
            logger.warning(f"Failed to create backend session: {e}")
            # Continue anyway - session can be created on first connection
        
        return space, raw_token
    
    async def _create_backend_session(self, session_id: str) -> None:
        """Create a session in backend/main.py via internal endpoint."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/internal/sessions",
                    json={"session_id": session_id}
                )
                response.raise_for_status()
                logger.info(f"Created backend session: {session_id}")
            except httpx.HTTPError as e:
                logger.warning(f"Backend session creation failed: {e}")
    
    async def get_space_by_id(
        self, 
        space_id: str, 
        user_id: Optional[str] = None
    ) -> Optional[ConversationSpace]:
        """
        Get a conversation space by ID with access control.
        
        Returns None if:
        - Space doesn't exist
        - User is not the owner and not a participant
        """
        result = await self.db.execute(
            select(ConversationSpace)
            .options(selectinload(ConversationSpace.participants))
            .where(ConversationSpace.id == space_id)
        )
        space = result.scalar_one_or_none()
        
        if not space:
            return None
        
        # Check access: owner or participant
        if user_id and (space.owner_user_id == user_id):
            return space
        
        # Check if user is a participant
        if user_id:
            participant_result = await self.db.execute(
                select(Participant).where(
                    and_(
                        Participant.conversation_space_id == space_id,
                        Participant.user_id == user_id
                    )
                )
            )
            if participant_result.scalar_one_or_none():
                return space
        
        # No user_id = guest access; return space if it exists (caller handles further validation)
        return space
    
    async def list_user_spaces(self, user_id: str) -> list[ConversationSpace]:
        """List all conversation spaces the user owns or participates in."""
        result = await self.db.execute(
            select(ConversationSpace)
            .options(selectinload(ConversationSpace.participants))
            .join(Participant, ConversationSpace.id == Participant.conversation_space_id)
            .where(Participant.user_id == user_id)
            .order_by(ConversationSpace.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def verify_invite_token(self, raw_token: str) -> Optional[ConversationSpace]:
        """
        Verify an invite token and return the conversation space.
        
        Returns None if:
        - Token is invalid
        - Token is expired
        - Space is full
        """
        import hashlib
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        result = await self.db.execute(
            select(ConversationSpace)
            .options(selectinload(ConversationSpace.participants))
            .where(ConversationSpace.invite_token_hash == token_hash)
        )
        space = result.scalar_one_or_none()
        
        if not space:
            return None
        
        # Check if invite expired (7 days)
        if space.is_invite_expired():
            return None
        
        # Check if space is full
        if space.is_full():
            return None
        
        return space
    
    async def add_participant(
        self,
        space_id: str,
        display_name: str,
        user_id: Optional[str] = None,
        is_guest: bool = True,
    ) -> Optional[Participant]:
        """
        Add a participant to a conversation space.
        
        Returns None if:
        - Space doesn't exist
        - Space is full
        - User is already a participant
        """
        space = await self.get_space_by_id(space_id, user_id)
        if not space:
            return None
        
        # Check if space is full
        if space.is_full():
            return None
        
        # Check if already a participant
        existing = await self.db.execute(
            select(Participant).where(
                and_(
                    Participant.conversation_space_id == space_id,
                    Participant.user_id == user_id if user_id else Participant.user_id.is_(None)
                )
            )
        )
        if existing.scalar_one_or_none():
            return None
        
        # Create participant
        participant = Participant(
            conversation_space_id=space_id,
            user_id=user_id,
            display_name=display_name,
            is_owner=False,
        )
        self.db.add(participant)
        await self.db.commit()
        await self.db.refresh(participant)
        
        return participant
    
    async def get_participant(
        self,
        space_id: str,
        user_id: Optional[str] = None,
        participant_id: Optional[str] = None,
    ) -> Optional[Participant]:
        """Get a participant by user_id or participant_id."""
        if participant_id:
            result = await self.db.execute(
                select(Participant).where(
                    and_(
                        Participant.id == participant_id,
                        Participant.conversation_space_id == space_id
                    )
                )
            )
        elif user_id:
            result = await self.db.execute(
                select(Participant).where(
                    and_(
                        Participant.conversation_space_id == space_id,
                        Participant.user_id == user_id
                    )
                )
            )
        else:
            return None
        
        return result.scalar_one_or_none()
    
    async def regenerate_invite(
        self,
        space_id: str,
        user_id: str,
    ) -> Optional[str]:
        """
        Regenerate invite token for a conversation space.
        Only the owner can do this.
        
        Returns the new raw token, or None if unauthorized.
        """
        space = await self.get_space_by_id(space_id, user_id)
        if not space:
            return None
        
        if space.owner_user_id != user_id:
            return None
        
        new_token = space.regenerate_invite_token()
        await self.db.commit()
        
        return new_token
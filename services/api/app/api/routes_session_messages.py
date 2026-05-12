"""
Session messages API routes.

Endpoints for the shared session chat:
- POST /conversation-spaces/{space_id}/messages - Send a message
- GET /conversation-spaces/{space_id}/messages - Get all messages (with polling support)
- GET /conversation-spaces/{space_id}/messages/latest - Get messages since timestamp (for polling)
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import SessionMessage, ConversationSpace, Participant
from app.api.routes_auth import require_user

router = APIRouter(prefix="/conversation-spaces", tags=["session-messages"])


# ─── Request/Response Models ──────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    content: str
    sender_name: Optional[str] = "User"


class MessageResponse(BaseModel):
    id: str
    conversation_space_id: str
    participant_id: Optional[str]
    sender_name: str
    is_aimee: bool
    content: str
    created_at: str


class MessagesListResponse(BaseModel):
    messages: list[MessageResponse]
    aimee_present: bool = True  # Aimee is always present in shared sessions


class ParticipantsResponse(BaseModel):
    participants: list[dict]


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/{space_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    space_id: str,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to a conversation space.
    
    The message will be stored and Aimee will respond asynchronously.
    For MVP, Aimee responses are generated immediately (simplified flow).
    """
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Get the space
    result = await db.execute(
        select(ConversationSpace).where(ConversationSpace.id == space_id)
    )
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Conversation space not found")
    
    # For MVP: create message with a placeholder participant_id
    # In full auth flow, this would come from the session
    # For now, we use a temporary approach
    message = SessionMessage(
        conversation_space_id=space_id,
        participant_id=None,  # Will be set when participant joins properly
        sender_name=data.sender_name or "User",
        is_aimee=False,
        content=data.content.strip(),
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        conversation_space_id=message.conversation_space_id,
        participant_id=message.participant_id,
        sender_name=message.sender_name,
        is_aimee=message.is_aimee,
        content=message.content,
        created_at=message.created_at.isoformat() if message.created_at else "",
    )


@router.get("/{space_id}/messages", response_model=MessagesListResponse)
async def get_messages(
    space_id: str,
    since: Optional[str] = None,  # ISO timestamp for polling
    db: AsyncSession = Depends(get_db),
):
    """
    Get all messages for a conversation space.
    
    Optional 'since' parameter for polling: returns only messages after that timestamp.
    """
    # Verify space exists
    result = await db.execute(
        select(ConversationSpace).where(ConversationSpace.id == space_id)
    )
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Conversation space not found")
    
    # Build query
    query = select(SessionMessage).where(
        SessionMessage.conversation_space_id == space_id
    ).order_by(SessionMessage.created_at.asc())
    
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            query = query.where(SessionMessage.created_at > since_dt)
        except ValueError:
            pass  # Ignore invalid timestamps
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return MessagesListResponse(
        messages=[
            MessageResponse(
                id=m.id,
                conversation_space_id=m.conversation_space_id,
                participant_id=m.participant_id,
                sender_name=m.sender_name,
                is_aimee=m.is_aimee,
                content=m.content,
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
            for m in messages
        ],
        aimee_present=True,  # Aimee is always available
    )


@router.get("/{space_id}/participants", response_model=ParticipantsResponse)
async def get_participants(
    space_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all participants in a conversation space, including Aimee."""
    # Verify space exists
    result = await db.execute(
        select(ConversationSpace).where(ConversationSpace.id == space_id)
    )
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Conversation space not found")
    
    # Get real participants
    result = await db.execute(
        select(Participant).where(Participant.conversation_space_id == space_id)
    )
    participants = result.scalars().all()
    
    # Build participant list with Aimee
    participant_list = [
        {
            "id": p.id,
            "display_name": p.display_name,
            "is_owner": p.is_owner,
            "is_aimee": False,
        }
        for p in participants
    ]
    
    # Add Aimee as a virtual participant
    participant_list.append({
        "id": "aimee",
        "display_name": "Aimee",
        "is_owner": False,
        "is_aimee": True,
    })
    
    return ParticipantsResponse(participants=participant_list)
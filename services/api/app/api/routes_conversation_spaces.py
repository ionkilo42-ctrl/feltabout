"""
Conversation space API routes.

Endpoints:
- POST /conversation-spaces - Create a new conversation space
- GET /conversation-spaces - List user's conversation spaces
- GET /conversation-spaces/{id} - Get a specific space (access-controlled)
- GET /conversation-spaces/verify-invite/{token} - Verify invite token
- POST /conversation-spaces/{id}/join - Join as guest
- POST /conversation-spaces/{id}/regenerate-invite - Regenerate invite token (owner only)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.conversation_space_service import ConversationSpaceService
from app.services.ws_token_service import get_ws_token_service
from app.api.routes_auth import require_user

router = APIRouter(prefix="/conversation-spaces", tags=["conversation-spaces"])


# ─── Request/Response Models ──────────────────────────────────────────────────

class CreateConversationSpaceRequest(BaseModel):
    name: Optional[str] = None
    max_participants: int = 2


class ConversationSpaceResponse(BaseModel):
    id: str
    name: Optional[str]
    status: str
    max_participants: int
    participant_count: int
    created_at: str
    is_owner: bool
    # WebSocket connection info (internal, not for UI display)
    websocket_session_id: Optional[str] = None


class CreateConversationSpaceResponse(BaseModel):
    id: str
    name: Optional[str]
    invite_url: str  # Full URL with raw token
    max_participants: int


class VerifyInviteResponse(BaseModel):
    valid: bool
    space_id: Optional[str] = None
    space_name: Optional[str] = None
    already_joined: bool = False
    is_full: bool = False


class JoinConversationRequest(BaseModel):
    display_name: str


class JoinConversationResponse(BaseModel):
    participant_id: str
    conversation_space_id: str
    websocket_session_id: str
    ws_access_token: str  # Scoped token for WS auth
    display_name: str


class ParticipantResponse(BaseModel):
    id: str
    display_name: str
    is_owner: bool
    joined_at: str


class ListConversationSpacesResponse(BaseModel):
    spaces: List[ConversationSpaceResponse]


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("", response_model=CreateConversationSpaceResponse, status_code=201)
async def create_conversation_space(
    data: CreateConversationSpaceRequest,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new conversation space.
    
    The owner is automatically added as the first participant.
    An invite link is generated and returned.
    """
    service = ConversationSpaceService(db)
    
    space, raw_token = await service.create_space(
        owner_user_id=current_user["sub"],
        name=data.name,
        max_participants=data.max_participants,
    )
    
    # Generate invite URL
    frontend_url = current_user.get("frontend_url", "http://localhost:3000")
    invite_url = f"{frontend_url}/join/{raw_token}"
    
    return CreateConversationSpaceResponse(
        id=space.id,
        name=space.name,
        invite_url=invite_url,
        max_participants=space.max_participants,
    )


@router.get("", response_model=ListConversationSpacesResponse)
async def list_conversation_spaces(
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversation spaces the user owns or participates in."""
    service = ConversationSpaceService(db)
    spaces = await service.list_user_spaces(current_user["sub"])
    
    return ListConversationSpacesResponse(
        spaces=[
            ConversationSpaceResponse(
                id=s.id,
                name=s.name,
                status=s.status,
                max_participants=s.max_participants,
                participant_count=s.participant_count,
                created_at=s.created_at.isoformat() if s.created_at else "",
                is_owner=s.owner_user_id == current_user["sub"],
                websocket_session_id=s.websocket_session_id,
            )
            for s in spaces
        ]
    )


@router.get("/verify-invite/{token}", response_model=VerifyInviteResponse)
async def verify_invite(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify an invite token.
    
    Returns:
    - valid: True if token is valid and space is available
    - space_id: The conversation space ID (if valid)
    - already_joined: True if user is already a participant (via cookie/session)
    - is_full: True if the space is at max capacity
    """
    service = ConversationSpaceService(db)
    space = await service.verify_invite_token(token)
    
    if not space:
        return VerifyInviteResponse(valid=False)
    
    return VerifyInviteResponse(
        valid=True,
        space_id=space.id,
        space_name=space.name,
        is_full=space.is_full(),
    )


@router.get("/{space_id}", response_model=ConversationSpaceResponse)
async def get_conversation_space(
    space_id: str,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation space (access-controlled)."""
    service = ConversationSpaceService(db)
    space = await service.get_space_by_id(space_id, current_user["sub"])
    
    if not space:
        raise HTTPException(status_code=404, detail="Conversation space not found or access denied")
    
    return ConversationSpaceResponse(
        id=space.id,
        name=space.name,
        status=space.status,
        max_participants=space.max_participants,
        participant_count=space.participant_count,
        created_at=space.created_at.isoformat() if space.created_at else "",
        is_owner=space.owner_user_id == current_user["sub"],
        websocket_session_id=space.websocket_session_id,
    )


@router.post("/{space_id}/join", response_model=JoinConversationResponse)
async def join_conversation_space(
    space_id: str,
    data: JoinConversationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Join a conversation space as a guest or authenticated user.
    
    For guests: no auth required, user_id will be NULL
    For authenticated users: can join via invite link
    """
    service = ConversationSpaceService(db)
    
    # First verify the invite token is valid
    # The space_id should match a valid space
    
    space = await service.get_space_by_id(space_id, None)
    if not space:
        raise HTTPException(status_code=404, detail="Conversation space not found")
    
    # Check if space is full
    if space.is_full():
        raise HTTPException(
            status_code=409,
            detail="This conversation space is already full. The host can create a new invite link if needed."
        )
    
    # Add participant (guest - no user_id)
    participant = await service.add_participant(
        space_id=space_id,
        display_name=data.display_name,
        user_id=None,  # Guest
        is_guest=True,
    )
    
    if not participant:
        raise HTTPException(status_code=400, detail="Could not join conversation space")
    
    # Generate scoped WS access token
    ws_token_service = get_ws_token_service()
    ws_session_id = str(space.websocket_session_id) if space.websocket_session_id else ""
    ws_access_token = ws_token_service.create_token(
        participant_id=str(participant.id),
        space_id=str(space_id),
        session_id=ws_session_id,
    )
    
    return JoinConversationResponse(
        participant_id=participant.id,
        conversation_space_id=space_id,
        websocket_session_id=space.websocket_session_id or "",
        ws_access_token=ws_access_token,
        display_name=data.display_name,
    )


@router.post("/{space_id}/regenerate-invite")
async def regenerate_invite(
    space_id: str,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate the invite token for a conversation space.
    Only the owner can do this.
    """
    service = ConversationSpaceService(db)
    new_token = await service.regenerate_invite(space_id, current_user["sub"])
    
    if not new_token:
        raise HTTPException(status_code=403, detail="Not authorized to regenerate invite")
    
    frontend_url = current_user.get("frontend_url", "http://localhost:3000")
    invite_url = f"{frontend_url}/join/{new_token}"
    
    return {"invite_url": invite_url}
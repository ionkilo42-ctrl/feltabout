"""
Library API routes.

Returns a unified view of reflections and conversation spaces
for the signed-in user, sorted newest first.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.models.reflection import Reflection
from app.models.conversation_space import ConversationSpace
from app.models.participant import Participant
from app.api.routes_auth import require_user

router = APIRouter(prefix="/library", tags=["library"])


class LibraryItemResponse(BaseModel):
    """Single unified item for the library view."""
    type: str  # "reflection" or "conversation"
    id: str
    name: str  # title for reflections, name for conversations
    created_at: str  # ISO format
    status: str  # draft/completed/archived for reflections, active/pending/complete for conversations
    participant_count: int = 0  # only meaningful for conversations
    is_owner: bool = False  # only meaningful for conversations
    # Optional subtitle for richer cards
    subtitle: Optional[str] = None


class LibraryResponse(BaseModel):
    items: List[LibraryItemResponse]


@router.get("", response_model=LibraryResponse)
async def get_library(
    current_user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """
    Get all library items (reflections + conversation spaces) for the current user.
    
    Sorted by created_at descending (newest first).
    Access-controlled — only returns items belonging to the signed-in user.
    """
    user_id = current_user["sub"]

    from sqlalchemy import select, or_, func

    # Get reflections for this user
    refl_stmt = (
        select(
            Reflection.id,
            Reflection.title,
            Reflection.status,
            Reflection.created_at,
            Reflection.situation,
        )
        .where(Reflection.user_id == user_id)
    )
    refl_result = await db.execute(refl_stmt)
    reflections = refl_result.all()

    # Get conversation spaces where user is owner OR participant
    # First get participant records for this user
    participant_stmt = select(Participant.space_id).where(Participant.user_id == user_id)
    participant_result = await db.execute(participant_stmt)
    participant_space_ids = [row[0] for row in participant_result.all()]

    if participant_space_ids:
        space_stmt = (
            select(
                ConversationSpace.id,
                ConversationSpace.name,
                ConversationSpace.status,
                ConversationSpace.created_at,
                ConversationSpace.owner_user_id,
            )
            .where(
                or_(
                    ConversationSpace.owner_user_id == user_id,
                    ConversationSpace.id.in_(participant_space_ids),
                )
            )
        )
    else:
        # User has no conversation space participation
        space_stmt = (
            select(
                ConversationSpace.id,
                ConversationSpace.name,
                ConversationSpace.status,
                ConversationSpace.created_at,
                ConversationSpace.owner_user_id,
            )
            .where(ConversationSpace.owner_user_id == user_id)
        )

    space_result = await db.execute(space_stmt)
    spaces = space_result.all()

    # Build unified list
    items: List[LibraryItemResponse] = []

    # Add reflections
    for r in reflections:
        name = r.title if r.title else (
            r.situation[:60] + "..." if r.situation and len(r.situation) > 60 else (r.situation or "Untitled reflection")
        )
        items.append(LibraryItemResponse(
            type="reflection",
            id=r.id,
            name=name,
            created_at=r.created_at.isoformat() if r.created_at else "",
            status=r.status or "draft",
            participant_count=0,
            is_owner=False,
        ))

    # Add conversation spaces (need participant count per space)
    # We already have the spaces, now get participant counts
    for s in spaces:
        # Count participants for this space
        count_result = await db.execute(
            select(func.count(Participant.id)).where(Participant.space_id == s.id)
        )
        participant_count = count_result.scalar() or 0

        space_name = s.name if s.name else (
            f"Conversation from {s.created_at.strftime('%b %d')}" if s.created_at else "Conversation"
        )
        items.append(LibraryItemResponse(
            type="conversation",
            id=s.id,
            name=space_name,
            created_at=s.created_at.isoformat() if s.created_at else "",
            status=s.status or "pending",
            participant_count=participant_count,
            is_owner=(s.owner_user_id == user_id),
        ))

    # Sort by created_at descending
    items.sort(key=lambda x: x.created_at, reverse=True)

    return LibraryResponse(items=items)
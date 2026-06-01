"""Entity API routes for v2.

These routes are INTERNAL/DEVELOPMENT only for MVP 1.
They require authentication and are disabled in production unless ALLOW_V2=true.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.routes_auth import require_user, check_v2_access
from app.schemas.v2.entity import EntityResponse
from app.services.v2.entity_service import EntityService

router = APIRouter(prefix="/v2/entities", tags=["v2-entities"])


@router.get("", response_model=List[EntityResponse])
async def list_entities(
    entity_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    check_v2_access()
    user_id = current_user["sub"]
    """List entities for the current user."""
    entities = await EntityService.list_by_user(
        db, user_id, entity_type=entity_type
    )
    return [EntityResponse.model_validate(e) for e in entities]


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    check_v2_access()
    user_id = current_user["sub"]
    """Get entity detail."""
    entity = await EntityService.get_by_id(db, entity_id, user_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return EntityResponse.model_validate(entity)
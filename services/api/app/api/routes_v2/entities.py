"""Entity API routes for v2."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.v2.entity import EntityResponse
from app.services.v2.entity_service import EntityService

router = APIRouter(prefix="/v2/entities", tags=["v2-entities"])


async def get_current_user_id() -> str:
    """Get current user ID (simplified for MVP)."""
    return "dev-user-001"


@router.get("", response_model=List[EntityResponse])
async def list_entities(
    entity_type: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List entities for the current user."""
    entities = await EntityService.list_by_user(
        db, user_id, entity_type=entity_type
    )
    return [EntityResponse.model_validate(e) for e in entities]


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get entity detail."""
    entity = await EntityService.get_by_id(db, entity_id, user_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return EntityResponse.model_validate(entity)
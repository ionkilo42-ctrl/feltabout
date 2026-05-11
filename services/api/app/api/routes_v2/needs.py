"""Need API routes for v2."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.v2.need import NeedResponse, NeedWithRelations
from app.services.v2.need_service import NeedService

router = APIRouter(prefix="/v2/needs", tags=["v2-needs"])


async def get_current_user_id() -> str:
    """Get current user ID (simplified for MVP)."""
    return "dev-user-001"


@router.get("", response_model=List[NeedResponse])
async def list_needs(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all needs for the current user."""
    needs = await NeedService.list_by_user(db, user_id)
    return [NeedResponse.model_validate(n) for n in needs]


@router.get("/{need_id}", response_model=NeedWithRelations)
async def get_need(
    need_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get need detail with related feelings, entities, topics, memories."""
    need = await NeedService.get_by_id(db, need_id, user_id)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")
    return NeedWithRelations.model_validate(need)
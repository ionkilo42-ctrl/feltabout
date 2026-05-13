"""Need API routes for v2.

These routes are INTERNAL/DEVELOPMENT only for MVP 1.
They require authentication and are disabled in production unless ALLOW_V2=true.
"""

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.routes_auth import require_user
from app.schemas.v2.need import NeedResponse, NeedWithRelations
from app.services.v2.need_service import NeedService

router = APIRouter(prefix="/v2/needs", tags=["v2-needs"])


def _check_v2_access():
    """Check if v2 routes are allowed in current environment."""
    allow_v2 = os.environ.get("ALLOW_V2", "false").lower() == "true"
    is_production = os.environ.get("ENVIRONMENT", "development") == "production"
    
    if is_production and not allow_v2:
        raise HTTPException(
            status_code=403,
            detail="V2 routes are not enabled in production. Set ALLOW_V2=true to enable."
        )


@router.get("", response_model=List[NeedResponse])
async def list_needs(
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    _check_v2_access()
    user_id = current_user["sub"]
    """List all needs for the current user."""
    needs = await NeedService.list_by_user(db, user_id)
    return [NeedResponse.model_validate(n) for n in needs]


@router.get("/{need_id}", response_model=NeedWithRelations)
async def get_need(
    need_id: str,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    _check_v2_access()
    user_id = current_user["sub"]
    """Get need detail with related feelings, entities, topics, memories."""
    need = await NeedService.get_by_id(db, need_id, user_id)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")
    return NeedWithRelations.model_validate(need)
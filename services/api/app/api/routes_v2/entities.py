"""Entity API routes for v2.

These routes are INTERNAL/DEVELOPMENT only for MVP 1.
They require authentication and are disabled in production unless ALLOW_V2=true.
"""

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.routes_auth import require_user
from app.schemas.v2.entity import EntityResponse
from app.services.v2.entity_service import EntityService

router = APIRouter(prefix="/v2/entities", tags=["v2-entities"])


def _check_v2_access():
    """Check if v2 routes are allowed in current environment."""
    allow_v2 = os.environ.get("ALLOW_V2", "false").lower() == "true"
    is_production = os.environ.get("ENVIRONMENT", "development") == "production"
    
    if is_production and not allow_v2:
        raise HTTPException(
            status_code=403,
            detail="V2 routes are not enabled in production. Set ALLOW_V2=true to enable."
        )


@router.get("", response_model=List[EntityResponse])
async def list_entities(
    entity_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    _check_v2_access()
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
    _check_v2_access()
    user_id = current_user["sub"]
    """Get entity detail."""
    entity = await EntityService.get_by_id(db, entity_id, user_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return EntityResponse.model_validate(entity)
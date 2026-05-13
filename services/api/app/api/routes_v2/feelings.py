"""Feelings API routes for v2.

These routes are INTERNAL/DEVELOPMENT only for MVP 1.
They require authentication and are disabled in production unless ALLOW_V2=true.
"""

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.routes_auth import require_user
from app.schemas.v2.feeling import FeelingResponse
from app.schemas.v2.feelflow import FeelFlowResponse, FeelMapResponse
from app.services.v2.feeling_service import FeelingService
from app.services.v2.analytics_service import AnalyticsService

router = APIRouter(prefix="/v2/feelings", tags=["v2-feelings"])


def _check_v2_access():
    """Check if v2 routes are allowed in current environment."""
    allow_v2 = os.environ.get("ALLOW_V2", "false").lower() == "true"
    is_production = os.environ.get("ENVIRONMENT", "development") == "production"
    
    if is_production and not allow_v2:
        raise HTTPException(
            status_code=403,
            detail="V2 routes are not enabled in production. Set ALLOW_V2=true to enable."
        )
from fastapi import HTTPException


@router.get("", response_model=List[FeelingResponse])
async def list_feelings(
    memory_id: Optional[str] = Query(None),
    primary_emotion: Optional[str] = Query(None),
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    _check_v2_access()
    user_id = current_user["sub"]
    """List feelings for the current user."""
    feelings = await FeelingService.list_by_user(
        db, user_id, memory_id=memory_id, primary_emotion=primary_emotion
    )
    return [FeelingResponse.model_validate(f) for f in feelings]


@router.get("/feel-flow", response_model=FeelFlowResponse)
async def get_feel_flow(
    entity_id: Optional[str] = Query(None),
    time_bucket: str = Query("day"),
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    _check_v2_access()
    user_id = current_user["sub"]
    """Get time series emotional data for FeelFlow visualization."""
    return await AnalyticsService.get_feel_flow(
        db, user_id, entity_id=entity_id, time_bucket=time_bucket, days=days
    )


@router.get("/feel-map", response_model=FeelMapResponse)
async def get_feel_map(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    _check_v2_access()
    user_id = current_user["sub"]
    """Get emotional composition data for FeelMap treemap."""
    return await AnalyticsService.get_feel_map(db, user_id, days=days)
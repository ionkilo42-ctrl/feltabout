"""Feelings API routes for v2."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.v2.feeling import FeelingResponse
from app.schemas.v2.feelflow import FeelFlowResponse, FeelMapResponse
from app.services.v2.feeling_service import FeelingService
from app.services.v2.analytics_service import AnalyticsService

router = APIRouter(prefix="/v2/feelings", tags=["v2-feelings"])


async def get_current_user_id() -> str:
    """Get current user ID (simplified for MVP)."""
    return "dev-user-001"


@router.get("", response_model=List[FeelingResponse])
async def list_feelings(
    memory_id: Optional[str] = Query(None),
    primary_emotion: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
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
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get time series emotional data for FeelFlow visualization."""
    return await AnalyticsService.get_feel_flow(
        db, user_id, entity_id=entity_id, time_bucket=time_bucket, days=days
    )


@router.get("/feel-map", response_model=FeelMapResponse)
async def get_feel_map(
    days: int = Query(30, ge=1, le=365),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get emotional composition data for FeelMap treemap."""
    return await AnalyticsService.get_feel_map(db, user_id, days=days)
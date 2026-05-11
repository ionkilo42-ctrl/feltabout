"""
Internal admin observability endpoints for Phase 1E.

These endpoints are for internal/admin use only.
They provide aggregate metrics without exposing user data.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.dependencies import get_db, get_admin_user
from app.models.user import User
from app.services.analytics import get_analytics, AnalyticsService


router = APIRouter(prefix="/internal", tags=["internal"])


class InternalStatsResponse(BaseModel):
    """Aggregate stats without user-level detail."""
    extractions: dict
    saves: dict
    safety: dict
    api_failures: dict
    users: dict
    generated_at: str


class HealthCheck(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Basic health check for internal monitoring."""
    return HealthCheck(
        status="healthy",
        version="1.0.0"
    )


@router.get("/v2/stats", response_model=InternalStatsResponse)
async def get_v2_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get aggregate V2 API statistics.
    
    Only accessible to admin users.
    Returns aggregate counts without user-level detail.
    No emotional text is ever exposed through this endpoint.
    """
    analytics: AnalyticsService = get_analytics(db)
    
    return analytics.get_full_stats()


@router.get("/users/count")
async def get_user_count(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get user count for admin dashboard."""
    total_users = db.query(User).count()
    return {"total_users": total_users}


@router.get("/system/ping")
async def ping():
    """Simple ping for connectivity checks."""
    return {"pong": True}
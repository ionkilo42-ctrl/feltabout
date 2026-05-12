"""
FeelFlow API routes — emotion timeline and summary data.

Endpoints:
- GET /feelflow/timeline - Recent emotion events for current user
- GET /feelflow/summary - Emotion distribution over time
- GET /feelflow/reflections/{reflection_id} - Events for specific reflection

Privacy: All data is user-isolated. No clinical interpretation in responses.
"""


from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.feelflow import (
    FeelFlowEventResponse,
    FeelFlowTimelineResponse,
    FeelFlowSummaryResponse,
    FeelFlowReflectionEventsResponse,
)
from app.services.feelflow_service import FeelFlowService
from app.api.routes_auth import require_user


# ─── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/feelflow", tags=["feelflow"])


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.get("/timeline", response_model=FeelFlowTimelineResponse)
async def get_timeline(
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent emotion events for the current user's timeline.
    
    Returns emotion events ordered by most recent first.
    No clinical interpretation — just raw event data.
    """
    events = await FeelFlowService.get_timeline(db, user["sub"], limit=limit)
    
    return FeelFlowTimelineResponse(
        events=[
            FeelFlowEventResponse(
                id=e.id,
                reflection_id=e.reflection_id,
                emotion=e.emotion,
                intensity=e.intensity,
                source_text=e.source_text,
                confidence_score=e.confidence_score,
                created_at=e.created_at,
            )
            for e in events
        ],
        total=len(events),
        limit=limit,
    )


@router.get("/summary", response_model=FeelFlowSummaryResponse)
async def get_summary(
    days: int = Query(default=30, ge=7, le=365),
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get emotion distribution summary over time.
    
    Returns raw emotion counts only — no clinical interpretation.
    Tone remains calm, practical, non-judgmental.
    """
    summary = await FeelFlowService.get_summary(db, user["sub"], days=days)
    
    return FeelFlowSummaryResponse(
        emotion_counts=summary["emotion_counts"],
        total_events=summary["total_events"],
        avg_intensity=summary["avg_intensity"],
        period_days=summary["period_days"],
    )


@router.get("/reflections/{reflection_id}", response_model=FeelFlowReflectionEventsResponse)
async def get_reflection_events(
    reflection_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get emotion events for a specific reflection.
    
    All events are user-isolated — only returns events
    belonging to the authenticated user.
    """
    events = await FeelFlowService.get_events_by_reflection(
        db, user["sub"], reflection_id
    )
    
    return FeelFlowReflectionEventsResponse(
        reflection_id=reflection_id,
        events=[
            FeelFlowEventResponse(
                id=e.id,
                reflection_id=e.reflection_id,
                emotion=e.emotion,
                intensity=e.intensity,
                source_text=e.source_text,
                confidence_score=e.confidence_score,
                created_at=e.created_at,
            )
            for e in events
        ],
        total=len(events),
    )

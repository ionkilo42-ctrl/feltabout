"""
Analytics & Admin API routes.

Endpoints for internal review and feedback aggregation.
These are for product telemetry and output quality review.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Reflection, ReflectionFeedback, ReflectionOutput, SafetyEvent


router = APIRouter(prefix="/admin", tags=["admin"])


async def require_user(current_user: dict = None) -> dict:
    """Admin routes require authentication (MVP 2: add admin role check)."""
    import os
    USE_AUTH = os.environ.get("USE_AUTH", "false") == "true"
    
    if USE_AUTH and not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Dev mode: allow all requests
    return {"sub": "dev-user-001"}


@router.get("/analytics/feedback-summary")
async def get_feedback_summary(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    """
    Aggregated feedback metrics for the last N days.
    
    Returns:
    - Total reflections completed
    - Total feedback submissions
    - Average prepared_score
    - Average less_reactive_score
    - Average conversation_went_better (for answered follow-ups)
    - Breakdown of each score (1, 2, 3 counts)
    - Breakdown by prompt_version for version comparison
    """
    # Get all feedback with joined reflections
    result = await db.execute(
        select(ReflectionFeedback).where(ReflectionFeedback.prepared_score > 0)
    )
    feedbacks = result.scalars().all()
    
    if not feedbacks:
        return {
            "total_responses": 0,
            "avg_prepared_score": None,
            "avg_less_reactive_score": None,
            "avg_conversation_went_better": None,
            "prepared_score_breakdown": {"1": 0, "2": 0, "3": 0},
            "less_reactive_breakdown": {"1": 0, "2": 0, "3": 0},
            "conversation_went_better_breakdown": {"0": 0, "1": 0, "2": 0, "3": 0},
            "by_prompt_version": {},
        }
    
    total = len(feedbacks)
    prepared_scores = [f.prepared_score for f in feedbacks]
    reactive_scores = [f.less_reactive_score for f in feedbacks]
    followup_scores = [f.conversation_went_better for f in feedbacks]
    answered_followup = [s for s in followup_scores if s > 0]
    
    # Count breakdowns
    prepared_breakdown = {str(i): prepared_scores.count(i) for i in [1, 2, 3]}
    reactive_breakdown = {str(i): reactive_scores.count(i) for i in [1, 2, 3]}
    followup_breakdown = {str(i): followup_scores.count(i) for i in [0, 1, 2, 3]}
    
    # Get outputs to group by prompt_version
    output_result = await db.execute(
        select(ReflectionOutput).where(ReflectionOutput.id.isnot(None))
    )
    outputs_by_reflection = {o.reflection_id: o for o in output_result.scalars().all()}
    
    # Group feedback by prompt_version
    by_prompt_version: dict[str, dict] = {}
    for fb in feedbacks:
        output = outputs_by_reflection.get(fb.reflection_id)
        if not output:
            continue
        version = output.prompt_version or "unknown"
        if version not in by_prompt_version:
            by_prompt_version[version] = {
                "count": 0,
                "avg_prepared": [],
                "avg_reactive": [],
                "avg_went_better": [],
            }
        by_prompt_version[version]["count"] += 1
        by_prompt_version[version]["avg_prepared"].append(fb.prepared_score)
        by_prompt_version[version]["avg_reactive"].append(fb.less_reactive_score)
        if fb.conversation_went_better > 0:
            by_prompt_version[version]["avg_went_better"].append(fb.conversation_went_better)
    
    # Compute averages per version
    by_prompt_version_summary = {}
    for version, data in by_prompt_version.items():
        avg_prep = data["avg_prepared"]
        avg_reac = data["avg_reactive"]
        avg_went = data["avg_went_better"]
        by_prompt_version_summary[version] = {
            "response_count": data["count"],
            "avg_prepared_score": round(sum(avg_prep) / len(avg_prep), 2) if avg_prep else None,
            "avg_less_reactive_score": round(sum(avg_reac) / len(avg_reac), 2) if avg_reac else None,
            "avg_conversation_went_better": round(sum(avg_went) / len(avg_went), 2) if avg_went else None,
            "went_better_response_count": len(avg_went),
        }
    
    return {
        "total_responses": total,
        "avg_prepared_score": round(sum(prepared_scores) / total, 2),
        "avg_less_reactive_score": round(sum(reactive_scores) / total, 2),
        "avg_conversation_went_better": round(sum(answered_followup) / len(answered_followup), 2) if answered_followup else None,
        "answered_followup_count": len(answered_followup),
        "prepared_score_breakdown": prepared_breakdown,
        "less_reactive_breakdown": reactive_breakdown,
        "conversation_went_better_breakdown": followup_breakdown,
        "by_prompt_version": by_prompt_version_summary,
    }


@router.get("/analytics/recent-outputs")
async def get_recent_outputs(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    """
    Recent conversation plan outputs for manual review.
    
    Returns outputs with reflection metadata (no user data).
    Includes generation metadata for version tracking.
    """
    result = await db.execute(
        select(ReflectionOutput, Reflection.title, Reflection.situation)
        .join(Reflection, ReflectionOutput.reflection_id == Reflection.id)
        .order_by(ReflectionOutput.created_at.desc())
        .limit(limit)
    )
    rows = result.all()
    
    return [
        {
            "reflection_title": title,
            "reflection_situation": situation[:200] + "..." if len(situation) > 200 else situation,
            "output_id": output.id,
            "output_created_at": output.created_at.isoformat(),
            "emotional_summary": output.emotional_summary,
            "needs_summary": output.needs_summary,
            "reframe": output.reframe,
            "conversation_opener": output.conversation_opener,
            # Generation metadata for version tracking
            "prompt_version": output.prompt_version or "unknown",
            "model_provider": output.model_provider or "unknown",
            "model_name": output.model_name or "unknown",
            "generation_mode": output.generation_mode or "unknown",
            "safety_version": output.safety_version or "unknown",
            # Human review status
            "human_review_status": output.human_review_status or "pending_review",
        }
        for output, title, situation in rows
    ]


@router.get("/analytics/safety-events")
async def get_safety_events(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    """
    Recent safety events for review.
    
    Returns event type, severity, timestamp, and reason.
    Does not include reflection content (for privacy).
    """
    result = await db.execute(
        select(SafetyEvent)
        .order_by(SafetyEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "severity": e.severity,
            "created_at": e.created_at.isoformat(),
            "model_response": e.model_response[:200] + "..." if e.model_response and len(e.model_response) > 200 else e.model_response,
        }
        for e in events
    ]


@router.patch("/outputs/{output_id}/review")
async def update_output_review_status(
    output_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    """
    Update human review status for an output.
    
    Used during internal review to flag outputs for:
    - excellent: best-in-class output worth studying
    - approved: acceptable quality
    - needs_prompt_revision: below standard, requires prompt iteration
    - flagged: safety concern or unexpected output
    
    Status values: pending_review | approved | flagged | excellent | needs_prompt_revision
    """
    valid_statuses = {"pending_review", "approved", "flagged", "excellent", "needs_prompt_revision"}
    
    new_status = data.get("human_review_status", "")
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    result = await db.execute(
        select(ReflectionOutput).where(ReflectionOutput.id == output_id)
    )
    output = result.scalar_one_or_none()
    
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    output.human_review_status = new_status
    await db.commit()
    
    return {
        "output_id": output.id,
        "human_review_status": output.human_review_status,
        "message": f"Status updated to {new_status}",
    }

"""
Reflection API routes.

Endpoints:
- POST /reflections - Create a new reflection
- GET /reflections - List all reflections for current user
- GET /reflections/{id} - Get a specific reflection
- PUT /reflections/{id} - Update a reflection
- DELETE /reflections/{id} - Delete a reflection
- POST /reflections/{id}/generate - Generate a conversation plan
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Reflection
from app.schemas.reflection import (
    CreateReflectionRequest,
    UpdateReflectionRequest,
    ReflectionResponse,
    ReflectionFeedbackResponse,
    GenerateResponse,
    CreateFeedbackRequest,
    UpdateFeedbackRequest,
    MemorySuggestionData,
)
from app.services import (
    ReflectionService,
    SafetyService,
    FacilitationService,
    ExtractionService,
)
from app.services.safety_service import check_safety, build_crisis_response


# ─── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/reflections", tags=["reflections"])


# ─── Auth Dependency ───────────────────────────────────────────────────────────

async def get_current_user(authorization: str = None) -> dict:
    """
    Returns user payload. For MVP 1, always returns a dev user.
    In MVP 2, integrate Clerk or Supabase auth.
    """
    USE_AUTH = os.environ.get("USE_AUTH", "false") == "true"
    
    if USE_AUTH:
        if not authorization or not authorization.startswith("Bearer "):
            return None
        # TODO: Decode token based on AUTH_PROVIDER
        return None
    
    # Dev mode: return a dev user
    return {"sub": "dev-user-001", "email": "dev@feltabout.local", "name": "Dev User"}


async def require_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return current_user


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ReflectionResponse, status_code=201)
async def create_reflection(
    data: CreateReflectionRequest,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new reflection."""
    await ReflectionService.ensure_user(db, user)
    reflection = await ReflectionService.create(db, user["sub"], data)
    return reflection


@router.get("", response_model=list[ReflectionResponse])
async def list_reflections(
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """List all reflections for the current user."""
    reflections = await ReflectionService.list_by_user(db, user["sub"])
    return reflections


@router.get("/{reflection_id}", response_model=ReflectionResponse)
async def get_reflection(
    reflection_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific reflection by ID."""
    reflection = await ReflectionService.get_by_id(db, reflection_id, user["sub"])
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    return reflection


@router.put("/{reflection_id}", response_model=ReflectionResponse)
async def update_reflection(
    reflection_id: str,
    data: UpdateReflectionRequest,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a reflection's fields."""
    reflection = await ReflectionService.get_by_id(db, reflection_id, user["sub"])
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    updated = await ReflectionService.update(db, reflection, data)
    return updated


@router.delete("/{reflection_id}", status_code=204)
async def delete_reflection(
    reflection_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a reflection."""
    reflection = await ReflectionService.get_by_id(db, reflection_id, user["sub"])
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    await ReflectionService.delete(db, reflection)


@router.post("/{reflection_id}/generate", response_model=GenerateResponse)
async def generate_plan(
    reflection_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a conversation plan for a reflection.
    
    Pipeline:
    1. Safety check (Safety Engine) — gates all generation
    2. Emotional analysis (Extraction Engine) — internal, not user-facing
    3. Conversation planning (Facilitation Engine) — uses analysis context
    4. FeelFlow event logging — for timeline visualization
    
    Only these are exposed to users:
    - emotion_distribution (derived from analysis)
    - memory_suggestion (optional: first candidate if detected)
    - conversation_plan (final output)
    - safety_status
    
    InternalAnalysis is NOT exposed to users.
    """
    # Fetch reflection
    reflection = await ReflectionService.get_by_id(db, reflection_id, user["sub"])
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    
    # Build reflection dict
    reflection_dict = {
        "situation": reflection.situation,
        "feelings": reflection.feelings,
        "interpretation": reflection.interpretation,
        "needs": reflection.needs,
        "fears": reflection.fears,
        "desired_outcome": reflection.desired_outcome,
        "message_draft": reflection.message_draft,
    }
    
    # ── Safety pre-check (Safety Engine) ──────────────────────────────────────
    all_text = ReflectionService.get_reflection_text(reflection)
    safety_result = check_safety(all_text)
    
    if safety_result.is_crisis:
        await SafetyService.log_safety_event(
            db=db,
            user_id=user["sub"],
            reflection_id=reflection_id,
            event_type="crisis_precheck",
            severity=safety_result.severity,
            reason=safety_result.reason,
        )
        return build_crisis_response(safety_result.severity)
    
    # ── Extraction (Extraction Engine) ─────────────────────────────────────────
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    
    extraction = ExtractionService()
    analysis = await extraction.analyze_with_fallback(
        reflection=reflection_dict,
        api_key=OPENAI_API_KEY if OPENAI_API_KEY else None,
        model=OPENAI_MODEL,
    )
    
    # Log memory candidate count
    memory_candidate_count = len(analysis.memory_candidates)
    
    # Convert analysis to dict for facilitation
    analysis_dict = {
        "primary_emotions": [
            {"name": e.name.value, "intensity": e.intensity, "source_text": e.source_text}
            for e in analysis.primary_emotions
        ],
        "secondary_emotions": [
            {"name": e.name.value, "intensity": e.intensity, "source_text": e.source_text}
            for e in analysis.secondary_emotions
        ],
        "needs": [
            {"category": n.category.value, "text": n.text, "intensity": n.intensity}
            for n in analysis.needs
        ],
        "conflict_markers": [
            {"type": m.type.value, "evidence": m.evidence, "severity": m.severity, "user_side": m.user_side}
            for m in analysis.conflict_markers
        ],
        "shame_markers": [
            {"shame_type": m.shame_type.value, "text_evidence": m.text_evidence, 
             "underlying_fear": m.underlying_fear, "is_hidden_anger": m.is_hidden_anger}
            for m in analysis.shame_markers
        ],
        "attachment_markers": [
            {"fear_type": m.fear_type.value, "text_evidence": m.text_evidence,
             "protest_behavior": m.protest_behavior, "withdrawal_behavior": m.withdrawal_behavior}
            for m in analysis.attachment_markers
        ],
        "nervous_system_markers": [
            {"state": m.state.value, "evidence": m.evidence, 
             "is_overwhelmed": m.is_overwhelmed, "is_dysregulated": m.is_dysregulated}
            for m in analysis.nervous_system_markers
        ],
        "memory_candidates": [
            {
                "title": m.title, "summary": m.summary,
                "privacy_default": m.privacy_default.value,
                "save_recommendation": m.save_recommendation,
                "reason": m.reason.value, "reason_text": m.reason_text,
            }
            for m in analysis.memory_candidates
        ],
        "conversation_risks": [
            {"risk_type": r.risk_type, "severity": r.severity, 
             "evidence": r.evidence, "recommendation": r.recommendation}
            for r in analysis.conversation_risks
        ],
    }
    
    # ── Facilitation (Facilitation Engine) ───────────────────────────────────
    facilitation = FacilitationService()
    
    if OPENAI_API_KEY:
        plan_data = await facilitation.generate_with_analysis(
            reflection=reflection_dict,
            analysis=analysis_dict,
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
        )
        metadata = {
            "prompt_version": "facilitation_mvp2_v1",
            "prompt_version_extraction": "extraction_v1",
            "extraction_model": OPENAI_MODEL,
            "analysis_confidence": 0.85,
            "memory_candidate_count": memory_candidate_count,
            "model_provider": "openai",
            "model_name": OPENAI_MODEL,
            "generation_mode": "staged_extraction",
            "safety_version": "safety_rules_v1",
        }
    else:
        plan_data = facilitation._fallback_with_analysis(reflection_dict, analysis_dict)
        metadata = {
            "prompt_version": "facilitation_mvp2_v1",
            "prompt_version_extraction": "extraction_fallback_v1",
            "extraction_model": "fallback",
            "analysis_confidence": 0.5,
            "memory_candidate_count": memory_candidate_count,
            "model_provider": "local_fallback",
            "model_name": "fallback",
            "generation_mode": "staged_extraction",
            "safety_version": "safety_rules_v1",
        }
    
    # Save output with generation metadata
    output = await ReflectionService.save_output(db, reflection, plan_data, metadata)
    
    # ── FeelFlow event logging ──────────────────────────────────────────────────
    from app.services.feelflow_service import FeelFlowService
    all_emotions = analysis_dict.get("primary_emotions", []) + analysis_dict.get("secondary_emotions", [])
    await FeelFlowService.save_events(db, user["sub"], reflection_id, all_emotions)
    
    # Build memory suggestion if candidates detected
    memory_suggestion = None
    if analysis.memory_candidates:
        first_candidate = analysis.memory_candidates[0]
        memory_suggestion = MemorySuggestionData(
            title=first_candidate.title,
            summary=first_candidate.summary,
            reason=first_candidate.reason_text or first_candidate.reason.value,
            reflection_id=reflection_id,
        )
    
    # Build response
    return GenerateResponse(
        is_crisis=False,
        severity="none",
        message="Your conversation plan is ready.",
        resources=[],
        output=output,
        memory_suggestion=memory_suggestion,
    )


# ─── Feedback Routes ───────────────────────────────────────────────────────────

@router.post("/{reflection_id}/feedback", response_model=ReflectionFeedbackResponse, status_code=201)
async def submit_feedback(
    reflection_id: str,
    data: CreateFeedbackRequest,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit feedback after viewing a conversation plan.
    
    Questions:
    1. Do you feel more prepared for the conversation?
    2. Do you feel less reactive than before?
    3. What was most helpful? (optional)
    
    Scores: 1=No, 2=Somewhat, 3=Yes
    """
    reflection = await ReflectionService.get_by_id(db, reflection_id, user["sub"])
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    
    feedback = await ReflectionService.save_feedback(
        db=db,
        reflection_id=reflection_id,
        user_id=user["sub"],
        data=data,
    )
    return feedback


@router.get("/{reflection_id}/feedback", response_model=ReflectionFeedbackResponse)
async def get_feedback(
    reflection_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get feedback for a specific reflection."""
    reflection = await ReflectionService.get_by_id(db, reflection_id, user["sub"])
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    
    feedback = await ReflectionService.get_feedback(
        db=db,
        reflection_id=reflection_id,
        user_id=user["sub"],
    )
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


@router.patch("/{reflection_id}/feedback", response_model=ReflectionFeedbackResponse)
async def update_feedback(
    reflection_id: str,
    data: UpdateFeedbackRequest,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update feedback — used for the follow-up question after the conversation.
    
    "Did the conversation go better than expected?"
    """
    feedback = await ReflectionService.get_feedback(db, reflection_id, user["sub"])
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    updated = await ReflectionService.update_feedback(db, feedback, data)
    return updated

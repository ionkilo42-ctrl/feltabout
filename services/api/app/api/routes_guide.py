"""
Guide Me session API routes.

Implements the structured Guide Me reflection flow with 12 stages:
safe_opening → first_expression → feeling_identification → intensity_capture →
validation → about_mapping → memory_discovery → meaning_discovery →
need_discovery → purpose_of_feeling → constructive_path →
reflection_review → save_or_signup

Endpoints:
- POST /guide-sessions           — Start a new Guide Me session
- GET /guide-sessions/{id}       — Get current session state
- POST /guide-sessions/{id}/respond — Send a user message, get Aimee's reply
- POST /guide-sessions/{id}/generate-card — Generate Reflection Card from session data
- PATCH /guide-sessions/{id}/card — Update/edit the Reflection Card
- POST /guide-sessions/{id}/save  — Save verified card as a Reflection
- GET /guide-sessions            — List all sessions for current user
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes_auth import require_user
from app.db.session import get_db
from app.models.guide_session import GuideSession
from app.schemas.guide_session import (
    GuideSessionResponse,
    AimeeReplyResponse,
    GenerateCardResponse,
    UpdateCardRequest,
    SaveSessionRequest,
    ConversationMessage,
    CollectedFeeling,
    CollectedAboutLink,
    CollectedNeed,
    ReflectionCard,
)
from app.services.guide_service import GuideService, dump_history, load_history
from app.services.reflection_service import ReflectionService
from app.services.safety_service import SafetyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guide-sessions", tags=["guide-sessions"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _session_to_response(session: GuideSession) -> GuideSessionResponse:
    """Convert a GuideSession model to a response schema."""
    history = load_history(session.conversation_history or "[]")
    feelings_raw = json.loads(session.collected_feelings or "[]")
    about_raw = json.loads(session.collected_about_links or "[]")
    needs_raw = json.loads(session.collected_needs or "[]")
    context_raw = json.loads(session.collected_context or "{}")
    card_raw = None
    if session.reflection_card:
        card_raw = json.loads(session.reflection_card)

    return GuideSessionResponse(
        id=session.id,
        user_id=session.user_id,
        status=session.status,
        current_stage=session.current_stage,
        conversation_history=history,
        collected_feelings=[CollectedFeeling(**f) for f in feelings_raw],
        collected_about_links=[CollectedAboutLink(**a) for a in about_raw],
        collected_needs=[CollectedNeed(**n) for n in needs_raw],
        collected_context=context_raw,
        reflection_card=ReflectionCard(**card_raw) if card_raw else None,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _feelings_to_json(feelings: list[CollectedFeeling]) -> str:
    return json.dumps([f.model_dump() for f in feelings])


def _about_to_json(about_links: list[CollectedAboutLink]) -> str:
    return json.dumps([a.model_dump() for a in about_links])


def _needs_to_json(needs: list[CollectedNeed]) -> str:
    return json.dumps([n.model_dump() for n in needs])


def _context_to_json(context: dict) -> str:
    return json.dumps(context)


def _card_to_json(card: ReflectionCard) -> str:
    return card.model_dump_json()


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("", response_model=GuideSessionResponse, status_code=201)
async def create_guide_session(
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new Guide Me session."""
    await ReflectionService.ensure_user(db, user)

    guide = GuideService()
    opening, history = await guide.start_session()

    session = GuideSession(
        user_id=user["sub"],
        status="active",
        current_stage="safe_opening",
        conversation_history=dump_history(history),
        collected_feelings="[]",
        collected_about_links="[]",
        collected_needs="[]",
        collected_context="{}",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(
        "Guide session started",
        extra={"session_id": session.id, "user_id": user["sub"]},
    )

    return _session_to_response(session)


@router.get("", response_model=list[GuideSessionResponse])
async def list_guide_sessions(
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """List all Guide Me sessions for the current user."""
    result = await db.execute(
        select(GuideSession)
        .where(GuideSession.user_id == user["sub"])
        .order_by(GuideSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [_session_to_response(s) for s in sessions]


@router.get("/{session_id}", response_model=GuideSessionResponse)
async def get_guide_session(
    session_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current state of a Guide Me session."""
    result = await db.execute(
        select(GuideSession).where(
            GuideSession.id == session_id,
            GuideSession.user_id == user["sub"],
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Guide session not found")
    return _session_to_response(session)


@router.post("/{session_id}/respond", response_model=AimeeReplyResponse)
async def respond_to_guide_session(
    session_id: str,
    user_message: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a user message in a Guide Me session.

    Safety check runs first. If crisis detected, returns crisis response.
    Otherwise, Aimee responds and the stage may advance.
    """
    result = await db.execute(
        select(GuideSession).where(
            GuideSession.id == session_id,
            GuideSession.user_id == user["sub"],
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Guide session not found")

    if session.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Guide session is {session.status}, not active",
        )

    # Load session data
    history = load_history(session.conversation_history or "[]")
    feelings_raw = json.loads(session.collected_feelings or "[]")
    about_raw = json.loads(session.collected_about_links or "[]")
    needs_raw = json.loads(session.collected_needs or "[]")
    context_raw = json.loads(session.collected_context or "{}")

    collected_feelings = [CollectedFeeling(**f) for f in feelings_raw]
    collected_about_links = [CollectedAboutLink(**a) for a in about_raw]
    collected_needs = [CollectedNeed(**n) for n in needs_raw]

    # Process the response
    guide = GuideService()
    result_dict = await guide.process_response(
        user_input=user_message,
        conversation_history=history,
        current_stage=session.current_stage,
        collected_feelings=collected_feelings,
        collected_about_links=collected_about_links,
        collected_needs=collected_needs,
        collected_context=context_raw,
    )

    # Update session
    session.conversation_history = dump_history(result_dict["conversation_history"])
    session.current_stage = result_dict["new_stage"]
    session.collected_feelings = _feelings_to_json(result_dict["collected_feelings"])
    session.collected_about_links = _about_to_json(result_dict["collected_about_links"])
    session.collected_needs = _needs_to_json(result_dict["collected_needs"])
    session.collected_context = _context_to_json(result_dict["collected_context"])

    # Mark completed if reached save_or_signup
    if session.current_stage == "save_or_signup":
        session.status = "completed"

    await db.commit()
    await db.refresh(session)

    logger.info(
        "Guide session message",
        extra={
            "session_id": session_id,
            "user_id": user["sub"],
            "stage": session.current_stage,
            "stage_advanced": result_dict["stage_advanced"],
        },
    )

    return AimeeReplyResponse(
        reply=result_dict["reply"],
        session=_session_to_response(session),
        stage_advanced=result_dict["stage_advanced"],
        new_stage=result_dict["new_stage"],
        is_crisis=result_dict["is_crisis"],
        safety_resources=result_dict["safety_resources"],
    )


@router.post("/{session_id}/generate-card", response_model=GenerateCardResponse)
async def generate_reflection_card(
    session_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate the Reflection Card from collected session data."""
    result = await db.execute(
        select(GuideSession).where(
            GuideSession.id == session_id,
            GuideSession.user_id == user["sub"],
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Guide session not found")

    # Load session data
    history = load_history(session.conversation_history or "[]")
    feelings_raw = json.loads(session.collected_feelings or "[]")
    about_raw = json.loads(session.collected_about_links or "[]")
    needs_raw = json.loads(session.collected_needs or "[]")
    context_raw = json.loads(session.collected_context or "{}")

    guide = GuideService()
    card = await guide.generate_reflection_card(
        collected_feelings=[CollectedFeeling(**f) for f in feelings_raw],
        collected_about_links=[CollectedAboutLink(**a) for a in about_raw],
        collected_needs=[CollectedNeed(**n) for n in needs_raw],
        collected_context=context_raw,
        conversation_history=history,
    )

    # Save card to session
    session.reflection_card = _card_to_json(card)
    session.current_stage = "reflection_review"
    await db.commit()
    await db.refresh(session)

    logger.info(
        "Reflection card generated",
        extra={"session_id": session_id, "user_id": user["sub"]},
    )

    return GenerateCardResponse(
        card=card,
        session=_session_to_response(session),
    )


@router.patch("/{session_id}/card", response_model=GuideSessionResponse)
async def update_reflection_card(
    session_id: str,
    data: UpdateCardRequest,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Update/edit the Reflection Card before saving."""
    result = await db.execute(
        select(GuideSession).where(
            GuideSession.id == session_id,
            GuideSession.user_id == user["sub"],
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Guide session not found")

    if not session.reflection_card:
        raise HTTPException(status_code=400, detail="No reflection card to update")

    # Load existing card
    card_dict = json.loads(session.reflection_card)

    # Apply updates
    if data.title is not None:
        card_dict["title"] = data.title
    if data.feelings is not None:
        card_dict["feelings"] = [f.model_dump() for f in data.feelings]
    if data.about_links is not None:
        card_dict["about_links"] = [a.model_dump() for a in data.about_links]
    if data.needs is not None:
        card_dict["needs"] = data.needs
    if data.memory_summary is not None:
        card_dict["memory_summary"] = data.memory_summary
    if data.purpose_of_feeling is not None:
        card_dict["purpose_of_feeling"] = data.purpose_of_feeling
    if data.constructive_path is not None:
        card_dict["constructive_path"] = data.constructive_path
    if data.suggested_words is not None:
        card_dict["suggested_words"] = data.suggested_words

    session.reflection_card = json.dumps(card_dict)
    await db.commit()
    await db.refresh(session)

    return _session_to_response(session)


@router.post("/{session_id}/save")
async def save_guide_session(
    session_id: str,
    data: SaveSessionRequest,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save the verified Reflection Card as a Reflection.

    This converts the Guide Me session output into a standard Reflection
    that appears in the user's library.
    """
    result = await db.execute(
        select(GuideSession).where(
            GuideSession.id == session_id,
            GuideSession.user_id == user["sub"],
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Guide session not found")

    if not session.reflection_card:
        raise HTTPException(status_code=400, detail="No reflection card to save")

    if not data.save:
        session.status = "abandoned"
        await db.commit()
        return {"status": "skipped", "message": "Reflection card was not saved."}

    # Load card
    card_dict = json.loads(session.reflection_card)

    # Build simple_opener from suggested_words (first suggestion)
    suggested_words = card_dict.get("suggested_words", [])
    simple_opener = suggested_words[0] if suggested_words else ""

    # Build plan_data for ReflectionOutput
    plan_data = {
        "simple_opener": simple_opener,
        "emotional_summary": card_dict.get("memory_summary", ""),
        "needs_summary": ", ".join(card_dict.get("needs", [])),
        "assumptions": "",
        "reframe": card_dict.get("purpose_of_feeling", ""),
        "avoid_saying": "",
        "conversation_opener": simple_opener,
        "followup_questions": "",
        "repair_statement": card_dict.get("constructive_path", ""),
    }

    # Create a Reflection from the card
    # First expression from context
    context_raw = json.loads(session.collected_context or "{}")
    first_expression = context_raw.get("first_expression", card_dict.get("title", ""))

    reflection = await ReflectionService.create(
        db=db,
        user_id=user["sub"],
        data={
            "title": card_dict.get("title", "Guide Me reflection"),
            "situation": first_expression,
            "feelings": ", ".join(f['name'] for f in card_dict.get("feelings", [])),
            "interpretation": card_dict.get("purpose_of_feeling", ""),
            "needs": ", ".join(card_dict.get("needs", [])),
            "fears": "",
            "desired_outcome": "",
            "message_draft": simple_opener,
        },
    )

    # Save output
    await ReflectionService.save_output(
        db=db,
        reflection=reflection,
        plan_data=plan_data,
        metadata={
            "prompt_version": "guide_me_mvp_v1",
            "generation_mode": "guided_reflection",
        },
    )

    # Mark session complete
    session.status = "completed"
    await db.commit()

    logger.info(
        "Guide session saved",
        extra={
            "session_id": session_id,
            "user_id": user["sub"],
            "reflection_id": reflection.id,
        },
    )

    return {
        "status": "saved",
        "message": "Reflection saved to your library.",
        "reflection_id": reflection.id,
    }
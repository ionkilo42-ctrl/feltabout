"""Aimee extraction routes for v2 emotional graph.

POST /v2/aimee/extract - Propose emotional extraction (no save)
POST /v2/aimee/confirm - Save confirmed extraction to emotional graph

These routes are INTERNAL/DEVELOPMENT only for MVP 1.
They require authentication and are disabled in production unless ALLOW_V2=true.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.v2.aimee import (
    ExtractionRequest,
    ExtractionResponse,
    ConfirmRequest,
    ConfirmResponse,
    ChatRequest,
    ChatResponse,
)
from app.services.v2.aimee_service import extract_emotions, confirm_extraction, chat_with_aimee
from app.api.routes_auth import require_user, check_v2_access

router = APIRouter(prefix="/v2/aimee", tags=["v2-aimee"])


@router.post("/extract", response_model=ExtractionResponse)
async def extract(
    request: ExtractionRequest,
    current_user: dict = Depends(require_user),
):
    """Extract emotional meaning without saving."""
    check_v2_access()
    _user_id = current_user["sub"]
    return await extract_emotions(request)


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm(
    request: ConfirmRequest,
    current_user: dict = Depends(require_user),
):
    """Save user-confirmed extraction to the emotional graph."""
    check_v2_access()
    user_id = current_user["sub"]
    try:
        return await confirm_extraction(request, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save memory")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(require_user),
):
    """Chat with Aimee using the signed-in user context."""
    check_v2_access()
    _user_id = current_user["sub"]
    return await chat_with_aimee(request)

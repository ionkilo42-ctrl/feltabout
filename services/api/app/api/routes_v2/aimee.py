"""Aimee extraction routes for v2 emotional graph.

POST /v2/aimee/extract - Propose emotional extraction (no save)
POST /v2/aimee/confirm - Save confirmed extraction to emotional graph

These routes are INTERNAL/DEVELOPMENT only for MVP 1.
They require authentication and are disabled in production unless ALLOW_V2=true.
"""

import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.v2.aimee import (
    ExtractionRequest,
    ExtractionResponse,
    ConfirmRequest,
    ConfirmResponse,
    ChatRequest,
    ChatResponse,
)
from app.services.v2.aimee_service import extract_emotions, confirm_extraction, chat_with_aimee
from app.api.routes_auth import require_user

router = APIRouter(prefix="/v2/aimee", tags=["v2-aimee"])


def _check_v2_access():
    """Check if v2 routes are allowed in current environment."""
    allow_v2 = os.environ.get("ALLOW_V2", "false").lower() == "true"
    is_production = os.environ.get("ENVIRONMENT", "development") == "production"
    
    if is_production and not allow_v2:
        raise HTTPException(
            status_code=403,
            detail="V2 routes are not enabled in production. Set ALLOW_V2=true to enable."
        )


@router.post("/extract", response_model=ExtractionResponse)
async def extract(
    request: ExtractionRequest,
    current_user: dict = Depends(require_user),
):
    """Check environment access."""
    _check_v2_access()
    user_id = current_user["sub"]
    """
    Extract emotional meaning from text.
    
    This endpoint PROPOSES only - it does NOT save anything.
    User must review and confirm via /v2/aimee/confirm.
    
    Safety check runs before extraction.
    Crisis/unsafe input returns safe response (no extraction).
    """
    return await extract_emotions(request)


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm(
    request: ConfirmRequest,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    _check_v2_access()
    user_id = current_user["sub"]
    """
    Save user-confirmed extraction to emotional graph.
    
    This is the ONLY endpoint that saves emotional data.
    Only user-confirmed or user-edited data gets saved.
    """
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
    """Check environment access."""
    _check_v2_access()
    user_id = current_user["sub"]
    """
    Free-form conversational chat with Aimee.
    
    This is Aimee's guide voice - warm, listening, asking questions.
    Safety check runs first. Crisis input returns crisis response.
    
    Returns conversational reply, not structured extraction.
    """
    return await chat_with_aimee(request)

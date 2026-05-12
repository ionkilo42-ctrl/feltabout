"""Aimee conversational chat routes.

POST /aimee/chat - Free-form conversational chat with Aimee.
Does not extract structured data (see /v2/aimee/extract for extraction).
"""

import logging
from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

from app.llm_minimax import generate_aimee_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/aimee", tags=["aimee"])


# ─── Request/Response Models ──────────────────────────────────────────────────────

class AimeeChatRequest(BaseModel):
    """Request body for /aimee/chat."""
    message: str = Field(
        ...,
        min_length=1,
        description="The user's message to Aimee"
    )
    context: str | None = Field(
        default=None,
        description="Optional conversation context (previous messages)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "I feel angry about what happened at work",
                    "context": None
                },
                {
                    "message": "I'm not sure what I'm feeling",
                    "context": "Previous conversation history..."
                }
            ]
        }
    }


class AimeeChatResponse(BaseModel):
    """Response body for /aimee/chat."""
    reply: str = Field(
        ...,
        description="Aimee's conversational response"
    )


# ─── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=AimeeChatResponse)
async def chat(request: AimeeChatRequest) -> AimeeChatResponse:
    """
    Conversational chat with Aimee.
    
    Aimee provides emotionally intelligent, reflective responses.
    This is a free-form chat endpoint - for structured extraction, use /v2/aimee/extract.
    
    Safety:
    - Messages are NOT logged or stored (per feltabout privacy principles)
    - No user identification is stored with chat messages
    """
    # Validate message is not just whitespace
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    try:
        reply = await generate_aimee_response(
            user_message=request.message,
            context=request.context
        )
        return AimeeChatResponse(reply=reply)
        
    except ValueError as e:
        # API key not configured
        logger.warning(f"Aimee chat failed: MiniMax not configured")
        raise HTTPException(
            status_code=503,
            detail="AI service not configured. Please set MINIMAX_API_KEY."
        )
        
    except Exception as e:
        # Log error without exposing details
        logger.error(f"Aimee chat error: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get response. Please try again."
        )
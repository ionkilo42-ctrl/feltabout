"""
Pattern Insights API routes.

Endpoints:
- GET /patterns - Get pattern insights for current user

Requires at least 3 completed reflections.
No DB storage — in-memory cache only.
"""

import time
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.patterns_service import analyze_user_patterns, PatternsResult
from app.services import ReflectionService
from app.api.routes_auth import require_user


# ─── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/patterns", tags=["patterns"])


# ─── Simple in-memory cache ────────────────────────────────────────────────────

_cache: dict[str, tuple[PatternsResult, float]] = {}
_CACHE_TTL = 3600  # 1 hour


def _get_cached(user_id: str) -> Optional[PatternsResult]:
    """Return cached result if fresh, else None."""
    if user_id in _cache:
        result, timestamp = _cache[user_id]
        if time.time() - timestamp < _CACHE_TTL:
            return result
        del _cache[user_id]
    return None


def _set_cached(user_id: str, result: PatternsResult) -> None:
    """Cache result for 1 hour."""
    _cache[user_id] = (result, time.time())


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def get_patterns(
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get pattern insights for the current user.
    
    Returns insights only when user has at least 3 completed reflections.
    Results are cached for 1 hour.
    
    Pattern types:
    - recurring_emotion: Same emotion keyword in 2+ reflections
    - recurring_need: Same need keyword in 2+ reflections
    - conflict_context: Topic cluster in 2+ reflections
    
    Language is always gentle and observational, never diagnostic.
    """
    user_id = user["sub"]
    
    # Check cache first
    cached = _get_cached(user_id)
    if cached:
        return _to_response(cached)
    
    # Get all completed reflections (decrypted via service)
    reflections = await ReflectionService.list_by_user(db, user_id)
    completed = [r for r in reflections if r.status == "completed"]
    
    # Build reflection dicts for analysis
    reflection_dicts = [
        {
            "situation": r.situation or "",
            "feelings": r.feelings or "",
            "interpretation": r.interpretation or "",
            "needs": r.needs or "",
            "desired_outcome": r.desired_outcome or "",
            "message_draft": r.message_draft or "",
        }
        for r in completed
    ]
    
    # Analyze patterns
    result = analyze_user_patterns(reflection_dicts)
    
    # Cache even if empty (prevents re-analysis)
    _set_cached(user_id, result)
    
    return _to_response(result)


def _to_response(result: PatternsResult) -> dict:
    """Convert PatternsResult to API response dict."""
    return {
        "patterns": [
            {
                "type": p.type,
                "insight": p.insight,
                "occurrences": p.occurrences,
                "confidence": p.confidence,
                "examples": p.examples,
            }
            for p in result.patterns
        ],
        "total_reflections_analyzed": result.total_reflections_analyzed,
        "requires_minimum": result.requires_minimum,
    }

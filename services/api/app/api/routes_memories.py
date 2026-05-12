"""
Core Memory API routes.

Endpoints:
- POST /memories - Create a user-confirmed memory
- GET /memories - List all memories for current user
- GET /memories/{id} - Get a specific memory
- PUT /memories/{id} - Update a memory
- DELETE /memories/{id} - Delete a memory
- POST /memories/{id}/dismiss - Record dismissal for learning
"""

import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.core_memory import (
    CreateCoreMemoryRequest,
    UpdateCoreMemoryRequest,
    CoreMemoryResponse,
    CoreMemoryListResponse,
)
from app.services.core_memory_service import CoreMemoryService
from app.api.routes_auth import require_user


# ─── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/memories", tags=["memories"])


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=CoreMemoryResponse, status_code=201)
async def create_memory(
    data: CreateCoreMemoryRequest,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a user-confirmed Core Memory.
    
    This endpoint requires explicit user confirmation before saving.
    Memory candidates from AI analysis are suggestions only — 
    this endpoint creates actual saved memories.
    """
    memory = await CoreMemoryService.create(db, user["sub"], data)
    return CoreMemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        title=memory.title,
        summary=memory.summary,
        emotions_json=memory.emotions_json,
        needs=memory.needs,
        privacy=memory.privacy,
        source_reflection_id=memory.source_reflection_id,
        user_confirmed=memory.user_confirmed,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


@router.get("", response_model=CoreMemoryListResponse)
async def list_memories(
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """List all Core Memories for the current user."""
    memories = await CoreMemoryService.list_by_user(db, user["sub"])
    return CoreMemoryListResponse(
        memories=[
            CoreMemoryResponse(
                id=m.id,
                user_id=m.user_id,
                title=m.title,
                summary=m.summary,
                emotions_json=m.emotions_json,
                needs=m.needs,
                privacy=m.privacy,
                source_reflection_id=m.source_reflection_id,
                user_confirmed=m.user_confirmed,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in memories
        ],
        total=len(memories),
    )


@router.get("/{memory_id}", response_model=CoreMemoryResponse)
async def get_memory(
    memory_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific Core Memory by ID."""
    memory = await CoreMemoryService.get_by_id(db, memory_id, user["sub"])
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return CoreMemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        title=memory.title,
        summary=memory.summary,
        emotions_json=memory.emotions_json,
        needs=memory.needs,
        privacy=memory.privacy,
        source_reflection_id=memory.source_reflection_id,
        user_confirmed=memory.user_confirmed,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


@router.put("/{memory_id}", response_model=CoreMemoryResponse)
async def update_memory(
    memory_id: str,
    data: UpdateCoreMemoryRequest,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a Core Memory's fields."""
    memory = await CoreMemoryService.get_by_id(db, memory_id, user["sub"])
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    updated = await CoreMemoryService.update(db, memory, data)
    return CoreMemoryResponse(
        id=updated.id,
        user_id=updated.user_id,
        title=updated.title,
        summary=updated.summary,
        emotions_json=updated.emotions_json,
        needs=updated.needs,
        privacy=updated.privacy,
        source_reflection_id=updated.source_reflection_id,
        user_confirmed=updated.user_confirmed,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a Core Memory and its associated FeelFlow events."""
    memory = await CoreMemoryService.get_by_id(db, memory_id, user["sub"])
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    await CoreMemoryService.delete(db, memory)


@router.post("/{memory_id}/dismiss", status_code=204)
async def dismiss_memory(
    memory_id: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Record dismissal of a memory candidate to prevent repeated suggestions.
    
    This is used for learning — when a user dismisses a suggested memory,
    the system records this to avoid suggesting similar memories again.
    
    The candidate_key is a hash of the memory content for matching.
    """
    # Get the memory to generate candidate key
    memory = await CoreMemoryService.get_by_id(db, memory_id, user["sub"])
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Generate candidate key from memory content
    content = f"{memory.title}:{memory.summary}"
    candidate_key = hashlib.sha256(content.encode()).hexdigest()[:32]
    
    await CoreMemoryService.dismiss_candidate(
        db=db,
        user_id=user["sub"],
        candidate_key=candidate_key,
        reason="user_dismissed",
    )


@router.post("/dismiss-candidate", status_code=204)
async def dismiss_candidate_by_content(
    title: str,
    summary: str,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Record dismissal of a memory candidate by its content.
    
    Used when user dismisses a suggested memory without saving.
    The candidate_key is generated from the memory content.
    """
    content = f"{title}:{summary}"
    candidate_key = hashlib.sha256(content.encode()).hexdigest()[:32]
    
    await CoreMemoryService.dismiss_candidate(
        db=db,
        user_id=user["sub"],
        candidate_key=candidate_key,
        reason="user_dismissed",
    )

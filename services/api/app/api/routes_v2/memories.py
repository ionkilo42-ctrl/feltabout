"""Memory API routes for v2.

These routes are INTERNAL/DEVELOPMENT only for MVP 1.
They require authentication and are disabled in production unless ALLOW_V2=true.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.routes_auth import require_user, check_v2_access
from app.schemas.v2.memory import (
    CreateMemoryRequest,
    MemoryResponse,
    NestedMemoryResponse,
)
from app.schemas.v2.feeling import FeelingWithRelations
from app.schemas.v2.need import NeedResponse
from app.schemas.v2.entity import EntityResponse
from app.schemas.v2.topic import TopicResponse
from app.services.v2.memory_service import MemoryService

router = APIRouter(prefix="/v2/memories", tags=["v2-memories"])


@router.post("", response_model=NestedMemoryResponse, status_code=201)
async def create_memory(
    data: CreateMemoryRequest,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    check_v2_access()
    user_id = current_user["sub"]
    """Create a memory with nested feelings, needs, entities, and topics."""
    memory = await MemoryService.create_with_nested(db, user_id, data)
    
    # Collect unique needs/entities/topics by ID
    seen_needs, seen_entities, seen_topics = set(), set(), set()
    needs_list, entities_list, topics_list = [], [], []
    
    for f in memory.feelings:
        for n in f.needs:
            if n.id not in seen_needs:
                seen_needs.add(n.id)
                needs_list.append(NeedResponse.model_validate(n))
        for e in f.entities:
            if e.id not in seen_entities:
                seen_entities.add(e.id)
                entities_list.append(EntityResponse.model_validate(e))
        for t in f.topics:
            if t.id not in seen_topics:
                seen_topics.add(t.id)
                topics_list.append(TopicResponse.model_validate(t))
    
    return NestedMemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        title=memory.title,
        narrative=memory.narrative,
        ai_summary=memory.ai_summary,
        occurred_at=memory.occurred_at,
        privacy_level=memory.privacy_level,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        feelings=[FeelingWithRelations.model_validate(f) for f in memory.feelings],
        needs=sorted(needs_list, key=lambda x: x.name),
        entities=sorted(entities_list, key=lambda x: x.canonical_name),
        topics=sorted(topics_list, key=lambda x: x.title),
    )


@router.get("", response_model=List[MemoryResponse])
async def list_memories(
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    check_v2_access()
    user_id = current_user["sub"]
    """List all memories for the current user."""
    memories = await MemoryService.list_by_user(db, user_id)
    return [MemoryResponse.model_validate(m) for m in memories]


@router.get("/{memory_id}", response_model=NestedMemoryResponse)
async def get_memory(
    memory_id: str,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    check_v2_access()
    user_id = current_user["sub"]
    """Get a specific memory with all relationships."""
    memory = await MemoryService.get_by_id(db, memory_id, user_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Collect unique needs/entities/topics
    seen_needs, seen_entities, seen_topics = set(), set(), set()
    needs_list, entities_list, topics_list = [], [], []
    for f in memory.feelings:
        for n in f.needs:
            if n.id not in seen_needs:
                seen_needs.add(n.id)
                needs_list.append(NeedResponse.model_validate(n))
        for e in f.entities:
            if e.id not in seen_entities:
                seen_entities.add(e.id)
                entities_list.append(EntityResponse.model_validate(e))
        for t in f.topics:
            if t.id not in seen_topics:
                seen_topics.add(t.id)
                topics_list.append(TopicResponse.model_validate(t))
    
    return NestedMemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        title=memory.title,
        narrative=memory.narrative,
        ai_summary=memory.ai_summary,
        occurred_at=memory.occurred_at,
        privacy_level=memory.privacy_level,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        feelings=[FeelingWithRelations.model_validate(f) for f in memory.feelings],
        needs=sorted(needs_list, key=lambda x: x.name),
        entities=sorted(entities_list, key=lambda x: x.canonical_name),
        topics=sorted(topics_list, key=lambda x: x.title),
    )


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Check environment access."""
    check_v2_access()
    user_id = current_user["sub"]
    """Delete a memory and its associated feelings."""
    memory = await MemoryService.get_by_id(db, memory_id, user_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    await MemoryService.delete(db, memory)
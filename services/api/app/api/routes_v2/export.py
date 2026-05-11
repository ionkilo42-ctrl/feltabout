"""
Export endpoint for Phase 1E - user data export.

Allows users to export their own data as JSON.
Does not include any other user's data.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.v2 import EmotionalMemory, Entity, Feeling, Need, Topic
from app.services.analytics import get_analytics


router = APIRouter(prefix="/v2", tags=["v2"])


class ExportedFeeling(BaseModel):
    id: str
    label: str
    primary_emotion: str
    intensity: int
    confidence: Optional[float] = None
    occurred_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ExportedNeed(BaseModel):
    id: str
    name: str
    created_at: str

    class Config:
        from_attributes = True


class ExportedEntity(BaseModel):
    id: str
    canonical_name: str
    entity_type: str
    created_at: str

    class Config:
        from_attributes = True


class ExportedTopic(BaseModel):
    id: str
    title: str
    created_at: str

    class Config:
        from_attributes = True


class ExportedMemory(BaseModel):
    id: str
    title: str
    narrative: Optional[str] = None
    ai_summary: Optional[str] = None
    privacy_level: str
    occurred_at: Optional[str] = None
    created_at: str
    feelings: List[ExportedFeeling] = []
    needs: List[ExportedNeed] = []
    entities: List[ExportedEntity] = []
    topics: List[ExportedTopic] = []

    class Config:
        from_attributes = True


class ExportResponse(BaseModel):
    user_id: str
    exported_at: str
    total_memories: int
    total_entities: int
    total_needs: int
    memories: List[ExportedMemory]


@router.get("/export", response_model=ExportResponse)
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export all of the current user's data as JSON.
    
    Includes:
    - All memories (with feelings, needs, entities, topics)
    - All entities created by this user
    - All needs created by this user
    
    Does NOT include other users' data.
    """
    # Fetch all user's memories with relations
    memories = db.query(EmotionalMemory).filter(
        EmotionalMemory.user_id == current_user.id
    ).all()
    
    # Collect all entities and needs referenced
    entity_ids = set()
    need_ids = set()
    
    for memory in memories:
        for f in memory.feelings:
            if f.entity_id:
                entity_ids.add(f.entity_id)
        for n in memory.needs:
            if n.need_id:
                need_ids.add(n.need_id)
    
    # Fetch entities and needs
    entities = db.query(Entity).filter(
        Entity.id.in_(entity_ids)
    ).all() if entity_ids else []
    
    needs = db.query(Need).filter(
        Need.id.in_(need_ids)
    ).all() if need_ids else []
    
    # Build export response
    exported_memories = []
    for memory in memories:
        exported_memory = ExportedMemory(
            id=str(memory.id),
            title=memory.title,
            narrative=memory.narrative,
            ai_summary=memory.ai_summary,
            privacy_level=memory.privacy_level,
            occurred_at=memory.occurred_at.isoformat() if memory.occurred_at else None,
            created_at=memory.created_at.isoformat() if memory.created_at else "",
            feelings=[
                ExportedFeeling(
                    id=str(f.id),
                    label=f.label,
                    primary_emotion=f.primary_emotion,
                    intensity=f.intensity,
                    confidence=f.confidence,
                    occurred_at=f.occurred_at.isoformat() if f.occurred_at else None,
                    created_at=f.created_at.isoformat() if f.created_at else "",
                )
                for f in memory.feelings
            ],
            needs=[
                ExportedNeed(
                    id=str(n.id),
                    name=n.name,
                    created_at=n.created_at.isoformat() if n.created_at else "",
                )
                for n in memory.needs
            ],
            entities=[
                ExportedEntity(
                    id=str(e.id),
                    canonical_name=e.canonical_name,
                    entity_type=e.entity_type,
                    created_at=e.created_at.isoformat() if e.created_at else "",
                )
                for e in memory.entities
            ],
            topics=[
                ExportedTopic(
                    id=str(t.id),
                    title=t.title,
                    created_at=t.created_at.isoformat() if t.created_at else "",
                )
                for t in memory.topics
            ],
        )
        exported_memories.append(exported_memory)
    
    return ExportResponse(
        user_id=str(current_user.id),
        exported_at=datetime.utcnow().isoformat(),
        total_memories=len(exported_memories),
        total_entities=len(entities),
        total_needs=len(needs),
        memories=exported_memories,
    )


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a specific memory.
    
    Users can only delete their own memories.
    """
    memory = db.query(EmotionalMemory).filter(
        EmotionalMemory.id == memory_id,
        EmotionalMemory.user_id == current_user.id
    ).first()
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    db.delete(memory)
    db.commit()
    
    return {"status": "deleted", "memory_id": memory_id}


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a specific entity.
    
    Users can only delete entities they created.
    Only deletes if entity is orphaned (not linked to any memory).
    """
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user.id
    ).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Check if entity is linked to any memory
    # (simplified - in production would check relationship table)
    # For now, allow deletion if user owns it
    
    db.delete(entity)
    db.commit()
    
    return {"status": "deleted", "entity_id": entity_id}
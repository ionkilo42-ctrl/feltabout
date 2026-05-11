"""Memory service for v2 emotional graph.

Handles creation of memories with nested feelings, needs, entities, and topics.
This is the core service for storing confirmed emotional data from Aimee.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.v2 import (
    Memory, 
    Feeling, 
    Need, 
    Entity, 
    Topic,
    feeling_needs,
    feeling_entities,
    feeling_topics,
)


class MemoryService:
    """Service for managing memories and their nested relationships."""
    
    @staticmethod
    async def ensure_user_exists(db: AsyncSession, user_id: str) -> None:
        """Ensure user exists in database."""
        from app.models.user import User
        result = await db.execute(select(User).where(User.id == user_id))
        if not result.scalar_one_or_none():
            user = User(
                id=user_id,
                email=f"{user_id}@v2.local",
                display_name=f"User {user_id[:8]}",
            )
            db.add(user)
            await db.commit()
    
    @staticmethod
    async def get_or_create_need(db: AsyncSession, user_id: str, name: str) -> str:
        """Get existing need by name or create new one, return need_id."""
        result = await db.execute(
            select(Need).where(Need.user_id == user_id, Need.name == name)
        )
        need = result.scalar_one_or_none()
        if not need:
            need = Need(
                id=uuid.uuid4().hex[:16],
                user_id=user_id,
                name=name,
            )
            db.add(need)
            await db.flush()
        return need.id
    
    @staticmethod
    async def get_or_create_entity(
        db: AsyncSession, 
        user_id: str, 
        name: str,
        entity_type: str = "person"
    ) -> str:
        """Get existing entity by name or create new one, return entity_id."""
        result = await db.execute(
            select(Entity).where(Entity.canonical_name == name)
        )
        entity = result.scalar_one_or_none()
        if not entity:
            entity = Entity(
                id=uuid.uuid4().hex[:16],
                user_id=user_id,
                canonical_name=name,
                entity_type=entity_type,
                privacy_level="private",
            )
            db.add(entity)
            await db.flush()
        return entity.id
    
    @staticmethod
    async def get_or_create_topic(db: AsyncSession, user_id: str, title: str) -> str:
        """Get existing topic by title or create new one, return topic_id."""
        result = await db.execute(
            select(Topic).where(Topic.user_id == user_id, Topic.title == title)
        )
        topic = result.scalar_one_or_none()
        if not topic:
            topic = Topic(
                id=uuid.uuid4().hex[:16],
                user_id=user_id,
                title=title,
            )
            db.add(topic)
            await db.flush()
        return topic.id
    
    @staticmethod
    async def create_with_nested(
        db: AsyncSession,
        user_id: str,
        data,
    ) -> Memory:
        """Create a memory with nested feelings, needs, entities, and topics.
        
        Uses direct table inserts for association tables to avoid async issues.
        """
        # Ensure user exists
        await MemoryService.ensure_user_exists(db, user_id)
        
        # Get or create related object IDs
        need_ids = []
        for need_name in data.need_names:
            need_id = await MemoryService.get_or_create_need(db, user_id, need_name)
            need_ids.append(need_id)
        
        entity_ids = []
        for entity_name in data.entity_names:
            entity_id = await MemoryService.get_or_create_entity(db, user_id, entity_name)
            entity_ids.append(entity_id)
        
        topic_ids = []
        for topic_title in data.topic_titles:
            topic_id = await MemoryService.get_or_create_topic(db, user_id, topic_title)
            topic_ids.append(topic_id)
        
        # Create memory
        memory = Memory(
            id=uuid.uuid4().hex[:16],
            user_id=user_id,
            title=data.title,
            narrative=data.narrative,
            ai_summary=data.ai_summary,
            occurred_at=data.occurred_at or datetime.utcnow(),
            privacy_level=data.privacy_level,
        )
        db.add(memory)
        await db.flush()
        
        # Create feelings
        feeling_ids = []
        for feeling_data in data.feelings:
            feeling = Feeling(
                id=uuid.uuid4().hex[:16],
                user_id=user_id,
                primary_emotion=feeling_data.primary_emotion,
                label=feeling_data.label,
                intensity=feeling_data.intensity,
                confidence=feeling_data.confidence,
                source_text=feeling_data.source_text,
                memory_id=memory.id,
                occurred_at=feeling_data.occurred_at or memory.occurred_at,
            )
            db.add(feeling)
            await db.flush()
            feeling_ids.append(feeling.id)
        
        # Create association records directly
        for feeling_id in feeling_ids:
            for need_id in need_ids:
                await db.execute(feeling_needs.insert().values(
                    feeling_id=feeling_id,
                    need_id=need_id,
                    confidence=0.5,
                    user_confirmed=True,
                ))
            
            for entity_id in entity_ids:
                await db.execute(feeling_entities.insert().values(
                    feeling_id=feeling_id,
                    entity_id=entity_id,
                    relationship_type="about",
                    confidence=0.5,
                    user_confirmed=True,
                ))
            
            for topic_id in topic_ids:
                await db.execute(feeling_topics.insert().values(
                    feeling_id=feeling_id,
                    topic_id=topic_id,
                    confidence=0.5,
                    user_confirmed=True,
                ))
        
        await db.commit()
        
        # Fetch memory with relationships
        return await MemoryService.get_by_id(db, memory.id, user_id)
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        memory_id: str,
        user_id: str,
    ) -> Optional[Memory]:
        """Get memory by ID with all relationships."""
        result = await db.execute(
            select(Memory)
            .options(
                selectinload(Memory.feelings).selectinload(Feeling.needs),
                selectinload(Memory.feelings).selectinload(Feeling.entities),
                selectinload(Memory.feelings).selectinload(Feeling.topics),
            )
            .where(Memory.id == memory_id, Memory.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Memory]:
        """List all memories for a user."""
        result = await db.execute(
            select(Memory)
            .options(selectinload(Memory.feelings))
            .where(Memory.user_id == user_id)
            .order_by(Memory.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def delete(db: AsyncSession, memory: Memory) -> None:
        """Delete a memory and its cascading feelings."""
        await db.delete(memory)
        await db.commit()
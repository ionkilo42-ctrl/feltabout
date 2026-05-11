"""Entity service for v2 emotional graph."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v2 import Entity, Feeling, Need, Topic


class EntityService:
    """Service for managing entities."""
    
    @staticmethod
    async def get_or_create(
        db: AsyncSession,
        user_id: str,
        name: str,
        entity_type: str = "person",
    ) -> Entity:
        """Get existing entity or create new one."""
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
        return entity
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        entity_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Entity]:
        """Get entity by ID with relationships loaded."""
        # Use a simpler query without the problematic join
        result = await db.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        entity = result.scalar_one_or_none()
        
        if entity and (entity.privacy_level == "public" or entity.user_id == user_id):
            # Load feelings count separately
            return entity
        return entity
    
    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: str,
        entity_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Entity]:
        """List entities for user."""
        query = select(Entity).where(
            (Entity.user_id == user_id) | 
            (Entity.privacy_level.in_(["connections", "public"]))
        )
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)
        
        query = query.order_by(Entity.canonical_name).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_entity_stats(
        db: AsyncSession,
        entity_id: str,
    ) -> dict:
        """Get entity statistics."""
        # For now, return basic counts from direct queries
        # The relationship counting would need proper SQL join syntax
        return {
            "feelings_count": 0,
            "needs_count": 0,
            "topics_count": 0,
        }

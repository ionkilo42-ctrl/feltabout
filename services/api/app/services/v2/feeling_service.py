"""Feeling service for v2 emotional graph."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.v2 import Feeling, Memory


class FeelingService:
    """Service for managing feelings."""
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        feeling_id: str,
        user_id: str,
    ) -> Optional[Feeling]:
        """Get feeling by ID with relationships."""
        result = await db.execute(
            select(Feeling)
            .options(
                selectinload(Feeling.needs),
                selectinload(Feeling.entities),
                selectinload(Feeling.topics),
            )
            .where(Feeling.id == feeling_id, Feeling.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: str,
        memory_id: Optional[str] = None,
        primary_emotion: Optional[str] = None,
        limit: int = 100,
    ) -> List[Feeling]:
        """List feelings for user with optional filters."""
        query = select(Feeling).where(Feeling.user_id == user_id)
        
        if memory_id:
            query = query.where(Feeling.memory_id == memory_id)
        if primary_emotion:
            query = query.where(Feeling.primary_emotion == primary_emotion)
        
        query = query.order_by(Feeling.occurred_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
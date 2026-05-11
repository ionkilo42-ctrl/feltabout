"""Need service for v2 emotional graph."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.v2 import Need, Feeling


class NeedService:
    """Service for managing needs."""
    
    @staticmethod
    async def get_or_create(
        db: AsyncSession,
        user_id: str,
        name: str,
        description: str = "",
    ) -> Need:
        """Get existing need or create new one."""
        result = await db.execute(
            select(Need).where(Need.user_id == user_id, Need.name == name)
        )
        need = result.scalar_one_or_none()
        if not need:
            need = Need(
                id=uuid.uuid4().hex[:16],
                user_id=user_id,
                name=name,
                description=description,
            )
            db.add(need)
            await db.flush()
        return need
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        need_id: str,
        user_id: str,
    ) -> Optional[Need]:
        """Get need by ID with relationships."""
        result = await db.execute(
            select(Need)
            .options(
                selectinload(Need.feelings),
            )
            .where(Need.id == need_id, Need.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: str,
        limit: int = 100,
    ) -> List[Need]:
        """List all needs for user."""
        result = await db.execute(
            select(Need)
            .where(Need.user_id == user_id)
            .order_by(Need.name)
            .limit(limit)
        )
        return list(result.scalars().all())
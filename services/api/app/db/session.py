"""
Database session management for feltabout API.
Provides async SQLAlchemy session factory and dependency injection.
"""

import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/feltabout"
)

# ─── Engine Setup ─────────────────────────────────────────────────────────────

engine_kwargs = {"echo": False, "pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs = {"echo": False, "poolclass": StaticPool}

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ─── Session Dependency ────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    async with async_session_factory() as session:
        yield session


# ─── Initialization ────────────────────────────────────────────────────────────

async def init_db():
    """Initialize database tables and ensure dev user exists."""
    from app.models.base import Base  # Imports v1 models' Base
    from app.models.user import User
    from sqlalchemy import select
    
    # Import v2 models to register them with Base.metadata
    from app.models.v2 import (
        Feeling, Need, Entity, Topic, Memory, Guide, PublicEntityAggregate,
        feeling_needs, feeling_entities, feeling_topics
    )
    
    # Create all tables (both v1 and v2 share the same Base)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Ensure dev user exists
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.id == "dev-user-001"))
        if not result.scalar_one_or_none():
            dev_user = User(
                id="dev-user-001",
                email="dev@feltabout.local",
                display_name="Dev User",
            )
            session.add(dev_user)
            await session.commit()
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
    """Initialize database: run schema migrations, create tables, ensure dev user."""
    from app.models.base import Base  # Imports v1 models' Base
    from app.models.user import User
    from sqlalchemy import select, text

    # Import v2 models to register them with Base.metadata
    from app.models.v2 import (
        Feeling, Need, Entity, Topic, Memory, Guide, PublicEntityAggregate,
        feeling_needs, feeling_entities, feeling_topics
    )
    # Import GuideSession to register it with Base.metadata
    from app.models.guide_session import GuideSession  # noqa: F401

    USE_AUTH = os.environ.get("USE_AUTH", "false").lower() == "false"

    # ── 1. Create all tables FIRST ───────────────────────────────────────────────
    # Fresh DB:  users table is created WITH is_admin via the model
    # Existing DB: users table already exists (with or without is_admin)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── 2. Additive migration: add is_admin to existing users table if missing ──
    # Only needed for pre-existing DBs created before is_admin was added to the model.
    # Fresh DBs: create_all already added the column, so this silently no-ops.
    async with engine.begin() as conn:
        if DATABASE_URL.startswith("sqlite"):
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            if "is_admin" not in columns:
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0;"
                ))
        else:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;"
            ))

    # ── 3. Ensure dev user exists and has admin in dev mode ──────────────────────
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.id == "dev-user-001"))
        dev_user = result.scalar_one_or_none()
        if not dev_user:
            dev_user = User(
                id="dev-user-001",
                email="dev@feltabout.local",
                display_name="Dev User",
                is_admin=True,  # Dev user is admin only in local/dev mode
            )
            session.add(dev_user)
        else:
            # Grant admin to existing dev user in dev mode
            dev_user.is_admin = True
        await session.commit()

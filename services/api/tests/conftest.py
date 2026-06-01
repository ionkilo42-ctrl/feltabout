import os

import pytest
import pytest_asyncio
from sqlalchemy import delete

from app.db.session import async_session_factory, init_db
from app.main import app
from app.models.base import Base
from app.services import ai_router as ai_router_module


@pytest.fixture(autouse=True)
def reset_test_globals(monkeypatch):
    """Reset process-wide mutable state that can leak across test modules."""
    monkeypatch.setenv("AI_PROVIDER", "local")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("MINIMAX_API_KEY", "")
    app.dependency_overrides.clear()
    ai_router_module._default_router = None
    yield
    app.dependency_overrides.clear()
    ai_router_module._default_router = None


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    """Keep the shared in-memory sqlite DB empty between tests."""
    await init_db()
    async with async_session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()

"""
Library API tests for the unified reflection/conversation hub.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("AI_PROVIDER", "local")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("ENCRYPTION_KEY", "nY1jcI7NI5vxhAXu7r_MT4h84trDxTcf6dzWTqtlSUU=")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import init_db
from app.main import app


@pytest.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def enable_auth():
    previous = os.environ.get("USE_AUTH")
    os.environ["USE_AUTH"] = "true"
    yield
    if previous is None:
        os.environ.pop("USE_AUTH", None)
    else:
        os.environ["USE_AUTH"] = previous


async def register_user(client) -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "email": "library-owner@example.com",
            "password": "stable-pass-123",
            "display_name": "Library Owner",
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_library_combines_plain_reflections_and_conversation_spaces(client):
    auth = await register_user(client)
    headers = {"Authorization": f"Bearer {auth['token']}"}

    reflection_response = await client.post(
        "/reflections",
        headers=headers,
        json={
            "title": "",
            "situation": "A direct conversation about shared expectations.",
            "feelings": "Clear and a little nervous",
        },
    )
    assert reflection_response.status_code == 201

    space_response = await client.post(
        "/conversation-spaces",
        headers=headers,
        json={"name": "Shared prep", "max_participants": 2},
    )
    assert space_response.status_code == 201

    library_response = await client.get("/library", headers=headers)

    assert library_response.status_code == 200
    items = library_response.json()["items"]
    names = [item["name"] for item in items]
    assert "Shared prep" in names
    assert "A direct conversation about shared expectations." in names
    assert all(not name.startswith("enc:v1:") for name in names)

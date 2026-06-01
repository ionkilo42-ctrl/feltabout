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
from sqlalchemy import select

from app.db.session import init_db
from app.db.session import async_session_factory
from app.main import app
from app.models.v2 import Memory


@pytest.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def enable_auth():
    previous = os.environ.get("USE_AUTH")
    previous_allow_v2 = os.environ.get("ALLOW_V2")
    os.environ["USE_AUTH"] = "true"
    os.environ["ALLOW_V2"] = "true"
    yield
    if previous is None:
        os.environ.pop("USE_AUTH", None)
    else:
        os.environ["USE_AUTH"] = previous
    if previous_allow_v2 is None:
        os.environ.pop("ALLOW_V2", None)
    else:
        os.environ["ALLOW_V2"] = previous_allow_v2


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


@pytest.mark.asyncio
async def test_library_includes_authenticated_aimee_memories_and_classic_reflections(client):
    auth = await register_user(client)
    headers = {"Authorization": f"Bearer {auth['token']}"}
    user_id = auth["user"]["id"]

    reflection_response = await client.post(
        "/reflections",
        headers=headers,
        json={
            "title": "",
            "situation": "Need to talk through how last night landed.",
            "feelings": "Tender and defensive",
        },
    )
    assert reflection_response.status_code == 201

    confirm_response = await client.post(
        "/v2/aimee/confirm",
        headers=headers,
        json={
            "source_text": "I keep replaying the argument and I want to say this more clearly.",
            "memory_title": "After the argument",
            "memory_narrative": "Trying to understand what I actually want to say next.",
            "feelings": [
                {
                    "primary_emotion": "sadness",
                    "label": "hurt",
                    "intensity": 6,
                    "confidence": 0.82,
                    "source_text": "I keep replaying the argument",
                    "entity_names": ["Partner"],
                    "topic_titles": ["recent argument"],
                    "need_names": ["understanding"],
                }
            ],
        },
    )
    assert confirm_response.status_code == 200
    memory_id = confirm_response.json()["memory_id"]

    async with async_session_factory() as session:
        result = await session.execute(select(Memory).where(Memory.id == memory_id))
        memory = result.scalar_one()

    assert memory.user_id == user_id
    assert memory.user_id != "dev-user-001"

    library_response = await client.get("/library", headers=headers)
    assert library_response.status_code == 200

    items = library_response.json()["items"]
    by_id = {item["id"]: item for item in items}

    assert memory_id in by_id
    assert by_id[memory_id]["name"] == "After the argument"
    assert by_id[memory_id]["type"] == "memory"
    assert by_id[memory_id]["status"] == "completed"
    assert by_id[memory_id]["subtitle"] == "Aimee reflection"

    reflection_names = [item["name"] for item in items if item["type"] == "reflection"]
    assert "Need to talk through how last night landed." in reflection_names

"""
Conversation-space API tests for the MVP shared-prep flow.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

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
    previous_auth = os.environ.get("USE_AUTH")
    previous_frontend = os.environ.get("FRONTEND_URL")
    os.environ["USE_AUTH"] = "true"
    os.environ["FRONTEND_URL"] = "http://localhost:3000"
    yield
    if previous_auth is None:
        os.environ.pop("USE_AUTH", None)
    else:
        os.environ["USE_AUTH"] = previous_auth
    if previous_frontend is None:
        os.environ.pop("FRONTEND_URL", None)
    else:
        os.environ["FRONTEND_URL"] = previous_frontend


async def register_user(client, email: str = "space-owner@example.com") -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "stable-pass-123",
            "display_name": "Space Owner",
        },
    )
    assert response.status_code == 200
    return response.json()


def invite_token_from_url(invite_url: str) -> str:
    path = urlparse(invite_url).path
    return path.rstrip("/").split("/")[-1]


@pytest.mark.asyncio
async def test_create_verify_and_join_conversation_space(client):
    auth = await register_user(client)

    create_response = await client.post(
        "/conversation-spaces",
        headers={"Authorization": f"Bearer {auth['token']}"},
        json={"name": "Kitchen table conversation", "max_participants": 2},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Kitchen table conversation"
    assert created["invite_url"].startswith("http://localhost:3000/join/")

    token = invite_token_from_url(created["invite_url"])
    verify_response = await client.get(f"/conversation-spaces/verify-invite/{token}")
    assert verify_response.status_code == 200
    verified = verify_response.json()
    assert verified["valid"] is True
    assert verified["space_id"] == created["id"]
    assert verified["space_name"] == "Kitchen table conversation"
    assert verified["is_full"] is False

    join_response = await client.post(
        f"/conversation-spaces/{created['id']}/join",
        json={"display_name": "Guest Person"},
    )
    assert join_response.status_code == 200
    joined = join_response.json()
    assert joined["conversation_space_id"] == created["id"]
    assert joined["display_name"] == "Guest Person"
    assert joined["ws_access_token"]

    full_response = await client.get(f"/conversation-spaces/verify-invite/{token}")
    assert full_response.status_code == 200
    assert full_response.json()["valid"] is False


@pytest.mark.asyncio
async def test_owner_can_list_and_fetch_conversation_space(client):
    auth = await register_user(client, email="space-list-owner@example.com")

    create_response = await client.post(
        "/conversation-spaces",
        headers={"Authorization": f"Bearer {auth['token']}"},
        json={"name": "Weekly check-in", "max_participants": 2},
    )
    space_id = create_response.json()["id"]

    list_response = await client.get(
        "/conversation-spaces",
        headers={"Authorization": f"Bearer {auth['token']}"},
    )
    assert list_response.status_code == 200
    spaces = list_response.json()["spaces"]
    assert any(space["id"] == space_id for space in spaces)

    get_response = await client.get(
        f"/conversation-spaces/{space_id}",
        headers={"Authorization": f"Bearer {auth['token']}"},
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == space_id
    assert data["is_owner"] is True
    assert data["participant_count"] == 1

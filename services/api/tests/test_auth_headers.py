"""
Auth header integration tests.
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
from app.services.auth_service import create_conversation_token


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


async def register_user(client, email: str = "auth-header@example.com") -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "stable-pass-123",
            "display_name": "Auth Header User",
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_auth_me_accepts_bearer_authorization_header(client):
    auth = await register_user(client)

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {auth['token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "auth-header@example.com"
    assert data["name"] == "Auth Header User"


@pytest.mark.asyncio
async def test_password_register_login_and_hash_verification(client):
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "Casey.Login@Example.com",
            "password": "stable-pass-123",
            "display_name": "Casey Login",
        },
    )
    assert register_response.status_code == 200
    registered = register_response.json()
    assert registered["user"]["email"] == "casey.login@example.com"
    assert registered["user"]["name"] == "Casey Login"
    assert registered["token"]

    failed_login = await client.post(
        "/auth/login",
        json={"email": "casey.login@example.com", "password": "wrong-password"},
    )
    assert failed_login.status_code == 401
    assert failed_login.json()["detail"] == "Invalid email or password"

    login_response = await client.post(
        "/auth/login",
        json={"email": "casey.login@example.com", "password": "stable-pass-123"},
    )
    assert login_response.status_code == 200
    logged_in = login_response.json()
    assert logged_in["user"]["email"] == "casey.login@example.com"
    assert logged_in["token"]


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email_and_short_password(client):
    short_password = await client.post(
        "/auth/register",
        json={
            "email": "short-password@example.com",
            "password": "short",
            "display_name": "Short Password",
        },
    )
    assert short_password.status_code == 400
    assert short_password.json()["detail"] == "Password must be at least 8 characters"

    await register_user(client, email="duplicate@example.com")
    duplicate = await client.post(
        "/auth/register",
        json={
            "email": "DUPLICATE@example.com",
            "password": "stable-pass-123",
            "display_name": "Duplicate User",
        },
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "An account with this email already exists"


@pytest.mark.asyncio
async def test_reflections_use_authenticated_bearer_user(client):
    auth = await register_user(client, email="reflection-owner@example.com")

    response = await client.post(
        "/reflections",
        headers={"Authorization": f"Bearer {auth['token']}"},
        json={
            "title": "Private reflection",
            "situation": "I need to prepare for a direct conversation.",
            "feelings": "Nervous but clear",
            "interpretation": "",
            "needs": "Respect and clarity",
            "fears": "",
            "desired_outcome": "A calm conversation",
            "message_draft": "",
        },
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == auth["user"]["id"]


@pytest.mark.asyncio
async def test_auth_me_rejects_conversation_scoped_token(client):
    token = create_conversation_token(
        user_id="user-123",
        conversation_space_id="space-123",
        participant_id="participant-123",
        display_name="Guest Person",
        is_guest=True,
    )

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401

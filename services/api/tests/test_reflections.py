"""
Unit tests for feltabout API — reflection CRUD and AI generation path.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("AI_PROVIDER", "local")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "")
# Stable test key — must be valid Fernet (base64, 32 bytes). Generate with:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
os.environ.setdefault("ENCRYPTION_KEY", "nY1jcI7NI5vxhAXu7r_MT4h84trDxTcf6dzWTqtlSUU=")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.db.session import init_db
from app.db.session import async_session_factory
from app.models import Reflection

# ─── Test client fixture ───────────────────────────────────────────────────────

@pytest.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── Health ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "feltabout-api"


# ─── Create Reflection ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_reflection(client):
    payload = {
        "title": "Talk with my partner about the chores",
        "situation": "We had a tense morning where I felt overwhelmed.",
        "feelings": "Frustrated, unheard, exhausted",
        "interpretation": "Maybe they don't care about sharing the load",
        "needs": "Support, recognition, partnership",
        "fears": "That they'll get defensive or shut down",
        "desired_outcome": "A fair division of tasks we both stick to",
        "message_draft": "Hey, can we talk about how we're dividing things?",
    }
    resp = await client.post("/reflections", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == payload["title"]
    assert data["situation"] == payload["situation"]
    assert data["feelings"] == payload["feelings"]
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data
    reflection_id = data["id"]

    # Fetch it back
    resp2 = await client.get(f"/reflections/{reflection_id}")
    assert resp2.status_code == 200
    assert resp2.json()["title"] == payload["title"]
    return reflection_id


# ─── List Reflections ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_reflections(client):
    # Create a reflection first
    payload = {
        "title": "Discussion about finances",
        "situation": "We disagreed about spending priorities.",
        "feelings": "Anxious",
        "interpretation": "They're reckless with money",
        "needs": "Security",
        "fears": "We'll fall into debt",
        "desired_outcome": "Agree on a budget",
        "message_draft": "",
    }
    await client.post("/reflections", json=payload)

    resp = await client.get("/reflections")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ─── Update Reflection ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_reflection(client):
    # Create
    payload = {"title": "Old title", "situation": "Test situation", "feelings": "Confused", "interpretation": "", "needs": "", "fears": "", "desired_outcome": "", "message_draft": ""}
    resp = await client.post("/reflections", json=payload)
    assert resp.status_code == 201
    rid = resp.json()["id"]

    # Update
    resp2 = await client.put(
        f"/reflections/{rid}",
        json={
            "title": "New title",
            "status": "archived",
            "situation": "Updated plain situation",
            "feelings": "Updated plain feelings",
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["title"] == "New title"
    assert resp2.json()["status"] == "archived"
    assert resp2.json()["situation"] == "Updated plain situation"
    assert resp2.json()["feelings"] == "Updated plain feelings"


# ─── Delete Reflection ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_reflection(client):
    payload = {"title": "To be deleted", "situation": "X", "feelings": "X", "interpretation": "", "needs": "", "fears": "", "desired_outcome": "", "message_draft": ""}
    resp = await client.post("/reflections", json=payload)
    rid = resp.json()["id"]

    resp2 = await client.delete(f"/reflections/{rid}")
    assert resp2.status_code == 204

    resp3 = await client.get(f"/reflections/{rid}")
    assert resp3.status_code == 404


# ─── Generate Plan (local fallback, no API key) ────────────────────────────────

@pytest.mark.asyncio
async def test_generate_plan_local_fallback(client):
    payload = {
        "title": "Hard conversation at work",
        "situation": "My manager gave vague feedback that felt personal.",
        "feelings": "Confused and undervalued",
        "interpretation": "They're dissatisfied with me",
        "needs": "Clarity and respect",
        "fears": "Losing my job",
        "desired_outcome": "Clear feedback I can act on",
        "message_draft": "I'd like to discuss the feedback you gave.",
    }
    resp = await client.post("/reflections", json=payload)
    assert resp.status_code == 201
    rid = resp.json()["id"]

    resp2 = await client.post(f"/reflections/{rid}/generate")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["is_crisis"] is False
    assert data["severity"] == "none"
    assert data["output"] is not None
    output = data["output"]
    assert output["simple_opener"] != ""
    assert output["emotional_summary"] != ""
    assert output["conversation_opener"] != ""
    assert output["repair_statement"] != ""

    # Reflection should now be "completed"
    resp3 = await client.get(f"/reflections/{rid}")
    assert resp3.json()["status"] == "completed"

    async with async_session_factory() as session:
        result = await session.execute(select(Reflection).where(Reflection.id == rid))
        stored = result.scalar_one()
        assert stored.situation.startswith("enc:v1:")
        assert stored.feelings.startswith("enc:v1:")


# ─── Safety: Crisis keyword triggers crisis response ───────────────────────────

@pytest.mark.asyncio
async def test_generate_plan_crisis_response(client):
    payload = {
        "title": "Crisis reflection",
        "situation": "I've been thinking about ending it all.",
        "feelings": "Hopeless",
        "interpretation": "Things will never get better",
        "needs": "Help",
        "fears": "I don't want to exist anymore",
        "desired_outcome": "",
        "message_draft": "",
    }
    resp = await client.post("/reflections", json=payload)
    assert resp.status_code == 201
    rid = resp.json()["id"]

    resp2 = await client.post(f"/reflections/{rid}/generate")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["is_crisis"] is True
    assert data["severity"] == "critical"
    assert len(data["resources"]) > 0
    assert data["output"] is None


# ─── Safety: Abuse keyword triggers crisis response ────────────────────────────

@pytest.mark.asyncio
async def test_generate_plan_abuse_response(client):
    payload = {
        "title": "Safety concern",
        "situation": "My partner threatened me.",
        "feelings": "Scared",
        "interpretation": "I'm in danger",
        "needs": "Safety",
        "fears": "They will hurt me",
        "desired_outcome": "",
        "message_draft": "",
    }
    resp = await client.post("/reflections", json=payload)
    rid = resp.json()["id"]

    resp2 = await client.post(f"/reflections/{rid}/generate")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["is_crisis"] is True
    assert data["severity"] == "high"


# ─── Not found ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_nonexistent_reflection(client):
    resp = await client.get("/reflections/nonexistent-id-xyz")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_nonexistent_reflection(client):
    resp = await client.put("/reflections/nonexistent-id-xyz", json={"title": "X"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_reflection(client):
    resp = await client.delete("/reflections/nonexistent-id-xyz")
    assert resp.status_code == 404

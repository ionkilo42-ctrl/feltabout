"""
Feedback API tests — verify reflection feedback endpoints.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("AI_PROVIDER", "local")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db


@pytest.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── Submit Feedback ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_feedback(client):
    """User can submit feedback after viewing a conversation plan."""
    # Create a completed reflection
    payload = {
        "title": "Test reflection",
        "situation": "Test situation",
        "feelings": "Test feelings",
        "interpretation": "",
        "needs": "",
        "fears": "",
        "desired_outcome": "",
        "message_draft": "",
    }
    resp = await client.post("/reflections", json=payload)
    assert resp.status_code == 201
    rid = resp.json()["id"]
    
    # Generate plan first (needed for context)
    resp2 = await client.post(f"/reflections/{rid}/generate")
    assert resp2.status_code == 200
    
    # Submit feedback
    feedback_data = {
        "prepared_score": 3,
        "less_reactive_score": 2,
        "helpful_text": "The conversation opener was useful.",
    }
    resp3 = await client.post(f"/reflections/{rid}/feedback", json=feedback_data)
    assert resp3.status_code == 201
    data = resp3.json()
    assert data["prepared_score"] == 3
    assert data["less_reactive_score"] == 2
    assert data["helpful_text"] == "The conversation opener was useful."
    assert data["reflection_id"] == rid


@pytest.mark.asyncio
async def test_submit_feedback_update(client):
    """Submitting feedback twice updates the existing feedback."""
    # Create reflection and generate plan
    payload = {
        "title": "Test reflection",
        "situation": "Test situation",
        "feelings": "Test feelings",
        "interpretation": "",
        "needs": "",
        "fears": "",
        "desired_outcome": "",
        "message_draft": "",
    }
    resp = await client.post("/reflections", json=payload)
    rid = resp.json()["id"]
    await client.post(f"/reflections/{rid}/generate")
    
    # Submit first feedback
    resp2 = await client.post(f"/reflections/{rid}/feedback", json={
        "prepared_score": 2,
        "less_reactive_score": 2,
        "helpful_text": "First submission",
    })
    assert resp2.status_code == 201
    
    # Submit updated feedback
    resp3 = await client.post(f"/reflections/{rid}/feedback", json={
        "prepared_score": 3,
        "less_reactive_score": 3,
        "helpful_text": "Updated after thinking more",
    })
    assert resp3.status_code == 201
    data = resp3.json()
    assert data["prepared_score"] == 3
    assert data["less_reactive_score"] == 3


@pytest.mark.asyncio
async def test_get_feedback(client):
    """User can retrieve their feedback for a reflection."""
    # Create reflection and generate plan
    payload = {
        "title": "Test reflection",
        "situation": "Test situation",
        "feelings": "Test feelings",
        "interpretation": "",
        "needs": "",
        "fears": "",
        "desired_outcome": "",
        "message_draft": "",
    }
    resp = await client.post("/reflections", json=payload)
    rid = resp.json()["id"]
    await client.post(f"/reflections/{rid}/generate")
    
    # Submit feedback
    await client.post(f"/reflections/{rid}/feedback", json={
        "prepared_score": 3,
        "less_reactive_score": 3,
        "helpful_text": "Very helpful",
    })
    
    # Get feedback
    resp2 = await client.get(f"/reflections/{rid}/feedback")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["prepared_score"] == 3
    assert data["less_reactive_score"] == 3


@pytest.mark.asyncio
async def test_get_nonexistent_feedback(client):
    """Returns 404 when feedback doesn't exist."""
    resp = await client.get("/reflections/nonexistent-id/feedback")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_feedback_requires_completed_reflection(client):
    """Can only submit feedback for an existing reflection."""
    # Try to submit feedback for non-existent reflection
    resp = await client.post("/reflections/nonexistent-id/feedback", json={
        "prepared_score": 3,
        "less_reactive_score": 3,
        "helpful_text": "",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_feedback_scores_required(client):
    """Feedback requires prepared_score and less_reactive_score."""
    # Create reflection and generate plan
    payload = {
        "title": "Test reflection",
        "situation": "Test situation",
        "feelings": "Test feelings",
        "interpretation": "",
        "needs": "",
        "fears": "",
        "desired_outcome": "",
        "message_draft": "",
    }
    resp = await client.post("/reflections", json=payload)
    rid = resp.json()["id"]
    await client.post(f"/reflections/{rid}/generate")
    
    # Missing prepared_score
    resp2 = await client.post(f"/reflections/{rid}/feedback", json={
        "less_reactive_score": 3,
    })
    assert resp2.status_code == 422
    
    # Missing less_reactive_score
    resp3 = await client.post(f"/reflections/{rid}/feedback", json={
        "prepared_score": 3,
    })
    assert resp3.status_code == 422
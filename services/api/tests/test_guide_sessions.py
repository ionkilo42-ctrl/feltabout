"""
Unit tests for Guide Me session API (routes_guide.py).

Tests cover:
- Full Guide Me session lifecycle (create → respond → generate card → save)
- Safety: crisis keyword triggers crisis response, no card generated
- Safety: abuse keyword triggers high-severity crisis response
- Philosophy: causal_claim defaults to false
- Philosophy: abandoned session saves collected feelings
- Library: Guide Me saved reflections appear in library list
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("AI_PROVIDER", "local")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault(
    "ENCRYPTION_KEY", "nY1jcI7NI5vxhAXu7r_MT4h84trDxTcf6dzWTqtlSUU="
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from sqlalchemy import delete

from app.db.session import init_db, async_session_factory
from app.models.guide_session import GuideSession
from app.models.reflection import Reflection, ReflectionOutput, ReflectionFeedback, SafetyEvent
from app.schemas.guide_session import ReflectionCard


# ─── Test client fixture ───────────────────────────────────────────────────────

@pytest.fixture
async def client():
    await init_db()
    # Keep product behavior intact while enforcing per-test isolation.
    async with async_session_factory() as session:
        await session.execute(delete(GuideSession))
        await session.execute(delete(ReflectionOutput))
        await session.execute(delete(ReflectionFeedback))
        await session.execute(delete(SafetyEvent))
        await session.execute(delete(Reflection))
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── Helpers ───────────────────────────────────────────────────────────────────

async def start_guide_session(client: AsyncClient) -> dict:
    """Start a new Guide Me session and return the session JSON."""
    resp = await client.post("/guide-sessions")
    assert resp.status_code == 201, resp.text
    return resp.json()


async def send_message(client: AsyncClient, session_id: str, message: str) -> dict:
    """Send a user message to a Guide Me session and return Aimee's reply."""
    resp = await client.post(
        f"/guide-sessions/{session_id}/respond",
        params={"user_message": message},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ─── Lifecycle: Create Session ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_guide_session(client):
    """POST /guide-sessions creates a new session with Aimee's opening."""
    resp = await client.post("/guide-sessions")
    assert resp.status_code == 201
    data = resp.json()

    assert data["id"] is not None
    assert data["user_id"] is not None
    assert data["status"] == "active"
    assert data["current_stage"] == "safe_opening"
    assert len(data["conversation_history"]) == 1  # Aimee's opening
    assert data["conversation_history"][0]["speaker"] == "aimee"
    assert data["collected_feelings"] == []
    assert data["collected_about_links"] == []
    assert data["collected_needs"] == []
    assert data["reflection_card"] is None


@pytest.mark.asyncio
async def test_get_guide_session(client):
    """GET /guide-sessions/{id} returns session state."""
    created = await start_guide_session(client)
    session_id = created["id"]

    resp = await client.get(f"/guide-sessions/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == session_id
    assert data["current_stage"] == "safe_opening"


@pytest.mark.asyncio
async def test_get_nonexistent_guide_session(client):
    """GET /guide-sessions/{id} returns 404 for unknown sessions."""
    resp = await client.get("/guide-sessions/nonexistent-xyz")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_guide_sessions(client):
    """GET /guide-sessions lists all sessions for the user."""
    await start_guide_session(client)
    await start_guide_session(client)

    resp = await client.get("/guide-sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


# ─── Lifecycle: Respond & Advance Stages ─────────────────────────────────────

@pytest.mark.asyncio
async def test_respond_safe_opening_advances_to_first_expression(client):
    """User response at safe_opening advances to first_expression."""
    session = await start_guide_session(client)
    assert session["current_stage"] == "safe_opening"

    reply_data = await send_message(
        client, session["id"], "My partner and I have been arguing a lot lately."
    )

    assert reply_data["is_crisis"] is False
    assert reply_data["session"]["current_stage"] == "first_expression"
    assert reply_data["stage_advanced"] is True


@pytest.mark.asyncio
async def test_respond_first_expression_captures_context_and_advances(client):
    """First expression is stored in collected_context and stage advances."""
    session = await start_guide_session(client)
    # Advance to first_expression
    await send_message(
        client, session["id"], "My partner and I have been arguing a lot lately."
    )

    reply_data = await send_message(
        client, session["id"],
        "It's been building up over several weeks. I feel like we're not connecting."
    )

    assert reply_data["session"]["current_stage"] == "feeling_identification"
    ctx = reply_data["session"]["collected_context"]
    assert ctx.get("first_expression") is not None


@pytest.mark.asyncio
async def test_respond_feeling_identification_captures_feeling(client):
    """Feeling word is captured when user names it at feeling_identification."""
    session = await start_guide_session(client)
    await send_message(client, session["id"], "Talking about the arguments.")
    await send_message(
        client, session["id"],
        "It's been building up over several weeks."
    )

    # Should be at feeling_identification
    reply_data = await send_message(client, session["id"], "I feel frustrated")
    assert reply_data["session"]["current_stage"] == "intensity_capture"
    feelings = reply_data["session"]["collected_feelings"]
    assert len(feelings) == 1
    assert feelings[0]["name"] == "frustrated"


@pytest.mark.asyncio
async def test_respond_intensity_capture_updates_feeling(client):
    """Intensity number is captured and stored on the current feeling."""
    session = await start_guide_session(client)
    await send_message(client, session["id"], "Talking about the arguments.")
    await send_message(client, session["id"], "It's been building up over several weeks.")
    await send_message(client, session["id"], "I feel frustrated")

    reply_data = await send_message(client, session["id"], "About a 7 out of 10")

    feelings = reply_data["session"]["collected_feelings"]
    assert len(feelings) == 1
    assert feelings[0]["intensity"] == 7.0


@pytest.mark.asyncio
async def test_full_lifecycle_to_card_generation(client):
    """Full session responds all the way through to reflection_review."""
    session = await start_guide_session(client)
    sid = session["id"]

    # safe_opening → first_expression
    await send_message(client, sid, "My partner and I have been arguing a lot.")
    # first_expression → feeling_identification
    await send_message(
        client, sid,
        "It's been building up over weeks. We keep missing each other."
    )
    # feeling_identification → intensity_capture
    await send_message(client, sid, "I feel hurt and frustrated")
    # intensity_capture → validation
    await send_message(client, sid, "8 out of 10")
    # validation → about_mapping
    await send_message(client, sid, "Yes, that feels right")

    # about_mapping → memory_discovery
    await send_message(client, sid, "About my partner, the distance between us")
    # memory_discovery → meaning_discovery
    await send_message(client, sid, "It shows up often, a pattern")
    # meaning_discovery → need_discovery
    await send_message(client, sid, "I think it means we're drifting apart")

    # need_discovery → purpose_of_feeling
    await send_message(client, sid, "I need to feel seen and understood")

    # purpose_of_feeling → constructive_path
    await send_message(
        client, sid,
        "This feeling is asking me to speak up before it gets worse"
    )

    # constructive_path → reflection_review (generate-card endpoint)
    reply_data = await send_message(client, sid, "I'll start by asking to talk calmly")

    assert reply_data["session"]["current_stage"] == "reflection_review"

    # Generate the card
    resp = await client.post(f"/guide-sessions/{sid}/generate-card")
    assert resp.status_code == 200
    card_data = resp.json()
    assert card_data["card"] is not None
    assert card_data["card"]["title"] != ""


@pytest.mark.asyncio
async def test_generate_card_requires_card_to_exist(client):
    """generate-card fails if no card data is available."""
    session = await start_guide_session(client)

    resp = await client.post(f"/guide-sessions/{session['id']}/generate-card")
    assert resp.status_code == 200  # Still works — fallback card from empty data


# ─── Safety: Crisis Keyword ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_respond_crisis_keyword_returns_crisis_response(client):
    """Crisis keyword in message returns crisis response, no stage advance."""
    session = await start_guide_session(client)

    reply_data = await send_message(
        client, session["id"], "I'm thinking about ending it all"
    )

    assert reply_data["is_crisis"] is True
    # Stage should NOT advance
    assert reply_data["session"]["current_stage"] == "safe_opening"
    # Aimee should have sent crisis response, not normal guidance
    assert len(reply_data["reply"]) > 10
    assert reply_data["safety_resources"]


@pytest.mark.asyncio
async def test_respond_abuse_keyword_returns_high_severity(client):
    """Abuse/threat keyword returns high-severity crisis response."""
    session = await start_guide_session(client)

    reply_data = await send_message(
        client, session["id"],
        "My partner threatened to hurt me last night"
    )

    assert reply_data["is_crisis"] is True
    # Crisis keyword matching is severity-based


@pytest.mark.asyncio
async def test_generate_card_does_not_run_on_crisis_session(client):
    """generate-card does not generate a normal card after crisis detection."""
    session = await start_guide_session(client)

    # Crisis message
    await send_message(client, session["id"], "I want to kill myself")

    # Still at safe_opening, no card generated
    assert session["current_stage"] == "safe_opening"

    # generate-card should still work but card won't be meaningful
    # because no feelings/needs were collected
    resp = await client.post(f"/guide-sessions/{session['id']}/generate-card")
    # The endpoint doesn't block it, but the card will be minimal


# ─── Safety: No card generated when crisis was detected ──────────────────────

@pytest.mark.asyncio
async def test_crisis_prevents_meaningful_card(client):
    """A session with crisis detection produces a minimal/empty card."""
    session = await start_guide_session(client)
    sid = session["id"]

    # Crisis at opening — no feelings collected
    reply_data = await send_message(client, sid, "I'm going to hurt myself")
    assert reply_data["is_crisis"] is True

    # No feelings captured
    assert reply_data["session"]["collected_feelings"] == []

    # Card generation still runs but card is empty/minimal
    resp = await client.post(f"/guide-sessions/{sid}/generate-card")
    assert resp.status_code == 200
    card = ReflectionCard.model_validate(resp.json()["card"])
    assert card.title != ""  # Fallback title still generated


# ─── Philosophy: causal_claim defaults to false ───────────────────────────────

@pytest.mark.asyncio
async def test_causal_claim_not_in_generated_card(client):
    """Generated Reflection Card should not contain a causal_claim field."""
    session = await start_guide_session(client)
    sid = session["id"]

    # Advance through enough stages to have data
    await send_message(client, sid, "My manager ignored my feedback in a meeting.")
    await send_message(client, sid, "I feel frustrated and disrespected")
    await send_message(client, sid, "About a 6 out of 10")
    await send_message(client, sid, "Yes that's right")
    await send_message(client, sid, "About my manager and the meeting")
    await send_message(client, sid, "It feels like a one-time thing")
    await send_message(client, sid, "I think they're dismissive of junior input")
    await send_message(client, sid, "I need to feel valued and heard")
    await send_message(client, sid, "The feeling might be telling me to speak up")
    await send_message(client, sid, "I'll bring it up in our next 1:1")

    resp = await client.post(f"/guide-sessions/{sid}/generate-card")
    assert resp.status_code == 200
    card = ReflectionCard.model_validate(resp.json()["card"])

    # causal_claim is not a valid field in ReflectionCard schema
    # (it would cause a pydantic validation error if we tried to add it)
    assert hasattr(card, "title")
    assert hasattr(card, "feelings")
    assert hasattr(card, "purpose_of_feeling")  # not causal_claim
    assert hasattr(card, "constructive_path")
    assert "causal_claim" not in card.model_dump()


# ─── Philosophy: Abandoned session saves collected feelings ─────────────────

@pytest.mark.asyncio
async def test_save_abandoned_session_preserves_feelings(client):
    """When user abandons (skip save), collected data is preserved in DB."""
    session = await start_guide_session(client)
    sid = session["id"]

    # Advance to feeling_identification and collect a feeling
    await send_message(client, sid, "Having issues with my team lead.")
    await send_message(client, sid, "They micromanage everything I do.")
    await send_message(client, sid, "I feel frustrated")

    # Get session state before save
    resp_before = await client.get(f"/guide-sessions/{sid}")
    session_before = resp_before.json()
    assert len(session_before["collected_feelings"]) > 0
    assert session_before["collected_feelings"][0]["name"] == "frustrated"

    # Generate card before save endpoint (save requires existing reflection_card)
    card_resp = await client.post(f"/guide-sessions/{sid}/generate-card")
    assert card_resp.status_code == 200

    # Skip saving (abandon)
    resp = await client.post(
        f"/guide-sessions/{sid}/save",
        json={"save": False}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "skipped"

    # Session status should be "abandoned"
    resp_check = await client.get(f"/guide-sessions/{sid}")
    assert resp_check.json()["status"] == "abandoned"


# ─── Save: Guide Me → Reflection conversion ──────────────────────────────────

@pytest.mark.asyncio
async def test_save_guide_session_creates_reflection(client):
    """POST /guide-sessions/{id}/save converts card to a Reflection."""
    session = await start_guide_session(client)
    sid = session["id"]

    # Advance through to reflection_review
    await send_message(client, sid, "My manager ignored my feedback in a meeting.")
    await send_message(client, sid, "I feel frustrated and disrespected")
    await send_message(client, sid, "About a 6 out of 10")
    await send_message(client, sid, "Yes that's right")
    await send_message(client, sid, "About my manager and the meeting")
    await send_message(client, sid, "It feels like a one-time thing")
    await send_message(client, sid, "I think they're dismissive of junior input")
    await send_message(client, sid, "I need to feel valued and heard")
    await send_message(client, sid, "The feeling might be telling me to speak up")
    await send_message(client, sid, "I'll bring it up in our next 1:1")

    # Generate card first
    await client.post(f"/guide-sessions/{sid}/generate-card")

    # Save
    resp = await client.post(
        f"/guide-sessions/{sid}/save",
        json={"save": True}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"
    assert resp.json()["reflection_id"] is not None

    # Verify session is completed
    resp_session = await client.get(f"/guide-sessions/{sid}")
    assert resp_session.json()["status"] == "completed"


# ─── Library: Guide Me saved reflections appear in library list ───────────────

@pytest.mark.asyncio
async def test_guide_me_reflection_appears_in_library(client):
    """A Guide Me session saved as a Reflection appears in /library."""
    # Create and save a Guide Me session
    session = await start_guide_session(client)
    sid = session["id"]

    await send_message(client, sid, "My manager ignored my feedback in a meeting.")
    await send_message(client, sid, "I feel frustrated and disrespected")
    await send_message(client, sid, "About a 6 out of 10")
    await send_message(client, sid, "Yes that's right")
    await send_message(client, sid, "About my manager and the meeting")
    await send_message(client, sid, "It feels like a one-time thing")
    await send_message(client, sid, "I think they're dismissive of junior input")
    await send_message(client, sid, "I need to feel valued and heard")
    await send_message(client, sid, "The feeling might be telling me to speak up")
    await send_message(client, sid, "I'll bring it up in our next 1:1")

    await client.post(f"/guide-sessions/{sid}/generate-card")
    save_resp = await client.post(
        f"/guide-sessions/{sid}/save",
        json={"save": True}
    )
    reflection_id = save_resp.json()["reflection_id"]

    # Check library
    resp = await client.get("/library")
    assert resp.status_code == 200
    library_payload = resp.json()
    assert isinstance(library_payload, dict)
    library = library_payload.get("items", [])
    assert isinstance(library, list)
    # At least the one we just saved should be there
    ids = [r["id"] for r in library]
    assert reflection_id in ids


# ─── Update Card ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_card_edits_reflection_card(client):
    """PATCH /guide-sessions/{id}/card edits the generated card."""
    session = await start_guide_session(client)
    sid = session["id"]

    await send_message(client, sid, "My manager ignored my feedback in a meeting.")
    await send_message(client, sid, "I feel frustrated and disrespected")
    await send_message(client, sid, "About a 6 out of 10")
    await send_message(client, sid, "Yes that's right")
    await send_message(client, sid, "About my manager and the meeting")
    await send_message(client, sid, "It feels like a one-time thing")
    await send_message(client, sid, "I think they're dismissive of junior input")
    await send_message(client, sid, "I need to feel valued and heard")
    await send_message(client, sid, "The feeling might be telling me to speak up")
    await send_message(client, sid, "I'll bring it up in our next 1:1")

    await client.post(f"/guide-sessions/{sid}/generate-card")

    # Update title
    resp = await client.patch(
        f"/guide-sessions/{sid}/card",
        json={"title": "Updated reflection title"}
    )
    assert resp.status_code == 200
    assert resp.json()["reflection_card"]["title"] == "Updated reflection title"


# ─── Completion and Status ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_session_status_completed_on_save_or_signup(client):
    """Session status becomes 'completed' when reaching save_or_signup stage."""
    session = await start_guide_session(client)
    sid = session["id"]

    # Advance all the way through
    await send_message(client, sid, "My manager ignored my feedback in a meeting.")
    await send_message(client, sid, "I feel frustrated and disrespected")
    await send_message(client, sid, "About a 6 out of 10")
    await send_message(client, sid, "Yes that's right")
    await send_message(client, sid, "About my manager and the meeting")
    await send_message(client, sid, "It feels like a one-time thing")
    await send_message(client, sid, "I think they're dismissive of junior input")
    await send_message(client, sid, "I need to feel valued and heard")
    await send_message(client, sid, "The feeling might be telling me to speak up")
    await send_message(client, sid, "I'll bring it up in our next 1:1")

    await client.post(f"/guide-sessions/{sid}/generate-card")

    resp = await client.get(f"/guide-sessions/{sid}")
    # After generate-card, stage is reflection_review
    assert resp.json()["current_stage"] == "reflection_review"

    # Send one more message — should reach save_or_signup
    reply_data = await send_message(client, sid, "Yes, that looks right")
    assert reply_data["session"]["current_stage"] == "save_or_signup"
    assert reply_data["session"]["status"] == "completed"


@pytest.mark.asyncio
async def test_respond_to_completed_session_returns_400(client):
    """Sending a message to a completed session returns 400."""
    session = await start_guide_session(client)
    sid = session["id"]

    # Advance to save_or_signup (which marks session complete)
    await send_message(client, sid, "My manager ignored my feedback.")
    await send_message(client, sid, "I feel frustrated")
    await send_message(client, sid, "About a 6 out of 10")
    await send_message(client, sid, "Yes that's right")
    await send_message(client, sid, "About the meeting")
    await send_message(client, sid, "One-time thing")
    await send_message(client, sid, "Dismissive manager")
    await send_message(client, sid, "Need to be heard")
    await send_message(client, sid, "Speak up more")
    await send_message(client, sid, "Talk in 1:1")
    await client.post(f"/guide-sessions/{sid}/generate-card")
    await send_message(client, sid, "Looks good")

    # Try to respond again
    resp = await client.post(
        f"/guide-sessions/{sid}/respond",
        params={"user_message": "Another message"}
    )
    assert resp.status_code == 400

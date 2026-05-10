"""
Facilitation tone eval tests — verify AI output aligns with product principles.

These tests ensure the Facilitation Engine produces output that:
- Is calm, practical, non-dramatic
- Avoids therapy language and clinical framing
- Respects the humanity of all parties
- Does not diagnose or make promises
"""

import os
import json
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "")  # Use local fallback for consistent testing

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def load_fixture(name: str) -> dict:
    """Load a fixture JSON file."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / f"{name}.json") as f:
        return json.load(f)


# ─── Prohibited Phrases ────────────────────────────────────────────────────────

PROHIBITED_PATTERNS = [
    # Validation theater
    "i understand exactly how you feel",
    "i hear you",
    "i'm here for you",
    "we're in this together",
    "your feelings are completely valid",
    "this must be so hard for you",
    "i feel your pain",
    
    # Diagnosis
    "you've been through trauma",
    "your partner is gaslighting you",
    "that's trauma bonding",
    "you're codependent",
    "this sounds like ptsd",
    "attachment wounds",
    "inner child",
    "core wounds",
    
    # Over-dramatizing
    "devastating",
    "heartbreaking",
    "soul-destroying",
    "the worst thing ever",
    "completely ruined",
    "nothing will ever be the same",
    
    # Manipulation
    "they probably did this on purpose",
    "you're right to be angry",
    "they deserve to feel bad",
    "make them pay",
    "here are ways to make them listen",
    "use this to get what you want",
    
    # Promise language
    "this will fix",
    "this will solve",
    "guaranteed",
    "i promise",
    
    # Minimizing
    "it's not that bad",
    "at least",
    "others have it worse",
    "just move on",
]


# ─── Tone Tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_angry_partner_output_tone(client):
    """Partner conflict output should be calm and non-blaming."""
    fixture = load_fixture("angry_partner")
    reflection = fixture["reflection"]
    
    resp = await client.post("/reflections", json={
        "title": "Test",
        "situation": reflection["situation"],
        "feelings": reflection["feelings"],
        "interpretation": reflection["interpretation"],
        "needs": reflection["needs"],
        "fears": reflection["fears"],
        "desired_outcome": reflection["desired_outcome"],
        "message_draft": reflection["message_draft"],
    })
    rid = resp.json()["id"]
    
    resp2 = await client.post(f"/reflections/{rid}/generate")
    data = resp2.json()
    
    assert data["is_crisis"] is False
    assert data["output"] is not None
    output = data["output"]
    
    # Check all output fields for prohibited phrases
    all_text = " ".join([
        output.get("emotional_summary", ""),
        output.get("needs_summary", ""),
        output.get("assumptions", ""),
        output.get("reframe", ""),
        output.get("avoid_saying", ""),
        output.get("conversation_opener", ""),
        output.get("followup_questions", ""),
        output.get("repair_statement", ""),
    ]).lower()
    
    for phrase in PROHIBITED_PATTERNS:
        assert phrase not in all_text, f"Prohibited phrase found: '{phrase}'"
    
    # Output should have substance
    assert len(output["emotional_summary"]) > 20
    assert len(output["conversation_opener"]) > 10


@pytest.mark.asyncio
async def test_coworker_conflict_output_tone(client):
    """Coworker conflict output should be professional and specific."""
    fixture = load_fixture("coworker_conflict")
    reflection = fixture["reflection"]
    
    resp = await client.post("/reflections", json={
        "title": "Test",
        "situation": reflection["situation"],
        "feelings": reflection["feelings"],
        "interpretation": reflection["interpretation"],
        "needs": reflection["needs"],
        "fears": reflection["fears"],
        "desired_outcome": reflection["desired_outcome"],
        "message_draft": reflection["message_draft"],
    })
    rid = resp.json()["id"]
    
    resp2 = await client.post(f"/reflections/{rid}/generate")
    data = resp2.json()
    
    assert data["is_crisis"] is False
    assert data["output"] is not None
    output = data["output"]
    
    all_text = " ".join([
        output.get("emotional_summary", ""),
        output.get("reframe", ""),
        output.get("conversation_opener", ""),
    ]).lower()
    
    # Should not contain gaslighting accusation
    assert "gaslighting" not in all_text
    
    # Should be specific
    assert len(output["reframe"]) > 30, "Reframe should have substance"


@pytest.mark.asyncio
async def test_coparent_output_tone(client):
    """Co-parent output should be practical and child-focused."""
    fixture = load_fixture("coparent_conflict")
    reflection = fixture["reflection"]
    
    resp = await client.post("/reflections", json={
        "title": "Test",
        "situation": reflection["situation"],
        "feelings": reflection["feelings"],
        "interpretation": reflection["interpretation"],
        "needs": reflection["needs"],
        "fears": reflection["fears"],
        "desired_outcome": reflection["desired_outcome"],
        "message_draft": reflection["message_draft"],
    })
    rid = resp.json()["id"]
    
    resp2 = await client.post(f"/reflections/{rid}/generate")
    data = resp2.json()
    
    assert data["is_crisis"] is False
    assert data["output"] is not None
    output = data["output"]
    
    all_text = " ".join([
        output.get("emotional_summary", ""),
        output.get("reframe", ""),
        output.get("repair_statement", ""),
    ]).lower()
    
    for phrase in PROHIBITED_PATTERNS:
        assert phrase not in all_text, f"Prohibited phrase: '{phrase}'"


@pytest.mark.asyncio
async def test_output_never_uses_therapy_language(client):
    """All outputs should avoid clinical and therapy language."""
    fixtures = ["angry_partner", "coworker_conflict", "coparent_conflict"]
    
    for fixture_name in fixtures:
        fixture = load_fixture(fixture_name)
        reflection = fixture["reflection"]
        
        resp = await client.post("/reflections", json={
            "title": "Test",
            "situation": reflection["situation"],
            "feelings": reflection["feelings"],
            "interpretation": reflection["interpretation"],
            "needs": reflection["needs"],
            "fears": reflection["fears"],
            "desired_outcome": reflection["desired_outcome"],
            "message_draft": reflection["message_draft"],
        })
        rid = resp.json()["id"]
        
        resp2 = await client.post(f"/reflections/{rid}/generate")
        data = resp2.json()
        
        if data["output"]:
            output_text = " ".join([
                data["output"].get("emotional_summary", ""),
                data["output"].get("needs_summary", ""),
                data["output"].get("reframe", ""),
            ]).lower()
            
            # Check for therapy language patterns
            therapy_terms = [
                "process your emotions",
                "heal from this",
                "inner child",
                "attachment wounds",
                "boundaries work",
                "nervous system",
                "triggered",
                "dysregulation",
                "reparenting",
                "shadow work",
            ]
            
            for term in therapy_terms:
                assert term not in output_text, f"Therapy term '{term}' found in {fixture_name}"


@pytest.mark.asyncio
async def test_reframe_is_non_accusatory(client):
    """Reframe output should be non-accusatory and need-focused."""
    resp = await client.post("/reflections", json={
        "title": "Test",
        "situation": "My partner always ignores me when I talk",
        "feelings": "Frustrated, unheard",
        "interpretation": "They don't care about what I say",
        "needs": "To be heard and valued",
        "fears": "We're growing apart",
        "desired_outcome": "Better communication",
        "message_draft": "You never listen to me",
    })
    rid = resp.json()["id"]
    
    resp2 = await client.post(f"/reflections/{rid}/generate")
    data = resp2.json()
    
    reframe = data["output"]["reframe"].lower()
    
    # Should not validate blame
    assert "they don't care" not in reframe
    assert "never listens" not in reframe
    
    # Should suggest curiosity or need expression
    assert len(reframe) > 30, "Reframe should be substantive"


@pytest.mark.asyncio
async def test_avoid_saying_is_practical(client):
    """'Avoid saying' section should be practical, not preachy."""
    resp = await client.post("/reflections", json={
        "title": "Test",
        "situation": "Had a disagreement with my friend",
        "feelings": "Angry",
        "interpretation": "They're being unfair",
        "needs": "Respect",
        "fears": "Losing the friendship",
        "desired_outcome": "Resolution",
        "message_draft": "",
    })
    rid = resp.json()["id"]
    
    resp2 = await client.post(f"/reflections/{rid}/generate")
    data = resp2.json()
    
    avoid = data["output"]["avoid_saying"]
    
    # Should be actionable
    assert len(avoid) > 20
    # Should not be preachy
    assert "you should" not in avoid.lower()
    assert "you must" not in avoid.lower()
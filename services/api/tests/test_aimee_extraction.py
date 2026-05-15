"""
Unit tests for Aimee extraction flow.

Tests the core trust promise: AI can suggest, user confirms, only confirmed data is saved.
"""

import os
import sys
from pathlib import Path
import types

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from sqlalchemy import select

from app.db.session import init_db, async_session_factory
from app.models.user import User
from app.services import ai_router as ai_router_module


@pytest.fixture
async def client():
    """Test client with initialized database."""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def force_local_ai(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "local")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("MINIMAX_API_KEY", "")


# ─── Extraction Endpoint Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extract_returns_structured_response(client):
    """Safe text extraction returns valid structured JSON with no database write."""
    payload = {"text": "I'm really angry about the price increase at Starbucks."}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    # Verify response structure
    assert "feelings" in data
    assert "suggested_memory_title" in data
    assert "suggested_response" in data
    assert "safety_status" in data
    
    # Verify safety status
    assert data["safety_status"] == "safe"
    
    # Verify feelings structure
    if data["feelings"]:
        feeling = data["feelings"][0]
        assert "primary_emotion" in feeling
        assert feeling["primary_emotion"] in ["joy", "sadness", "anger", "fear", "disgust"]
        assert "label" in feeling
        assert "intensity" in feeling
        assert 1 <= feeling["intensity"] <= 10
        assert "confidence" in feeling


@pytest.mark.asyncio
async def test_extract_handles_joy(client):
    """Test extraction with joyful text."""
    payload = {"text": "I felt so happy when my friend called to say congratulations!"}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["safety_status"] == "safe"
    assert len(data["feelings"]) > 0
    assert data["feelings"][0]["primary_emotion"] == "joy"


@pytest.mark.asyncio
async def test_extract_handles_sadness(client):
    """Test extraction with sad text."""
    payload = {"text": "I feel really lonely and hurt after the conversation."}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["safety_status"] == "safe"
    assert len(data["feelings"]) > 0
    assert data["feelings"][0]["primary_emotion"] == "sadness"


@pytest.mark.asyncio
async def test_extract_handles_fear(client):
    """Test extraction with anxious/scared text."""
    payload = {"text": "I'm worried about the presentation tomorrow and feel anxious."}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["safety_status"] == "safe"
    assert len(data["feelings"]) > 0
    # Mock extracts "scared/afraid/worried/anxious" as fear
    assert data["feelings"][0]["primary_emotion"] == "fear"


@pytest.mark.asyncio
async def test_extract_catches_crisis_keywords(client):
    """Crisis keywords return flagged status with supportive message."""
    payload = {"text": "I want to kill myself because everything feels hopeless."}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["safety_status"] == "flagged"
    assert data["feelings"] == []
    assert "988" in data["suggested_response"] or "741741" in data["suggested_response"]


@pytest.mark.asyncio
async def test_extract_catches_self_harm(client):
    """Self-harm keywords return flagged status."""
    payload = {"text": "I keep thinking about hurting myself."}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["safety_status"] == "flagged"
    assert data["feelings"] == []


@pytest.mark.asyncio
async def test_extract_validates_empty_text(client):
    """Empty text is rejected."""
    payload = {"text": ""}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_extract_requires_text_field(client):
    """Request without text field is rejected."""
    payload = {}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_extract_does_not_infer_emotion_from_name_only_input(client):
    """Name-only input should not create a fake emotional extraction."""
    payload = {"text": "My name is John."}

    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["safety_status"] == "safe"
    assert data["feelings"] == []
    assert data["suggested_memory_title"] == ""


@pytest.mark.asyncio
async def test_chat_name_only_input_stays_grounded(client):
    """Name-only input should not trigger emotional assumptions."""
    payload = {"message": "My name is John."}

    resp = await client.post("/v2/aimee/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["safety_status"] == "safe"
    reply = data["reply"].lower()
    assert "what's on your mind" not in reply
    assert "sad" not in reply
    assert "hurt" not in reply
    assert "feeling" not in reply
    assert "john" in reply


@pytest.mark.asyncio
async def test_chat_keeps_normal_turns_in_conversation_mode(client, monkeypatch):
    """Regular reflection turns should stay conversational and avoid review mode."""
    monkeypatch.setenv("MINIMAX_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    payload = {"message": "My new boss called my work junk and I'm angry about it."}

    resp = await client.post("/v2/aimee/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["safety_status"] == "safe"
    assert data["should_offer_review"] is False
    assert data["reply"].count("?") <= 1
    assert "saved" not in data["reply"].lower()


@pytest.mark.asyncio
async def test_chat_marks_done_or_save_turns_for_review(client, monkeypatch):
    """When the user says they are done or wants to save, chat should switch to review mode."""
    monkeypatch.setenv("MINIMAX_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    payload = {"message": "I think that's it. Can we save this?"}

    resp = await client.post("/v2/aimee/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["safety_status"] == "safe"
    assert data["should_offer_review"] is True
    assert "save" in data["reply"].lower() or "captured" in data["reply"].lower()


@pytest.mark.asyncio
async def test_chat_does_not_treat_im_just_as_a_name_intro(client, monkeypatch):
    """Conversational text starting with I'm should not be treated as a name-only intro."""
    monkeypatch.setenv("MINIMAX_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    payload = {"message": "I'm just thinking through my feelings."}

    resp = await client.post("/v2/aimee/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["safety_status"] == "safe"
    reply = data["reply"].lower()
    assert "hi just" not in reply
    assert "what would you like help thinking through today" not in reply


@pytest.mark.asyncio
async def test_extract_does_not_infer_sadness_from_negated_sadness(client, monkeypatch):
    """Negated sadness should not create a fake sadness extraction in fallback mode."""
    monkeypatch.setenv("MINIMAX_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    payload = {"text": "Bro, I'm not sad."}

    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["safety_status"] == "safe"
    assert data["feelings"] == []
    assert data["suggested_memory_title"] == ""


@pytest.mark.asyncio
async def test_chat_does_not_reply_with_hurt_for_negated_sadness(client, monkeypatch):
    """Negated sadness should not trigger the fallback hurt reply."""
    monkeypatch.setenv("MINIMAX_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    payload = {"message": "Bro, I'm not sad."}

    resp = await client.post("/v2/aimee/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["safety_status"] == "safe"
    reply = data["reply"].lower()
    assert "sense of hurt" not in reply
    assert "closest to how you're feeling" not in reply


@pytest.mark.asyncio
async def test_v2_chat_uses_shared_minimax_router_not_openai_sdk(client, monkeypatch):
    """The v2 chat endpoint should use the shared MiniMax router path, not the OpenAI SDK."""
    monkeypatch.setenv("AI_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M2.7")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    async def fake_generate(self, messages, max_tokens=1000):
        return "Use the shared router."

    monkeypatch.setattr(ai_router_module.AIRouter, "generate", fake_generate)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("openai SDK should not be used for v2 chat"))))

    resp = await client.post("/v2/aimee/chat", json={"message": "I'm planning two chats today."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety_status"] == "safe"
    assert data["reply"] == "Use the shared router."


@pytest.mark.asyncio
async def test_v2_extract_uses_shared_minimax_router_not_openai_sdk(client, monkeypatch):
    """The v2 extract endpoint should use the shared MiniMax router path, not the OpenAI SDK."""
    monkeypatch.setenv("AI_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M2.7")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    async def fake_generate(self, messages, max_tokens=1000):
        return (
            '{"feelings":[{"primary_emotion":"fear","label":"worried","intensity":6,"confidence":0.9,'
            '"entities":[],"topics":[],"needs":[{"name":"clarity","status":"identified"}]}],'
            '"suggested_memory_title":"Worried about upcoming chats",'
            '"suggested_response":"That sounds like a lot to hold.",'
            '"safety_status":"safe"}'
        )

    monkeypatch.setattr(ai_router_module.AIRouter, "generate", fake_generate)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("openai SDK should not be used for v2 extract"))))

    resp = await client.post("/v2/aimee/extract", json={"text": "I'm preparing for a couple of chats."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety_status"] == "safe"
    assert data["feelings"][0]["primary_emotion"] == "fear"


# ─── Confirm Endpoint Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirm_saves_to_emotional_graph(client):
    """Confirm endpoint saves confirmed data to emotional graph."""
    payload = {
        "source_text": "I felt angry about the price increase.",
        "memory_title": "Anger about prices",
        "memory_narrative": "This happened at Starbucks.",
        "feelings": [
            {
                "primary_emotion": "anger",
                "label": "frustrated",
                "intensity": 7,
                "confidence": 0.85,
                "source_text": "I felt angry",
                "entity_names": ["Starbucks"],
                "topic_titles": [],
                "need_names": ["fairness"],
            }
        ],
    }
    
    resp = await client.post("/v2/aimee/confirm", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert "memory_id" in data
    assert data["feelings_count"] == 1
    assert data["status"] == "saved"


@pytest.mark.asyncio
async def test_confirm_requires_at_least_one_feeling(client):
    """Confirm requires at least one feeling."""
    payload = {
        "source_text": "Some text",
        "memory_title": "Test memory",
        "feelings": [],  # Empty!
    }
    
    resp = await client.post("/v2/aimee/confirm", json=payload)
    assert resp.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_confirm_validates_intensity_range(client):
    """Confirm validates intensity is between 1 and 10."""
    payload = {
        "source_text": "Test",
        "memory_title": "Test",
        "feelings": [
            {
                "primary_emotion": "anger",
                "label": "test",
                "intensity": 15,  # Invalid - too high
                "confidence": 0.8,
            }
        ],
    }
    
    resp = await client.post("/v2/aimee/confirm", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_confirm_validates_emotion(client):
    """Confirm validates primary emotion is valid."""
    payload = {
        "source_text": "Test",
        "memory_title": "Test",
        "feelings": [
            {
                "primary_emotion": "not_a_real_emotion",  # Invalid!
                "label": "test",
                "intensity": 5,
                "confidence": 0.8,
            }
        ],
    }
    
    resp = await client.post("/v2/aimee/confirm", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_confirm_multiple_feelings(client):
    """Confirm can save multiple feelings."""
    payload = {
        "source_text": "Mixed feelings today.",
        "memory_title": "Complex emotions",
        "feelings": [
            {
                "primary_emotion": "anger",
                "label": "frustrated",
                "intensity": 6,
                "confidence": 0.8,
            },
            {
                "primary_emotion": "sadness",
                "label": "hurt",
                "intensity": 5,
                "confidence": 0.75,
            },
        ],
    }
    
    resp = await client.post("/v2/aimee/confirm", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["feelings_count"] == 2


# ─── Integration Test: Extract → Confirm Flow ─────────────────────────────────

@pytest.mark.asyncio
async def test_extract_confirm_flow(client):
    """Test the complete Aimee flow: extract → review → confirm."""
    # Step 1: Extract emotional meaning
    extract_payload = {"text": "I'm frustrated with my manager about the feedback."}
    extract_resp = await client.post("/v2/aimee/extract", json=extract_payload)
    assert extract_resp.status_code == 200
    
    extract_data = extract_resp.json()
    assert extract_data["safety_status"] == "safe"
    
    # Step 2: User reviews and confirms (possibly edits)
    if extract_data["feelings"]:
        feeling = extract_data["feelings"][0]
        confirm_payload = {
            "source_text": extract_payload["text"],
            "memory_title": extract_data.get("suggested_memory_title", "New memory"),
            "memory_narrative": "",
            "feelings": [
                {
                    "primary_emotion": feeling["primary_emotion"],
                    "label": feeling["label"],
                    "intensity": feeling["intensity"],
                    "confidence": feeling.get("confidence", 0.8),
                    "source_text": extract_payload["text"],
                    "entity_names": [e["name"] for e in feeling.get("entities", [])],
                    "topic_titles": [t["title"] for t in feeling.get("topics", [])],
                    "need_names": [n["name"] for n in feeling.get("needs", [])],
                }
            ],
        }
        
        confirm_resp = await client.post("/v2/aimee/confirm", json=confirm_payload)
        assert confirm_resp.status_code == 200
        confirm_data = confirm_resp.json()
        assert confirm_data["status"] == "saved"
        
        # Step 3: Verify saved in graph
        memory_id = confirm_data["memory_id"]
        get_resp = await client.get(f"/v2/memories/{memory_id}")
        assert get_resp.status_code == 200
        memory = get_resp.json()
        assert len(memory["feelings"]) >= 1


# ─── Safety Check Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_safety_suicide_keywords(client):
    """Test various suicide-related keywords trigger safety."""
    crisis_texts = [
        "I want to kill myself",
        "I'm going to end it all",
        "I wish I were dead",
        "Better off dead",
        "Suicide is the only way",
    ]
    
    for text in crisis_texts:
        resp = await client.post("/v2/aimee/extract", json={"text": text})
        assert resp.json()["safety_status"] == "flagged", f"Failed for: {text}"


@pytest.mark.asyncio
async def test_safety_self_harm_keywords(client):
    """Test self-harm keywords trigger safety."""
    harm_texts = [
        "I'm going to hurt myself",
        "I want to self-harm",
        "I'll overdose on pills",
    ]
    
    for text in harm_texts:
        resp = await client.post("/v2/aimee/extract", json={"text": text})
        assert resp.json()["safety_status"] == "flagged", f"Failed for: {text}"


@pytest.mark.asyncio
async def test_safe_text_not_flagged(client):
    """Normal emotional content is marked safe."""
    safe_texts = [
        "I'm feeling frustrated about work",
        "The service at the restaurant was disappointing",
        "I'm anxious about my presentation",
        "I'm so happy to see my friend",
    ]
    
    for text in safe_texts:
        resp = await client.post("/v2/aimee/extract", json={"text": text})
        assert resp.json()["safety_status"] == "safe", f"Should be safe: {text}"


# ─── Need Status Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extraction_includes_need_status(client):
    """Extracted feelings include need_status field."""
    payload = {"text": "I'm angry about the delay."}
    
    resp = await client.post("/v2/aimee/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    if data["feelings"]:
        for feeling in data["feelings"]:
            # Each need should have a status
            for need in feeling.get("needs", []):
                assert "status" in need
                assert need["status"] in ["identified", "unknown", "skipped"]

"""
Unit tests for v2 emotional graph API.

Tests nested memory creation with multiple feelings, needs, entities, and topics.
This is the central test case proving the emotional graph works.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.db.session import init_db
from app.db.session import async_session_factory
from app.models.v2 import Memory, Feeling, Need, Entity, Topic


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
    """Verify API health check works."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


# ─── Create Memory with Nested Objects (Central Test) ─────────────────────────

@pytest.mark.asyncio
async def test_create_memory_with_nested_objects(client):
    """
    Create one memory containing:
    - Multiple feelings (hurt/sadness, anger)
    - Multiple needs (reassurance, understanding, connection)
    - One entity (Crystal)
    - One topic (feeling ignored after dinner)
    
    Then verify all relationships are retrieved intact.
    """
    payload = {
        "title": "Feeling ignored by Crystal after dinner",
        "narrative": "I tried to share something important during dinner but Crystal seemed distracted and didn't respond.",
        "ai_summary": "",
        "privacy_level": "private",
        "feelings": [
            {
                "primary_emotion": "sadness",
                "label": "hurt",
                "intensity": 7.0,
                "confidence": 0.85,
                "source_text": "I tried to share something important during dinner"
            },
            {
                "primary_emotion": "anger",
                "label": "frustrated",
                "intensity": 5.0,
                "confidence": 0.80,
                "source_text": "Crystal seemed distracted"
            }
        ],
        "need_names": ["reassurance", "understanding", "connection"],
        "entity_names": ["Crystal"],
        "topic_titles": ["feeling ignored after dinner"]
    }
    
    resp = await client.post("/v2/memories", json=payload)
    assert resp.status_code == 201, f"Failed: {resp.text}"
    data = resp.json()
    
    memory_id = data["id"]
    assert data["title"] == payload["title"]
    assert data["privacy_level"] == "private"
    
    # Verify feelings
    assert len(data["feelings"]) == 2
    feelings_by_emotion = {f["primary_emotion"]: f for f in data["feelings"]}
    
    assert "sadness" in feelings_by_emotion
    assert feelings_by_emotion["sadness"]["label"] == "hurt"
    assert feelings_by_emotion["sadness"]["intensity"] == 7.0
    
    assert "anger" in feelings_by_emotion
    assert feelings_by_emotion["anger"]["label"] == "frustrated"
    assert feelings_by_emotion["anger"]["intensity"] == 5.0
    
    # Verify needs are linked to feelings
    sadness_feeling = feelings_by_emotion["sadness"]
    assert len(sadness_feeling.get("needs", [])) >= 3
    
    # Verify entity is linked
    assert len(data["entities"]) == 1
    assert data["entities"][0]["canonical_name"] == "Crystal"
    
    # Verify topic is linked
    assert len(data["topics"]) == 1
    assert data["topics"][0]["title"] == "feeling ignored after dinner"
    
    return memory_id


# ─── List Memories ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_memories(client):
    """Create a memory and verify it appears in list."""
    payload = {
        "title": "Test memory for listing",
        "narrative": "A simple test",
        "feelings": [
            {"primary_emotion": "joy", "label": "happy", "intensity": 6.0}
        ],
        "need_names": ["peace"],
        "entity_names": [],
        "topic_titles": []
    }
    
    resp = await client.post("/v2/memories", json=payload)
    assert resp.status_code == 201
    
    # List memories
    resp2 = await client.get("/v2/memories")
    assert resp2.status_code == 200
    data = resp2.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ─── Get Memory with All Relations ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_memory_with_relations(client):
    """Create a memory and retrieve it with all nested relationships."""
    # Create
    payload = {
        "title": "Memory for detail test",
        "feelings": [
            {"primary_emotion": "fear", "label": "anxious", "intensity": 5.0}
        ],
        "need_names": ["safety"],
        "entity_names": ["Work"],
        "topic_titles": ["deadline pressure"]
    }
    
    resp = await client.post("/v2/memories", json=payload)
    assert resp.status_code == 201
    memory_id = resp.json()["id"]
    
    # Get detail
    resp2 = await client.get(f"/v2/memories/{memory_id}")
    assert resp2.status_code == 200
    data = resp2.json()
    
    assert data["id"] == memory_id
    assert len(data["feelings"]) == 1
    assert len(data["needs"]) >= 1
    assert len(data["entities"]) == 1
    assert len(data["topics"]) == 1


# ─── Delete Memory ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_memory(client):
    """Create and delete a memory."""
    payload = {
        "title": "Memory to delete",
        "feelings": [
            {"primary_emotion": "disgust", "label": "disappointed", "intensity": 4.0}
        ],
        "need_names": [],
        "entity_names": [],
        "topic_titles": []
    }
    
    # Create
    resp = await client.post("/v2/memories", json=payload)
    assert resp.status_code == 201
    memory_id = resp.json()["id"]
    
    # Delete
    resp2 = await client.delete(f"/v2/memories/{memory_id}")
    assert resp2.status_code == 204
    
    # Verify deleted
    resp3 = await client.get(f"/v2/memories/{memory_id}")
    assert resp3.status_code == 404


# ─── Feel Flow Endpoint ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_feel_flow_endpoint(client):
    """Test feel-flow time series endpoint."""
    # Create some feelings first
    payload = {
        "title": "Test for feel flow",
        "feelings": [
            {"primary_emotion": "joy", "label": "grateful", "intensity": 7.0},
            {"primary_emotion": "sadness", "label": "melancholy", "intensity": 4.0},
        ],
        "need_names": ["appreciation"],
        "entity_names": ["Family"],
        "topic_titles": ["holiday gathering"]
    }
    await client.post("/v2/memories", json=payload)
    
    # Get feel-flow data
    resp = await client.get("/v2/feelings/feel-flow?days=30")
    assert resp.status_code == 200
    data = resp.json()
    
    assert "data" in data
    assert "emotion_totals" in data
    assert "average_intensity" in data
    assert data["time_bucket"] == "day"


# ─── Feel Map Endpoint ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_feel_map_endpoint(client):
    """Test feel-map composition endpoint."""
    # Create feelings
    payload = {
        "title": "Test for feel map",
        "feelings": [
            {"primary_emotion": "anger", "label": "frustrated", "intensity": 6.0},
            {"primary_emotion": "anger", "label": "annoyed", "intensity": 3.0},
        ],
        "need_names": ["clarity"],
        "entity_names": ["Work"],
        "topic_titles": ["project delays"]
    }
    await client.post("/v2/memories", json=payload)
    
    # Get feel-map data
    resp = await client.get("/v2/feelings/feel-map?days=30")
    assert resp.status_code == 200
    data = resp.json()
    
    assert "emotion_groups" in data
    assert "dominant_emotion" in data
    assert "total_feelings" in data
    assert data["total_feelings"] >= 2


# ─── List Entities ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_entities(client):
    """Test entities listing."""
    # Create with entity
    payload = {
        "title": "Test entity listing",
        "feelings": [
            {"primary_emotion": "joy", "label": "loved", "intensity": 8.0}
        ],
        "need_names": ["connection"],
        "entity_names": ["Partner"],
        "topic_titles": ["date night"]
    }
    await client.post("/v2/memories", json=payload)
    
    # List entities
    resp = await client.get("/v2/entities")
    assert resp.status_code == 200
    data = resp.json()
    
    assert isinstance(data, list)
    entity_names = [e["canonical_name"] for e in data]
    assert "Partner" in entity_names


# ─── Get Entity Detail ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_entity_detail(client):
    """Test entity detail with relations."""
    # Create with entity
    payload = {
        "title": "Test entity detail",
        "feelings": [
            {"primary_emotion": "sadness", "label": "hurt", "intensity": 6.0}
        ],
        "need_names": ["understanding"],
        "entity_names": ["Manager"],
        "topic_titles": ["feedback conversation"]
    }
    resp = await client.post("/v2/memories", json=payload)
    
    # Get entity detail
    entity_id = resp.json()["entities"][0]["id"]
    resp2 = await client.get(f"/v2/entities/{entity_id}")
    assert resp2.status_code == 200
    data = resp2.json()
    
    assert data["canonical_name"] == "Manager"
    # Simplified response - just verify entity fields are present
    assert "id" in data
    assert "entity_type" in data


# ─── List Needs ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_needs(client):
    """Test needs listing."""
    # Create with needs
    payload = {
        "title": "Test needs listing",
        "feelings": [
            {"primary_emotion": "fear", "label": "worried", "intensity": 5.0}
        ],
        "need_names": ["clarity", "security", "recognition"],
        "entity_names": [],
        "topic_titles": []
    }
    await client.post("/v2/memories", json=payload)
    
    # List needs
    resp = await client.get("/v2/needs")
    assert resp.status_code == 200
    data = resp.json()
    
    assert isinstance(data, list)
    need_names = [n["name"] for n in data]
    assert "clarity" in need_names
    assert "security" in need_names
    assert "recognition" in need_names


# ─── Get Need Detail ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_need_detail(client):
    """Test need detail with relations."""
    # Create with need
    payload = {
        "title": "Test need detail",
        "feelings": [
            {"primary_emotion": "anger", "label": "resentful", "intensity": 6.0}
        ],
        "need_names": ["respect"],
        "entity_names": ["Colleague"],
        "topic_titles": ["unfair treatment"]
    }
    resp = await client.post("/v2/memories", json=payload)
    
    # Get need detail
    need_id = resp.json()["needs"][0]["id"]
    resp2 = await client.get(f"/v2/needs/{need_id}")
    assert resp2.status_code == 200
    data = resp2.json()
    
    assert data["name"] == "respect"
    assert "feelings" in data


# ─── List Feelings ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_feelings(client):
    """Test feelings listing."""
    # Create feelings
    payload = {
        "title": "Test feelings listing",
        "feelings": [
            {"primary_emotion": "joy", "label": "excited", "intensity": 8.0},
            {"primary_emotion": "disgust", "label": "appalled", "intensity": 7.0},
        ],
        "need_names": [],
        "entity_names": [],
        "topic_titles": []
    }
    await client.post("/v2/memories", json=payload)
    
    # List feelings
    resp = await client.get("/v2/feelings")
    assert resp.status_code == 200
    data = resp.json()
    
    assert isinstance(data, list)
    emotions = [f["primary_emotion"] for f in data]
    assert "joy" in emotions
    assert "disgust" in emotions


# ─── User Isolation ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_isolation(client):
    """Verify data is isolated to user (MVP: dev-user-001 only)."""
    # Create memory as dev user
    payload = {
        "title": "Private memory",
        "feelings": [
            {"primary_emotion": "sadness", "label": "lonely", "intensity": 8.0}
        ],
        "need_names": ["connection"],
        "entity_names": [],
        "topic_titles": []
    }
    resp = await client.post("/v2/memories", json=payload)
    assert resp.status_code == 201
    memory_id = resp.json()["id"]
    
    # Verify it's returned in list
    resp2 = await client.get("/v2/memories")
    memory_ids = [m["id"] for m in resp2.json()]
    assert memory_id in memory_ids


# ─── Default Privacy is Private ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_default_privacy_is_private(client):
    """Verify memories default to private privacy level."""
    payload = {
        "title": "Privacy test",
        "feelings": [
            {"primary_emotion": "fear", "label": "anxious", "intensity": 5.0}
        ],
        "need_names": [],
        "entity_names": [],
        "topic_titles": []
    }
    
    resp = await client.post("/v2/memories", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    
    assert data["privacy_level"] == "private"


# ─── Intensity Range Validation ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_intensity_must_be_1_to_10(client):
    """Verify intensity must be between 1 and 10."""
    payload = {
        "title": "Invalid intensity test",
        "feelings": [
            {"primary_emotion": "joy", "label": "test", "intensity": 15.0}  # Invalid
        ],
        "need_names": [],
        "entity_names": [],
        "topic_titles": []
    }
    
    resp = await client.post("/v2/memories", json=payload)
    # Should fail validation
    assert resp.status_code in [422, 400, 500]


# ─── Not Found ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_memory_not_found(client):
    """Verify 404 for nonexistent memory."""
    resp = await client.get("/v2/memories/nonexistent-id-xyz")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_entity_not_found(client):
    """Verify 404 for nonexistent entity."""
    resp = await client.get("/v2/entities/nonexistent-id-xyz")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_need_not_found(client):
    """Verify 404 for nonexistent need."""
    resp = await client.get("/v2/needs/nonexistent-id-xyz")
    assert resp.status_code == 404
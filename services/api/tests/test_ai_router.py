"""Unit tests for AI router provider behavior."""

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.services.ai_router import AIRouter
from app.services import ai_router as ai_router_module


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeAsyncClient:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None):
        return _FakeResponse(self.payload)


@pytest.mark.asyncio
async def test_minimax_generation_strips_reasoning_tags_and_uses_current_endpoint(monkeypatch):
    captured = {}

    def fake_client_factory(*args, **kwargs):
        payload = {
            "choices": [{"message": {"content": "<think>internal</think>{\"ok\":true}"}}],
            "base_resp": {"status_code": 0, "status_msg": "ok"},
        }
        client = _FakeAsyncClient(payload)

        async def post(url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return _FakeResponse(payload)

        client.post = post
        return client

    monkeypatch.setattr(ai_router_module, "AI_PROVIDER", "minimax")
    monkeypatch.setattr(ai_router_module, "MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setattr(ai_router_module, "MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    monkeypatch.setattr(ai_router_module, "MINIMAX_MODEL", "MiniMax-M2.7")
    monkeypatch.setenv("AI_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M2.7")
    monkeypatch.setattr(ai_router_module.httpx, "AsyncClient", fake_client_factory)

    router = AIRouter(api_key="", model="MiniMax-M2.7")
    content = await router.generate([{"role": "user", "content": "hello"}], max_tokens=123)

    assert content == '{"ok":true}'
    assert captured["url"] == "https://api.minimax.io/v1/text/chatcompletion_v2"
    assert captured["headers"]["Authorization"] == "Bearer test-minimax-key"
    assert captured["json"]["model"] == "MiniMax-M2.7"
    assert captured["json"]["max_completion_tokens"] == 123

"""
AI Router — Abstraction layer for AI provider calls.

Keeps AI provider calls behind an abstraction layer so we can:
- Swap providers (OpenAI, Anthropic, Gemini) without changing call sites
- Add fallbacks when API keys aren't configured
- Test without hitting real APIs

TODO (MVP 2): Add support for additional providers.
"""

import os
import re
from typing import Optional

import httpx


# ─── Config ────────────────────────────────────────────────────────────────────

AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# MiniMax config (OpenAI-compatible endpoint)
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7")


def get_provider_name() -> str:
    """Return the currently configured provider name."""
    return os.environ.get("AI_PROVIDER", AI_PROVIDER)


def get_model_name(provider: Optional[str] = None) -> str:
    """Return the configured model for the selected provider."""
    current_provider = provider or get_provider_name()
    if current_provider == "minimax":
        return os.environ.get("MINIMAX_MODEL", MINIMAX_MODEL)
    return os.environ.get("OPENAI_MODEL", OPENAI_MODEL)


def get_provider_api_key(provider: Optional[str] = None) -> str:
    """Return the configured API key for the selected provider."""
    current_provider = provider or get_provider_name()
    if current_provider == "minimax":
        return os.environ.get("MINIMAX_API_KEY", MINIMAX_API_KEY)
    if current_provider == "openai":
        return os.environ.get("OPENAI_API_KEY", OPENAI_API_KEY)
    return ""


def provider_has_key(provider: Optional[str] = None) -> bool:
    """Whether the selected provider has a configured API key."""
    return bool(get_provider_api_key(provider))


def _strip_minimax_reasoning(content: str) -> str:
    """Remove MiniMax reasoning tags from user-visible output."""
    return re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.IGNORECASE).strip()


# ─── AI Router ─────────────────────────────────────────────────────────────────

class AIRouter:
    """
    Abstraction layer for AI generation.
    
    Usage:
        router = AIRouter(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)
        result = await router.generate(prompt)
    """
    
    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = OPENAI_MODEL):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, messages: list[dict], max_tokens: int = 1000) -> str:
        """
        Generate content using the configured provider.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text content
        """
        provider = get_provider_name()
        if provider == "minimax" and provider_has_key(provider):
            return await self._generate_minimax(messages, max_tokens)
        elif provider == "openai" and (self.api_key or provider_has_key(provider)):
            return await self._generate_openai(messages, max_tokens)
        else:
            raise ValueError(f"No valid AI provider configured (provider: {provider})")
    
    async def _generate_minimax(self, messages: list[dict], max_tokens: int) -> str:
        """Call MiniMax API (OpenAI-compatible endpoint)."""
        base_url = os.environ.get("MINIMAX_BASE_URL", MINIMAX_BASE_URL)
        api_key = get_provider_api_key("minimax")
        model = os.environ.get("MINIMAX_MODEL", MINIMAX_MODEL)
        url = f"{base_url}/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
            "temperature": 0.7,
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
            base_resp = data.get("base_resp")
            if base_resp and base_resp.get("status_code") not in (0, None):
                raise ConnectionError(
                    f"{base_resp.get('status_code')} - {base_resp.get('status_msg')}"
                )
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                return _strip_minimax_reasoning(msg.get("content", ""))
            return ""
        except Exception as e:
            raise ConnectionError(f"MiniMax API call failed: {e}")
    
    async def _generate_openai(self, messages: list[dict], max_tokens: int) -> str:
        """Call OpenAI-compatible API."""
        url = "https://api.openai.com/v1/chat/completions"
        api_key = self.api_key or get_provider_api_key("openai")
        model = self.model or get_model_name("openai")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                return msg.get("content", "")
            return ""
        except Exception as e:
            raise ConnectionError(f"OpenAI API call failed: {e}")


# ─── Singleton Instance ─────────────────────────────────────────────────────────

_default_router: Optional[AIRouter] = None


def get_ai_router() -> AIRouter:
    """Get the default AI router instance."""
    global _default_router
    if _default_router is None:
        _default_router = AIRouter()
    return _default_router

"""
AI Router — Abstraction layer for AI provider calls.

Keeps AI provider calls behind an abstraction layer so we can:
- Swap providers (OpenAI, Anthropic, Gemini) without changing call sites
- Add fallbacks when API keys aren't configured
- Test without hitting real APIs

TODO (MVP 2): Add support for additional providers.
"""

import os
from typing import Optional

import httpx


# ─── Config ────────────────────────────────────────────────────────────────────

AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


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
        if AI_PROVIDER == "openai" and self.api_key:
            return await self._generate_openai(messages, max_tokens)
        else:
            raise ValueError("No valid AI provider configured")
    
    async def _generate_openai(self, messages: list[dict], max_tokens: int) -> str:
        """Call OpenAI-compatible API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
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
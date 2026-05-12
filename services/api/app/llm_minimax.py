"""MiniMax LLM client for Aimee conversation.

Uses OpenAI Python SDK with MiniMax's OpenAI-compatible endpoint.
Backend-only - API key never exposed to frontend.
"""

import os
from typing import Any, Optional
import openai


# ─── Configuration ────────────────────────────────────────────────────────────────

def _get_config() -> tuple[str, str, str]:
    """Get MiniMax configuration from environment.
    
    Returns:
        tuple: (api_key, base_url, model)
        
    Raises:
        ValueError: If MINIMAX_API_KEY is not set
    """
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    
    if not api_key:
        raise ValueError(
            "MINIMAX_API_KEY environment variable is not set. "
            "Please add your MiniMax API key to the .env file."
        )
    
    base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    model = os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7")
    
    return api_key, base_url, model


# ─── System Prompt ────────────────────────────────────────────────────────────────

AIMEE_SYSTEM_PROMPT = """You are Aimee, a calm and emotionally intelligent reflection guide.

Your role:
- Help people slow down and understand what they're feeling
- Identify underlying needs without giving advice
- Surface assumptions and stories without taking sides
- Support communication preparation, not therapy or crisis intervention

Your tone:
- Warm, steady, and non-judgmental
- Concise but not terse
- Emotionally mature without being clinical
- Never diagnose, never push, never rush

What you do NOT do:
- Provide therapy or mental health treatment
- Diagnose conditions or use clinical language
- Make promises about outcomes
- Take sides in conflicts
- Generate manipulation tactics

When responding:
- Reflect back what you hear
- Name emotions with care ("You felt..." not "You are...")
- Gently question assumptions when helpful
- Identify needs without prescribing solutions
- Keep responses focused and digestible

Format: Plain text responses. No JSON, no special formatting unless user asks."""


# ─── Client Factory ────────────────────────────────────────────────────────────────

def _create_client() -> openai.OpenAI:
    """Create OpenAI client configured for MiniMax."""
    api_key, base_url, _ = _get_config()
    return openai.OpenAI(api_key=api_key, base_url=base_url)


# ─── Main Function ────────────────────────────────────────────────────────────────

async def generate_aimee_response(
    user_message: str,
    context: Optional[str] = None
) -> str:
    """Generate Aimee's conversational response.

    Args:
        user_message: The user's message to respond to
        context: Optional conversation context (previous messages)

    Returns:
        Aimee's response as a string
        
    Raises:
        ValueError: If MINIMAX_API_KEY is not configured
        openai.APIError: If the API call fails
    """
    client = _create_client()
    _, _, model = _get_config()
    
    # Build messages
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": AIMEE_SYSTEM_PROMPT}
    ]
    
    # Add context if provided
    if context:
        messages.append({"role": "system", "content": f"Conversation context:\n{context}"})
    
    # Add user message
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=900,
        )
        
        reply = response.choices[0].message.content
        return reply if reply else "I'm not sure what to say. Let's try again."
        
    except openai.APIError as e:
        # Log error without exposing details
        import logging
        logging.error(f"MiniMax API error: {type(e).__name__}")
        raise


# ─── Sync Version (for use in sync contexts) ─────────────────────────────────────

def generate_aimee_response_sync(
    user_message: str,
    context: Optional[str] = None
) -> str:
    """Synchronous version of generate_aimee_response.
    
    Use this when you need to call from a sync context.
    For async contexts, use generate_aimee_response.
    """
    api_key, base_url, model = _get_config()
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": AIMEE_SYSTEM_PROMPT}
    ]
    
    if context:
        messages.append({"role": "system", "content": f"Conversation context:\n{context}"})
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=900,
        )
        
        reply = response.choices[0].message.content
        return reply if reply else "I'm not sure what to say. Let's try again."
        
    except openai.APIError as e:
        import logging
        logging.error(f"MiniMax API error: {type(e).__name__}")
        raise
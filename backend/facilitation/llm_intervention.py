"""
RelateFX — LLM Intervention Generator

Given an InterventionDecision, generates the actual facilitator response text.
Uses MiniMax when available, falls back to deterministic local responses.
"""
import os
import httpx
from openai import OpenAI

from .types import InterventionType, FacilitatorOutput


MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
MINIMAX_MODEL = "MiniMax-M2.7"
MINIMAX_URL = "https://api.minimax.io/v1/text/chatcompletion_v2"
MAX_TOKENS = int(os.environ.get("MINIMAX_MAX_TOKENS", "400"))

# OpenAI-compatible (ChatAnyone proxy) config
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "minimax")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://free.v36.cm/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


INTERVENTION_SYSTEM_PROMPT = """You are RelateFX, an AI relationship facilitation assistant. Your role is to help people communicate more effectively in difficult conversations — couples, family members, partners.

You have five intervention tools you can use. Choose the right one based on what's happening:

1. REFLECT — When someone shares something emotional, paraphrase what you heard AND validate the emotion underneath. Be brief (1-2 sentences).

2. PAUSE — When the conversation is escalating or tense, slow it down. Ask both people to take a breath before continuing. Offer a grounding prompt.

3. INVITE — When one person has been quiet or one person is dominating, bring the quiet person in with a specific, warm invitation.

4. EXERCISE — When emotions are running high and people are stuck, suggest a brief structured exercise (e.g., "let's try one person speaking for 2 minutes while the other just listens").

5. REBALANCE — When one person is dominating the conversation, gently redirect and invite the other person to share.

IMPORTANT RULES:
- Keep responses SHORT — 1 to 3 sentences maximum.
- NEVER take sides. Both people deserve to be heard equally.
- When someone shares something painful, honor the emotion first.
- Be warm but structured — you are a calm facilitator, not a therapist.
- If this is a PAUSE intervention, you may suggest a brief grounding exercise."""


INTERVENTION_USER_PROMPT_TEMPLATE = """Generate a {intervention_type} intervention.

Speaker said: "{speaker_message}"
Speaker name: {speaker_name}
Context: {context}

Respond with a JSON object with a single field "response" containing your intervention text (1-3 sentences).
No markdown. Respond only with JSON."""


LOCAL_INTERVENTIONS = {
    InterventionType.REFLECT: [
        "I hear you. It sounds like what's underneath that is {emotion}. Is that right?",
        "It seems like you're carrying something heavy here. Thank you for sharing it.",
        "I can tell this matters a lot to you. It takes courage to say that.",
    ],
    InterventionType.PAUSE: [
        "Let's take a moment here. Before we continue, I'd like each of you to take one slow breath. We don't have to rush.",
        "I want to slow this down a little. It sounds like we're getting into some tender territory. A brief pause — how are you both feeling right now?",
        "Can we pause for just a breath? This is important work, and it deserves our full attention.",
    ],
    InterventionType.INVITE: [
        "I'd love to hear from the other person here. What's your reaction to what was just shared?",
        "It's natural to listen and react — but I'd also like to check in. How are you experiencing this conversation?",
        "I'd like to make sure everyone has a chance to be heard. What's your perspective?",
    ],
    InterventionType.EXERCISE: [
        "I'd suggest we try something: one person shares for about 2 minutes while the other simply listens, without interrupting. Then we switch.",
        "When emotions run high, sometimes a little structure helps. Let's try this: one person speaks, the other just listens and holds what they hear. Then we switch.",
        "I think a brief exercise might help here. Let's try the speaker-listener format: one person shares, the other reflects back what they heard, then we switch.",
    ],
    InterventionType.REBALANCE: [
        "I've noticed one perspective has been shared quite a bit. I'd love to make sure we hear from everyone. What's your take on this?",
        "Before we go further, I'd like to invite the other person into the conversation. What are you thinking or feeling right now?",
        "I want to make sure this feels balanced. Let's hear from the other person — what's your reaction?",
    ],
}


def _build_intervention_prompt(
    intervention_type: InterventionType,
    speaker_message: str,
    speaker_name: str,
    context: str,
) -> list[dict]:
    """Build the messages for the LLM call."""
    system = {"role": "system", "content": INTERVENTION_SYSTEM_PROMPT}
    user_content = INTERVENTION_USER_PROMPT_TEMPLATE.format(
        intervention_type=intervention_type.value,
        speaker_message=speaker_message,
        speaker_name=speaker_name,
        context=context or "General facilitation",
    )
    return [system, {"role": "user", "content": user_content}]


async def get_llm_intervention(
    intervention_type: InterventionType,
    speaker_message: str,
    speaker_name: str,
    context: str = "",
    conversation_history: list[dict] | None = None,
) -> FacilitatorOutput:
    """
    Generate a facilitator intervention response.
    Uses LLM_PROVIDER to select: openai_compatible, minimax, or local fallback.
    """
    if intervention_type == InterventionType.NONE:
        return FacilitatorOutput(
            response="",
            intervention_type=intervention_type,
            confidence=1.0,
        )

    # Build messages
    messages = _build_intervention_prompt(intervention_type, speaker_message, speaker_name, context)
    if conversation_history:
        history_block = ""
        for u in conversation_history[-8:]:
            speaker = u.get("speaker_name", "Participant")
            history_block += f"{speaker}: {u.get('text', '')}\n"
        messages.insert(1, {"role": "user", "content": f"Conversation so far:\n{history_block}"})

    # Try OpenAI-compatible (ChatAnyone proxy) if configured
    if LLM_PROVIDER == "openai_compatible" and OPENAI_API_KEY:
        try:
            client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=0.7,
            )
            content = response.choices[0].message.content or ""

            # Extract JSON from response
            import json as _json
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end > start:
                try:
                    parsed = _json.loads(content[start:end + 1])
                    response_text = parsed.get("response", content[:100]).strip()
                except _json.JSONDecodeError:
                    response_text = content[:200].strip()
            else:
                response_text = content[:200].strip()

            # Clean leaking <think> response
            response_text = response_text.replace("<think>", "").replace("", "").strip()
            if response_text.startswith("The user"):
                response_text = "Got it. Hi! How are you feeling today?"

            if response_text:
                return FacilitatorOutput(
                    response=response_text,
                    intervention_type=intervention_type,
                    confidence=0.9,
                )
        except Exception as e:
            print(f"[RelateFX] OpenAI-compatible call failed: {e}")
            # Fall through to local fallback

    # Try MiniMax if configured — wrap with 10s timeout to avoid blocking
    if LLM_PROVIDER == "minimax" and MINIMAX_API_KEY:
        import asyncio
        import json as _json
        try:
            payload = {
                "model": MINIMAX_MODEL,
                "max_tokens": MAX_TOKENS,
                "messages": messages,
            }
            async def _call_minimax():
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        MINIMAX_URL,
                        headers={
                            "Authorization": f"Bearer {MINIMAX_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    resp.raise_for_status()
                    return resp.json()

            print(f"[RelateFX] Calling MiniMax for {intervention_type.value} intervention...")
            data = await asyncio.wait_for(_call_minimax(), timeout=10.0)
            print("[RelateFX] MiniMax response received, status=ok")

            content = ""
            choices = data.get("choices", [])
            if choices:
                choice = choices[0]
                message = choice.get("message", {})
                content = message.get("content") or message.get("text") or ""

            print(f"[RelateFX] MiniMax content length: {len(content)}")

            # Extract JSON from response
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end > start:
                try:
                    parsed = _json.loads(content[start:end + 1])
                    response_text = parsed.get("response", content[:100]).strip()
                except _json.JSONDecodeError:
                    response_text = content[:200].strip()
            else:
                response_text = content[:200].strip()

            if response_text:
                print(f"[RelateFX] Returning MiniMax response: {response_text[:80]}...")
                return FacilitatorOutput(
                    response=response_text,
                    intervention_type=intervention_type,
                    confidence=0.9,
                )
            else:
                print("[RelateFX] MiniMax returned empty content, falling back to local")
        except asyncio.TimeoutError:
            print("[RelateFX] MiniMax call timed out after 10s — falling back to local")
        except Exception as e:
            print(f"[RelateFX] MiniMax call failed: {type(e).__name__}: {e} — falling back to local")

    # Local fallback
    return _local_fallback(intervention_type)


def _local_fallback(intervention_type: InterventionType) -> FacilitatorOutput:
    """Return a local fallback intervention."""
    import random
    lines = LOCAL_INTERVENTIONS.get(
        intervention_type,
        LOCAL_INTERVENTIONS[InterventionType.REFLECT],
    )
    return FacilitatorOutput(
        response=random.choice(lines),
        intervention_type=intervention_type,
        confidence=0.5,
    )
"""Aimee extraction service for v2 emotional graph.

Aimee proposes emotional meaning from free-form text.
User confirms. Only confirmed data gets saved.
"""

import os
import json
import re
from typing import Optional

from pydantic import ValidationError

from app.schemas.v2.aimee import (
    ExtractionRequest,
    ExtractionResponse,
    ExtractedFeeling,
    ExtractedEntity,
    ExtractedTopic,
    ExtractedNeed,
    ConfirmRequest,
    ConfirmResponse,
    NeedStatus,
    ChatRequest,
    ChatResponse,
)


LOW_SIGNAL_PATTERNS = [
    re.compile(r"^\s*(hi|hello|hey|yo|sup|good morning|good afternoon|good evening)[.!?\s]*$", re.IGNORECASE),
    re.compile(r"^\s*(i('| a)?m|i am)\s+[a-z][a-z '-]{0,40}[.!?\s]*$", re.IGNORECASE),
    re.compile(r"^\s*(my name is|name'?s)\s+[a-z][a-z '-]{0,40}[.!?\s]*$", re.IGNORECASE),
]


def _extract_intro_name(text: str) -> Optional[str]:
    """Return a first-name-like token from a simple introduction."""
    match = re.match(
        r"^\s*(?:hi[,!\s]*)?(?:i(?:'| a)?m|i am|my name is|name'?s)\s+([a-z][a-z'-]{0,30})\b",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    name = match.group(1).strip(" .,!?\t\n\r")
    if not name:
        return None

    return name[:1].upper() + name[1:].lower()


def _is_low_signal_input(text: str) -> bool:
    """Detect greetings and simple introductions that do not support extraction."""
    cleaned = text.strip()
    if not cleaned:
        return False

    if any(pattern.match(cleaned) for pattern in LOW_SIGNAL_PATTERNS):
        return True

    word_count = len(re.findall(r"\b[\w'-]+\b", cleaned))
    if word_count <= 3 and cleaned.lower() in {"hi there", "hello there", "hey there"}:
        return True

    return False


def _build_low_signal_chat_reply(text: str) -> str:
    """Reply naturally to greetings or introductions without inventing emotion."""
    name = _extract_intro_name(text)
    if name:
        return f"Hi {name}. What would you like help thinking through today?"

    return "Hi. What would you like help thinking through today?"


# ─── Safety Check ────────────────────────────────────────────────────────────────

def check_safety(text: str) -> tuple[bool, str]:
    """
    Check text for safety concerns.
    Returns (is_safe, message).
    """
    text_lower = text.lower()
    
    # Crisis keywords
    crisis_keywords = [
        "kill myself", "end it all", "suicide", "self-harm",
        "overdose", "want to die", "better off dead", "wish i were dead",
        "going to kill", "i were dead",
    ]
    
    # Violence/threat keywords  
    violence_keywords = [
        "hurt myself", "harm myself", "hurting myself",
    ]
    
    for keyword in crisis_keywords:
        if keyword in text_lower:
            return False, "It sounds like you might be going through something really difficult. I'm concerned about you. Please reach out to 988 Suicide & Crisis Lifeline (call or text 988) or Crisis Text Line (text HOME to 741741). You don't have to face this alone."
    
    for keyword in violence_keywords:
        if keyword in text_lower:
            return False, "I'm concerned about what you're going through. If you're thinking of hurting yourself, please reach out for support: 988 Suicide & Crisis Lifeline or Crisis Text Line (text HOME to 741741)."
    
    return True, ""


# ─── AI Extraction (Mock for tests / Real when API key available) ──────────────

async def extract_emotions(request: ExtractionRequest) -> ExtractionResponse:
    """
    Extract emotional meaning from text using AI.
    
    This function:
    1. Runs safety check first
    2. If flagged, returns safe response (no extraction)
    3. If safe, calls AI for structured extraction
    4. Validates output with Pydantic
    """
    # Step 1: Safety check
    is_safe, message = check_safety(request.text)
    
    if not is_safe:
        return ExtractionResponse(
            feelings=[],
            suggested_memory_title="",
            suggested_response=message,
            safety_status="flagged",
        )

    if _is_low_signal_input(request.text):
        return ExtractionResponse(
            feelings=[],
            suggested_memory_title="",
            suggested_response="",
            safety_status="safe",
        )
    
    # Step 2: Try AI extraction (MiniMax or OpenAI)
    api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        return await _extract_with_openai(request.text)
    else:
        return _extract_with_mock(request.text)


async def _extract_with_openai(text: str) -> ExtractionResponse:
    """Extract emotions using MiniMax (OpenAI-compatible API)."""
    import openai
    
    system_prompt = """You are Aimee, a feelings guide. You help people understand their emotions.

For each text, identify:
1. The primary emotion (joy, sadness, anger, fear, or disgust)
2. A specific label for that emotion
3. The intensity (1-10 scale)
4. Any entities (people, companies, etc.) mentioned
5. Any topics or themes
6. Underlying needs (using Nonviolent Communication framework)

Important guardrails:
- Stay anchored to what the person actually said.
- If the text is only a greeting, introduction, or name, return no feelings and no needs.
- Do not invent sadness, hurt, or any other emotion when the signal is thin.

Be specific and empathetic. Use non-blaming language ("You felt angry" not "X made you angry").

Return a JSON object with:
- feelings: array of feeling objects
- suggested_memory_title: brief title for this emotional moment
- suggested_response: Aimee's empathetic acknowledgment

Example format:
{
  "feelings": [
    {
      "primary_emotion": "anger",
      "label": "frustrated",
      "intensity": 7,
      "entities": [{"name": "Starbucks", "entity_type": "company"}],
      "topics": [{"title": "rising prices"}],
      "needs": [{"name": "fairness", "status": "identified"}],
      "confidence": 0.88
    }
  ],
  "suggested_memory_title": "Feeling angry about rising prices",
  "suggested_response": "That frustration seems connected to your need for fairness. Does that resonate?"
}"""

    # Use MiniMax endpoint if configured, otherwise fallback
    base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("MINIMAX_MODEL", "MiniMax-Text-01")
    
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Parse into Pydantic models
        feelings = []
        for f in result.get("feelings", []):
            try:
                feelings.append(ExtractedFeeling(
                    primary_emotion=f["primary_emotion"],
                    label=f["label"],
                    intensity=f["intensity"],
                    confidence=f.get("confidence", 0.8),
                    entities=[ExtractedEntity(**e) for e in f.get("entities", [])],
                    topics=[ExtractedTopic(**t) for t in f.get("topics", [])],
                    needs=[ExtractedNeed(
                        name=n["name"],
                        status=NeedStatus(n.get("status", "identified"))
                    ) for n in f.get("needs", [])],
                ))
            except (KeyError, ValidationError):
                continue
        
        return ExtractionResponse(
            feelings=feelings,
            suggested_memory_title=result.get("suggested_memory_title", ""),
            suggested_response=result.get("suggested_response", ""),
            safety_status="safe",
        )
    except Exception as e:
        # Log error for debugging
        print(f"MINIMAX ERROR: {type(e).__name__}: {e}")
        # Fallback to mock on error
        return _extract_with_mock(text)


def _extract_with_mock(text: str) -> ExtractionResponse:
    """Mock extraction for testing and when no API key is available."""
    text_lower = text.lower()

    if _is_low_signal_input(text):
        return ExtractionResponse(
            feelings=[],
            suggested_memory_title="",
            suggested_response="",
            safety_status="safe",
        )
    
    # Simple keyword-based mock extraction
    feelings = []
    title = "Emotional moment"
    response = "Thank you for sharing that with me."
    
    # Detect emotion keywords
    if any(w in text_lower for w in ["angry", "frustrated", "mad", "annoyed"]):
        feelings.append(ExtractedFeeling(
            primary_emotion="anger",
            label="frustrated",
            intensity=6.0,
            confidence=0.75,
            entities=[],
            topics=[ExtractedTopic(title="general")],
            needs=[ExtractedNeed(name="understanding", status=NeedStatus.IDENTIFIED)],
        ))
        title = "Feeling frustrated"
        response = "That frustration makes sense. What's behind it?"
    elif any(w in text_lower for w in ["sad", "hurt", "disappointed", "lonely"]):
        feelings.append(ExtractedFeeling(
            primary_emotion="sadness",
            label="hurt",
            intensity=6.0,
            confidence=0.75,
            entities=[],
            topics=[ExtractedTopic(title="general")],
            needs=[ExtractedNeed(name="connection", status=NeedStatus.IDENTIFIED)],
        ))
        title = "Feeling sad"
        response = "I hear the sadness in what you're sharing."
    elif any(w in text_lower for w in ["happy", "joy", "excited", "grateful"]):
        feelings.append(ExtractedFeeling(
            primary_emotion="joy",
            label="happy",
            intensity=7.0,
            confidence=0.75,
            entities=[],
            topics=[ExtractedTopic(title="general")],
            needs=[ExtractedNeed(name="meaning", status=NeedStatus.IDENTIFIED)],
        ))
        title = "Feeling joyful"
        response = "It's wonderful that you're feeling this way!"
    elif any(w in text_lower for w in ["scared", "afraid", "worried", "anxious"]):
        feelings.append(ExtractedFeeling(
            primary_emotion="fear",
            label="anxious",
            intensity=6.0,
            confidence=0.75,
            entities=[],
            topics=[ExtractedTopic(title="general")],
            needs=[ExtractedNeed(name="safety", status=NeedStatus.IDENTIFIED)],
        ))
        title = "Feeling anxious"
        response = "That anxiety is telling you something. What would help you feel safer?"
    elif any(w in text_lower for w in ["disgusted", "gross", "ew", "ugh"]):
        feelings.append(ExtractedFeeling(
            primary_emotion="disgust",
            label="disgusted",
            intensity=5.0,
            confidence=0.75,
            entities=[],
            topics=[ExtractedTopic(title="general")],
            needs=[ExtractedNeed(name="integrity", status=NeedStatus.IDENTIFIED)],
        ))
        title = "Feeling disgusted"
        response = "That reaction makes sense given what you're experiencing."
    else:
        # Default fallback
        feelings.append(ExtractedFeeling(
            primary_emotion="sadness",
            label="uncertain",
            intensity=5.0,
            confidence=0.5,
            entities=[],
            topics=[ExtractedTopic(title="general")],
            needs=[ExtractedNeed(name="clarity", status=NeedStatus.UNKNOWN)],
        ))
        title = "Emotional moment"
        response = "Thank you for sharing. Let's explore what you're feeling."
    
    return ExtractionResponse(
        feelings=feelings,
        suggested_memory_title=title,
        suggested_response=response,
        safety_status="safe",
    )


# ─── Conversational Chat ──────────────────────────────────────────────────────

async def chat_with_aimee(request: ChatRequest) -> ChatResponse:
    """
    Free-form conversational chat with Aimee.
    
    This is Aimee's guide voice - warm, listening, asking gentle questions.
    Safety check runs first. Crisis input returns crisis response.
    """
    # Step 1: Safety check
    is_safe, crisis_message = check_safety(request.message)
    
    if not is_safe:
        return ChatResponse(
            reply=crisis_message,
            safety_status="flagged",
        )

    if _is_low_signal_input(request.message):
        return ChatResponse(
            reply=_build_low_signal_chat_reply(request.message),
            safety_status="safe",
        )
    
    # Step 2: Build conversation context
    system_prompt = """You are Aimee, a calm and thoughtful reflection guide for Feltabout.

You help people understand their feelings through gentle conversation. 
You listen carefully, acknowledge what's shared, and ask one thoughtful question at a time.
You do not lecture, diagnose, or rush to solutions.

Your style:
- Calm and unhurried
- Warm but not effusive
- Curious about what matters to the person
- Ask one question at a time when appropriate
- Non-judgmental about any emotion or situation
- Grounded in the user's actual words

Rules:
- Do not infer emotions, needs, or conflict from a greeting or simple introduction.
- If the person only says hello or shares their name, greet them briefly and ask what they want help thinking through.
- Do not use therapy language or generic filler like "Thank you for sharing that with me."

Remember: you are a guide for reflection, not a therapist or advisor."""

    messages = []
    if request.conversation_context:
        messages.append({"role": "system", "content": system_prompt})
        # Add context as a user message for continuity
        context_msg = f"Here's our recent conversation:\n{request.conversation_context}\n\nThe person just said: {request.message}"
        messages.append({"role": "user", "content": context_msg})
    else:
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": request.message})
    
    # Step 3: Try AI chat (MiniMax or mock)
    api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        return await _chat_with_openai(messages, request.message)
    else:
        return _chat_with_mock(request.message)


async def _chat_with_openai(
    messages: list[dict],
    original_message: str,
) -> ChatResponse:
    """Chat using MiniMax (OpenAI-compatible API)."""
    import openai
    
    base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("MINIMAX_MODEL", "MiniMax-Text-01")
    
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
        )
        
        reply = response.choices[0].message.content.strip()
        return ChatResponse(reply=reply, safety_status="safe")
    except Exception as e:
        print(f"MINIMAX CHAT ERROR: {type(e).__name__}: {e}")
        return _chat_with_mock(original_message)


def _chat_with_mock(message: str) -> ChatResponse:
    """Mock chat for testing and when no API key is available."""
    text_lower = message.lower()

    if _is_low_signal_input(message):
        return ChatResponse(reply=_build_low_signal_chat_reply(message), safety_status="safe")
    
    # Warm, reflective responses
    if any(w in text_lower for w in ["angry", "frustrated", "mad", "annoyed"]):
        reply = "That frustration sounds heavy. What's underneath it, if you feel like saying more?"
    elif any(w in text_lower for w in ["sad", "hurt", "disappointed", "lonely"]):
        reply = "I hear that sense of hurt. Take your time — what's closest to how you're feeling right now?"
    elif any(w in text_lower for w in ["happy", "joy", "excited", "grateful"]):
        reply = "That's really lovely to hear. What made this moment feel especially good?"
    elif any(w in text_lower for w in ["scared", "afraid", "worried", "anxious"]):
        reply = "Anxiety can feel like a lot. What's the part that's weighing on you most?"
    elif any(w in text_lower for w in ["disgusted", "gross", "ew", "ugh"]):
        reply = "That reaction makes sense. What was it about the situation that felt off?"
    elif any(w in text_lower for w in ["help", "advice", "should i"]):
        reply = "I'm not here to give advice, but I'm happy to listen. What's going on?"
    else:
        reply = "Tell me a little more about what's going on."
    
    return ChatResponse(reply=reply, safety_status="safe")


# ─── Confirmation (Save to Emotional Graph) ──────────────────────────────────

async def confirm_extraction(
    request: ConfirmRequest,
    user_id: str,
) -> ConfirmResponse:
    """
    Save user-confirmed extraction to the emotional graph.
    
    This is the ONLY place where AI-proposed data gets saved.
    User has reviewed and confirmed all data.
    """
    from app.services.v2.memory_service import MemoryService
    from app.db.session import async_session_factory
    from app.schemas.v2.memory import CreateMemoryRequest, CreateFeelingInput
    
    # Build nested memory request from confirmed data
    feelings = [
        CreateFeelingInput(
            primary_emotion=f.primary_emotion.value,
            label=f.label,
            intensity=f.intensity,
            confidence=f.confidence,
            source_text=f.source_text,
            occurred_at=f.occurred_at,
        )
        for f in request.feelings
    ]
    
    # Collect all unique entity/topic/need names
    entity_names = list(set(
        name for f in request.feelings for name in f.entity_names
    ))
    topic_titles = list(set(
        title for f in request.feelings for title in f.topic_titles
    ))
    need_names = list(set(
        name for f in request.feelings for name in f.need_names
    ))
    
    memory_request = CreateMemoryRequest(
        title=request.memory_title,
        narrative=request.memory_narrative,
        ai_summary="",  # No AI summary for confirmed data
        occurred_at=request.occurred_at,
        privacy_level="private",
        feelings=feelings,
        entity_names=entity_names,
        topic_titles=topic_titles,
        need_names=need_names,
    )
    
    # Save to database
    async with async_session_factory() as db:
        memory = await MemoryService.create_with_nested(db, user_id, memory_request)
        
        return ConfirmResponse(
            memory_id=memory.id,
            feelings_count=len(memory.feelings),
            status="saved",
        )

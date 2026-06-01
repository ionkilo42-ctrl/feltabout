"""Aimee extraction service for v2 emotional graph.

Aimee proposes emotional meaning from free-form text.
User confirms. Only confirmed data gets saved.
"""

import json
import re
from typing import Optional

from pydantic import ValidationError
from app.services.ai_router import get_ai_router, provider_has_key

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
    re.compile(r"^\s*(i('| a)?m|i am)\s+[a-z][a-z'-]{0,30}[.!?\s]*$", re.IGNORECASE),
    re.compile(r"^\s*(my name is|name'?s)\s+[a-z][a-z '-]{0,40}[.!?\s]*$", re.IGNORECASE),
]

REVIEW_REQUEST_PATTERNS = [
    re.compile(r"\b(can we|could you|please)?\s*save (this|that|it)?\b", re.IGNORECASE),
    re.compile(r"\b(i('| a)?m|i am)\s+(done|finished)\b", re.IGNORECASE),
    re.compile(r"\bthat'?s (it|enough|all)\b", re.IGNORECASE),
    re.compile(r"\bready to save\b", re.IGNORECASE),
    re.compile(r"\blet'?s save\b", re.IGNORECASE),
    re.compile(r"\bwrap (this )?up\b", re.IGNORECASE),
]


def _extract_intro_name(text: str) -> Optional[str]:
    """Return a first-name-like token from a simple introduction."""
    match = re.match(
        r"^\s*(?:hi[,!\s]*)?(?:i(?:'| a)?m|i am|my name is|name'?s)\s+([a-z][a-z'-]{0,30})[.!?\s]*$",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    name = match.group(1).strip(" .,!?\t\n\r")
    if not name:
        return None

    return name[:1].upper() + name[1:].lower()


def _has_unnegated_keyword(text: str, keywords: list[str]) -> bool:
    """Return true when any keyword appears without a simple local negation."""
    for keyword in keywords:
        pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            prefix = text[max(0, match.start() - 12):match.start()].lower()
            if re.search(r"(?:\bnot\s+|n't\s+)$", prefix):
                continue
            return True
    return False


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


def _wants_review_or_save(text: str) -> bool:
    """Detect when the user signals they want to review or save."""
    cleaned = text.strip()
    if not cleaned:
        return False

    return any(pattern.search(cleaned) for pattern in REVIEW_REQUEST_PATTERNS)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _build_chat_system_prompt(message: str, should_offer_review: bool) -> str:
    """Build the Aimee prompt with pacing guidance tied to the user's message size."""
    user_words = max(_word_count(message), 1)
    lower_bound = max(6, round(user_words * 0.6))
    upper_bound = max(lower_bound + 2, round(user_words * 1.4))
    review_mode = "yes" if should_offer_review else "no"

    return f"""You are Aimee, a calm reflection guide for Feltabout.

You help people think clearly about difficult conversations.
You are not a therapist, not a clinician, and not an advice machine.

Voice and pacing:
- Keep the reply conversational, human, and simple.
- Match the user's conversational size. Target roughly {lower_bound}-{upper_bound} words for this turn unless safety requires otherwise.
- Start with a brief acknowledgment when the message carries emotion.
- Follow with one focused reflection.
- Ask at most one gentle question.
- No lists, tables, JSON, headings, or structured analysis in normal conversation.
- Do not dump big summaries, emotional inventories, or reviews unless the user explicitly wants review/save.
- Do not use therapy language, clinical framing, or dependency language.
- Stay grounded in the user's actual words and specifics.

Special handling:
- If the person only says hello or shares their name, greet them briefly and ask what they want help thinking through.
- If the person signals they are done or want to save: review_mode={review_mode}. Briefly acknowledge that, avoid another exploratory question, and say you can review what seems worth saving.

Remember: Feltabout is for reflection and conversation preparation, not therapy."""


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
    
    # Step 2: Try AI extraction through the shared provider router.
    if provider_has_key():
        return await _extract_with_router(request.text)
    else:
        return _extract_with_mock(request.text)


async def _extract_with_router(text: str) -> ExtractionResponse:
    """Extract emotions using the shared AI router."""
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

    try:
        router = get_ai_router()
        content = await router.generate(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=1000,
        )

        result = json.loads(content)
        
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
        print(f"AI EXTRACTION ERROR: {type(e).__name__}: {e}")
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
    if _has_unnegated_keyword(text, ["angry", "frustrated", "mad", "annoyed"]):
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
    elif _has_unnegated_keyword(text, ["sad", "hurt", "disappointed", "lonely"]):
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
    elif _has_unnegated_keyword(text, ["happy", "joy", "excited", "grateful"]):
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
    elif _has_unnegated_keyword(text, ["scared", "afraid", "worried", "anxious"]):
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
    elif _has_unnegated_keyword(text, ["disgusted", "gross", "ew", "ugh"]):
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
        # Thin or ambiguous input should not fabricate an emotion.
        return ExtractionResponse(
            feelings=[],
            suggested_memory_title="",
            suggested_response="",
            safety_status="safe",
        )
    
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
            should_offer_review=False,
        )

    if _is_low_signal_input(request.message):
        return ChatResponse(
            reply=_build_low_signal_chat_reply(request.message),
            safety_status="safe",
            should_offer_review=False,
        )

    should_offer_review = _wants_review_or_save(request.message)
    
    # Step 2: Build conversation context with optional participant awareness
    system_prompt = _build_chat_system_prompt(request.message, should_offer_review)

    # Build full context with participant information if available
    full_context = ""
    if request.participant_context:
        full_context += f"{request.participant_context}\n\n"
    if request.conversation_context:
        full_context += f"Recent conversation:\n{request.conversation_context}\n\n"
    
    messages = []
    if full_context:
        messages.append({"role": "system", "content": system_prompt})
        # Add context as a user message for continuity
        context_msg = f"{full_context}The person just said: {request.message}"
        messages.append({"role": "user", "content": context_msg})
    else:
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": request.message})
    
    # Step 3: Try AI chat through the shared provider router.
    if provider_has_key():
        return await _chat_with_router(messages, request.message, should_offer_review)
    else:
        return _chat_with_mock(request.message, should_offer_review)


async def _chat_with_router(
    messages: list[dict],
    original_message: str,
    should_offer_review: bool,
) -> ChatResponse:
    """Chat using the shared AI router."""
    try:
        router = get_ai_router()
        reply = await router.generate(
            messages,
            max_tokens=1000,
        )
        return ChatResponse(
            reply=reply.strip(),
            safety_status="safe",
            should_offer_review=should_offer_review,
        )
    except Exception as e:
        print(f"AI CHAT ERROR: {type(e).__name__}: {e}")
        return _chat_with_mock(original_message, should_offer_review)


def _chat_with_mock(message: str, should_offer_review: bool) -> ChatResponse:
    """Mock chat for testing and when no API key is available."""
    text_lower = message.lower()

    if _is_low_signal_input(message):
        return ChatResponse(
            reply=_build_low_signal_chat_reply(message),
            safety_status="safe",
            should_offer_review=False,
        )

    if should_offer_review:
        return ChatResponse(
            reply="We can do that. I'll keep this simple and help you review what seems worth saving before we save it.",
            safety_status="safe",
            should_offer_review=True,
        )
    
    if _has_unnegated_keyword(message, ["angry", "frustrated", "mad", "annoyed"]):
        reply = (
            "That sounds painful.\n\n"
            "You care about what happened here, and the anger seems tied to that. "
            "What hit hardest for you?"
        )
    elif _has_unnegated_keyword(message, ["sad", "hurt", "disappointed", "lonely"]):
        reply = (
            "That seems significant.\n\n"
            "There is some hurt in this, not just the event itself. "
            "What feels most exposed right now?"
        )
    elif _has_unnegated_keyword(message, ["happy", "joy", "excited", "grateful"]):
        reply = "That sounds good.\n\nWhat feels most meaningful about it?"
    elif _has_unnegated_keyword(message, ["scared", "afraid", "worried", "anxious"]):
        reply = (
            "That sounds like a lot to hold.\n\n"
            "There is something uncertain here that's pressing on you. "
            "What part feels most risky?"
        )
    elif _has_unnegated_keyword(message, ["disgusted", "gross", "ew", "ugh"]):
        reply = "That reaction makes sense.\n\nWhat felt most off about it?"
    elif any(w in text_lower for w in ["help", "advice", "should i"]):
        reply = "I can help you think it through.\n\nWhat happened?"
    else:
        reply = "Tell me a little more.\n\nWhat feels most important in this?"
    
    return ChatResponse(
        reply=reply,
        safety_status="safe",
        should_offer_review=False,
    )


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

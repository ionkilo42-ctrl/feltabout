"""Aimee extraction service for v2 emotional graph.

Aimee proposes emotional meaning from free-form text.
User confirms. Only confirmed data gets saved.
"""

import os
import json
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
)


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
    
    # Step 2: Try AI extraction
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        return await _extract_with_openai(request.text)
    else:
        return _extract_with_mock(request.text)


async def _extract_with_openai(text: str) -> ExtractionResponse:
    """Extract emotions using OpenAI."""
    import openai
    
    system_prompt = """You are Aimee, a feelings guide. You help people understand their emotions.

For each text, identify:
1. The primary emotion (joy, sadness, anger, fear, or disgust)
2. A specific label for that emotion
3. The intensity (1-10 scale)
4. Any entities (people, companies, etc.) mentioned
5. Any topics or themes
6. Underlying needs (using Nonviolent Communication framework)

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
        response = await openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY")).chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
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
        # Fallback to mock on error
        return _extract_with_mock(text)


def _extract_with_mock(text: str) -> ExtractionResponse:
    """Mock extraction for testing and when no API key is available."""
    text_lower = text.lower()
    
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
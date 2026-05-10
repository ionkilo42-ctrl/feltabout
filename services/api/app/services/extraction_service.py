"""
Extraction Service — Staged emotional analysis pipeline.

This service extracts internal emotional analysis from reflection data
using framework-aligned detection patterns. Output powers the
Facilitation Engine without exposing clinical labels to users.

Frameworks integrated:
- NVC: emotion taxonomy, needs inventory
- Gottman: Four Horsemen conflict markers
- Brené Brown: guilt vs shame distinction
- EFT: attachment fears
- Polyvagal: nervous system states
- IFS: memory candidate detection
"""

import os
from typing import Optional

from app.schemas.emotional_analysis import InternalAnalysis
from app.services.ai_router import get_ai_router, AIRouter
from app.prompts.extraction_prompt import (
    get_extraction_messages,
    parse_extraction_json,
)


# ─── Config ────────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


# ─── Fallback Analysis ─────────────────────────────────────────────────────────

def get_fallback_analysis(reflection: dict) -> InternalAnalysis:
    """Generate minimal internal analysis when no API is available.
    
    This provides a graceful fallback that still extracts basic information
    from the reflection data.
    """
    from app.schemas.emotional_analysis import (
        EmotionSignal,
        EmotionCategory,
        NeedSignal,
        NeedCategory,
    )
    
    # Extract basic emotions from feelings field
    feelings = reflection.get("feelings", "")
    primary_emotions = []
    
    if feelings:
        # Simple heuristic extraction
        words = feelings.lower()
        emotion_map = {
            "frustrat": EmotionCategory.FRUSTRATED,
            "angry": EmotionCategory.ANGRY,
            "hurt": EmotionCategory.HURT,
            "sad": EmotionCategory.SAD,
            "anxious": EmotionCategory.ANXIOUS,
            "worried": EmotionCategory.WORRIED,
            "scared": EmotionCategory.SCARED,
            "confused": EmotionCategory.CONFUSED,
            "overwhelm": EmotionCategory.OVERWHELMED,
            "exhaust": EmotionCategory.EXHAUSTED,
            "disconnect": EmotionCategory.DISCONNECTED,
            "disappoint": EmotionCategory.DISAPPOINTED,
        }
        
        for word, emotion in emotion_map.items():
            if word in words:
                primary_emotions.append(
                    EmotionSignal(
                        name=emotion,
                        intensity=0.7,
                        source_text=feelings[:100],
                    )
                )
                break
        
        if not primary_emotions:
            primary_emotions.append(
                EmotionSignal(
                    name=EmotionCategory.FRUSTRATED,
                    intensity=0.5,
                    source_text=feelings[:100],
                )
            )
    
    # Extract basic needs
    needs_field = reflection.get("needs", "")
    needs = []
    
    if needs_field:
        need_map = {
            "respect": NeedCategory.RESPECT,
            "understand": NeedCategory.UNDERSTANDING,
            "hear": NeedCategory.CONNECTION,
            "listen": NeedCategory.CONNECTION,
            "support": NeedCategory.SUPPORT,
            "trust": NeedCategory.TRUST,
            "safety": NeedCategory.SECURITY,
            "clarity": NeedCategory.CLARITY,
            "fair": NeedCategory.FAIRNESS,
        }
        
        for word, need in need_map.items():
            if word in needs_field.lower():
                needs.append(
                    NeedSignal(
                        category=need,
                        text=needs_field[:100],
                        intensity=0.7,
                    )
                )
                break
        
        if not needs:
            needs.append(
                NeedSignal(
                    category=NeedCategory.CONNECTION,
                    text=needs_field[:100],
                    intensity=0.6,
                )
            )
    
    return InternalAnalysis(
        primary_emotions=primary_emotions,
        secondary_emotions=[],
        needs=needs,
        values=[],
        conflict_markers=[],
        shame_markers=[],
        attachment_markers=[],
        nervous_system_markers=[],
        memory_candidates=[],
        conversation_risks=[],
    )


# ─── Extraction Service ───────────────────────────────────────────────────────────

class ExtractionService:
    """
    Extraction Engine for staged emotional analysis.
    
    Responsible for:
    - Converting reflection data into InternalAnalysis
    - Using AI for structured extraction
    - Providing fallback for when no API key is available
    
    This is the first stage in the Facilitation pipeline (after Safety).
    """
    
    def __init__(self, ai_router: Optional[AIRouter] = None):
        self.ai_router = ai_router or get_ai_router()
    
    async def analyze(
        self,
        reflection: dict,
        api_key: Optional[str] = None,
        model: str = OPENAI_MODEL,
    ) -> InternalAnalysis:
        """
        Extract internal analysis from reflection data.
        
        Args:
            reflection: Dict with keys: situation, feelings, interpretation, needs, fears, desired_outcome, message_draft
            api_key: Optional API key override
            model: Model to use
            
        Returns:
            InternalAnalysis object with extracted emotional intelligence
        """
        if api_key and OPENAI_API_KEY or OPENAI_API_KEY:
            try:
                router = self.ai_router
                if api_key:
                    router = AIRouter(api_key=api_key, model=model)
                
                messages = get_extraction_messages(reflection)
                content = await router.generate(messages)
                
                # Parse JSON response
                parsed = parse_extraction_json(content)
                
                if parsed:
                    return InternalAnalysis(**parsed)
                else:
                    # Fall back to default analysis if parsing fails
                    return get_fallback_analysis(reflection)
            
            except Exception:
                # On any error, fall back to basic extraction
                return get_fallback_analysis(reflection)
        else:
            # No API key available — use fallback
            return get_fallback_analysis(reflection)
    
    async def analyze_with_fallback(
        self,
        reflection: dict,
        api_key: Optional[str] = None,
        model: str = OPENAI_MODEL,
    ) -> InternalAnalysis:
        """
        Alias for analyze() — always returns a valid InternalAnalysis.
        
        This is the recommended method for production use.
        """
        return await self.analyze(reflection, api_key, model)

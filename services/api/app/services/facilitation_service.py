"""
Facilitation Service — Conversation plan generation.

This is the Facilitation Engine in feltabout's three-engine architecture.
Handles AI-powered conversation planning with proper prompt structure.
Uses staged extraction pipeline for enhanced output quality.

Pipeline:
  1. Safety check (SafetyService)
  2. Emotion extraction (ExtractionService)
  3. Needs extraction (ExtractionService)
  4. Conflict detection (ExtractionService)
  5. Shame detection (ExtractionService)
  6. Conversation planning with analysis context
  7. Final assembly
"""

import json
import os
from typing import Optional

from app.services.ai_router import get_ai_router, AIRouter


# ─── Config ────────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")


# ─── Facilitation Service ──────────────────────────────────────────────────────

class FacilitationService:
    """
    Facilitation Engine for feltabout.
    
    Responsible for:
    - Converting reflection data into conversation plans
    - Reframing emotional content into calm, clear language
    - Generating conversation openers, follow-up questions, repair statements
    
    Can use InternalAnalysis from ExtractionService for enhanced output.
    """
    
    def __init__(self, ai_router: Optional[AIRouter] = None):
        self.ai_router = ai_router or get_ai_router()
    
    async def generate_conversation_plan(
        self,
        reflection: dict,
        api_key: Optional[str] = None,
        model: str = OPENAI_MODEL,
    ) -> dict:
        """
        Generate a conversation plan from reflection data (legacy method).
        
        Args:
            reflection: Dict with keys: situation, feelings, interpretation, needs, fears, desired_outcome, message_draft
            api_key: Optional API key override
            model: Model to use
            
        Returns:
            Dict with keys: emotional_summary, needs_summary, assumptions, reframe, avoid_saying, conversation_opener, followup_questions, repair_statement
        """
        prompt = self._build_facilitation_prompt(reflection)
        messages = [{"role": "user", "content": prompt}]
        
        if (api_key and AI_PROVIDER == "openai") or OPENAI_API_KEY:
            router = self.ai_router
            if api_key:
                router = AIRouter(api_key=api_key, model=model)
            try:
                content = await router.generate(messages)
                return self._parse_json_content(content)
            except Exception:
                return self._fallback_plan(reflection)
        else:
            return self._fallback_plan(reflection)
    
    async def generate_with_analysis(
        self,
        reflection: dict,
        analysis: dict,
        api_key: Optional[str] = None,
        model: str = OPENAI_MODEL,
    ) -> dict:
        """
        Generate a conversation plan with internal analysis context.
        
        This is the analysis-aware method that produces enhanced outputs
        by using the framework-aligned extraction results.
        
        Args:
            reflection: Dict with reflection data
            analysis: InternalAnalysis as dict (from ExtractionService)
            api_key: Optional API key override
            model: Model to use
            
        Returns:
            Dict with conversation plan fields
        """
        prompt = self._build_analysis_aware_prompt(reflection, analysis)
        messages = [{"role": "user", "content": prompt}]
        
        if (api_key and AI_PROVIDER == "openai") or OPENAI_API_KEY:
            router = self.ai_router
            if api_key:
                router = AIRouter(api_key=api_key, model=model)
            try:
                content = await router.generate(messages)
                result = self._parse_json_content(content)
                if result:
                    return result
            except Exception:
                pass
        
        # Fallback to basic plan with analysis hints
        return self._fallback_with_analysis(reflection, analysis)
    
    def _build_analysis_aware_prompt(self, reflection: dict, analysis: dict) -> str:
        """Build facilitation prompt with analysis context."""
        # Build context from analysis
        context_parts = []
        
        # Top emotions
        primary_emotions = analysis.get("primary_emotions", [])
        if primary_emotions:
            emotion_names = [e.get("name", "") for e in primary_emotions[:3]]
            context_parts.append(f"Detected emotions: {', '.join(emotion_names)}")
        
        # Needs
        needs = analysis.get("needs", [])
        if needs:
            need_names = [n.get("category", "") for n in needs[:3]]
            context_parts.append(f"Underlying needs: {', '.join(need_names)}")
        
        # Conflict markers
        conflict_markers = analysis.get("conflict_markers", [])
        if conflict_markers:
            marker_types = [m.get("type", "") for m in conflict_markers]
            context_parts.append(f"Conflict patterns: {', '.join(marker_types)}")
        
        # Shame markers
        shame_markers = analysis.get("shame_markers", [])
        has_shame = any(m.get("shame_type") == "shame" for m in shame_markers)
        if has_shame:
            context_parts.append("Shame patterns detected - use gentle, validating tone")
        
        # Conversation risks
        conversation_risks = analysis.get("conversation_risks", [])
        high_risks = [r.get("risk_type") for r in conversation_risks if r.get("severity", 0) > 0.5]
        if high_risks:
            context_parts.append(f"Conversation risks to address: {', '.join(high_risks)}")
        
        analysis_context = "\n".join(context_parts) if context_parts else "No specific patterns detected."
        
        return f"""You are feltabout, an AI communication guidance assistant. Your role is to help people
prepare for difficult conversations with empathy, clarity, and emotional intelligence.

IMPORTANT: You are NOT a therapist. You do NOT diagnose. You do NOT provide mental health treatment.
You offer reflection prompts, communication guidance, and conversation preparation support.

INTERNAL ANALYSIS (for your reference, do not expose clinical labels to user):
{analysis_context}

Given the following reflection data, generate a structured conversation plan:

SITUATION: {reflection.get('situation', '')}
FEELINGS: {reflection.get('feelings', '')}
INTERPRETATION (story you're telling yourself): {reflection.get('interpretation', '')}
NEEDS: {reflection.get('needs', '')}
FEARS: {reflection.get('fears', '')}
DESIRED OUTCOME: {reflection.get('desired_outcome', '')}
MESSAGE DRAFT: {reflection.get('message_draft', '')}

Generate a JSON response with these exact fields (no markdown, no explanation, just the JSON):
{{
  "emotional_summary": "2-3 sentence summary of the emotional landscape",
  "needs_summary": "2-3 sentence summary of the underlying needs",
  "assumptions": "List of 2-3 possible assumptions being made (gentle, non-judgmental)",
  "reframe": "A gentle reframe of the situation that opens space for understanding",
  "avoid_saying": "2-3 specific things to avoid saying and why",
  "conversation_opener": "A calm, non-accusatory way to begin the conversation",
  "followup_questions": "2-3 follow-up questions to explore understanding",
  "repair_statement": "A closing statement oriented toward repair and connection"
}}

Style: calm, warm, practical, non-clinical. Avoid therapy language. Be specific and actionable."""
    
    def _build_facilitation_prompt(self, reflection: dict) -> str:
        """Build the facilitation prompt from reflection data."""
        return f"""You are feltabout, an AI communication guidance assistant. Your role is to help people
prepare for difficult conversations with empathy, clarity, and emotional intelligence.

IMPORTANT: You are NOT a therapist. You do NOT diagnose. You do NOT provide mental health treatment.
You offer reflection prompts, communication guidance, and conversation preparation support.

Given the following reflection data, generate a structured conversation plan:

SITUATION: {reflection.get('situation', '')}
FEELINGS: {reflection.get('feelings', '')}
INTERPRETATION (story you're telling yourself): {reflection.get('interpretation', '')}
NEEDS: {reflection.get('needs', '')}
FEARS: {reflection.get('fears', '')}
DESIRED OUTCOME: {reflection.get('desired_outcome', '')}
MESSAGE DRAFT: {reflection.get('message_draft', '')}

Generate a JSON response with these exact fields (no markdown, no explanation, just the JSON):
{{
  "emotional_summary": "2-3 sentence summary of the emotional landscape",
  "needs_summary": "2-3 sentence summary of the underlying needs",
  "assumptions": "List of 2-3 possible assumptions being made (gentle, non-judgmental)",
  "reframe": "A gentle reframe of the situation that opens space for understanding",
  "avoid_saying": "2-3 specific things to avoid saying and why",
  "conversation_opener": "A calm, non-accusatory way to begin the conversation",
  "followup_questions": "2-3 follow-up questions to explore understanding",
  "repair_statement": "A closing statement oriented toward repair and connection"
}}

Style: calm, warm, practical, non-clinical. Avoid therapy language. Be specific and actionable."""
    
    def _parse_json_content(self, content: str) -> dict:
        """Extract JSON from LLM response."""
        if not content:
            return {}
        
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(content[start:end + 1])
            except Exception:
                pass
        return {}
    
    def _fallback_plan(self, reflection: dict) -> dict:
        """Generate a local fallback plan when no API is available."""
        return {
            "emotional_summary": f"It sounds like you're navigating something difficult. You mentioned feeling: {reflection.get('feelings', 'unsure')[:100]}.",
            "needs_summary": f"Underneath the situation, you may be looking for: {reflection.get('needs', 'understanding and respect')[:100]}.",
            "assumptions": "Consider: What story am I telling myself? Is there another perspective?",
            "reframe": "Before the conversation, you might say to yourself: 'I want to understand their perspective too.'",
            "avoid_saying": "1. 'You're always...' (absolute statements)\n2. 'You made me feel...' (blame language)\n3. Starting with accusations before sharing your experience.",
            "conversation_opener": f"I've been thinking about something and I'd like to talk with you when we both have time. {reflection.get('situation', 'Our last conversation')[:50]}...",
            "followup_questions": "1. 'Can you help me understand your perspective?'\n2. 'What do you need from me?'\n3. 'How can I support you?'",
            "repair_statement": "I care about our relationship and I want to find a way through this together.",
        }
    
    def _fallback_with_analysis(self, reflection: dict, analysis: dict) -> dict:
        """Generate a fallback plan enhanced with analysis context."""
        primary_emotions = analysis.get("primary_emotions", [])
        emotions_summary = ""
        if primary_emotions:
            emotion_names = [e.get("name", "") for e in primary_emotions[:2]]
            emotions_summary = f"You seem to be feeling {', '.join(emotion_names)}. "
        
        needs = analysis.get("needs", [])
        needs_summary = ""
        if needs:
            need_names = [n.get("category", "") for n in needs[:2]]
            needs_summary = f"Underneath, you may need {', '.join(need_names)}. "
        
        shame_markers = analysis.get("shame_markers", [])
        has_shame = any(m.get("shame_type") == "shame" for m in shame_markers)
        
        conflict_markers = analysis.get("conflict_markers", [])
        avoid_tips = []
        if conflict_markers:
            marker_types = [m.get("type", "") for m in conflict_markers]
            if "defensiveness" in marker_types:
                avoid_tips.append("Avoid being defensive - own your experience without counter-attacking")
            if "criticism" in marker_types:
                avoid_tips.append("Avoid 'you always' or 'you never' statements")
        
        shame_tip = ""
        if has_shame:
            shame_tip = "4. Be gentle with yourself - shame can make us defensive"
        
        avoid_text = "1. 'You're always...' (absolute statements)\n2. 'You made me feel...' (blame language)"
        if avoid_tips:
            avoid_text = "\n".join(avoid_tips[:2]) + "\n" + avoid_text
        if shame_tip:
            avoid_text += f"\n{shame_tip}"
        
        return {
            "emotional_summary": f"{emotions_summary}This is a situation many people find challenging to navigate. {reflection.get('feelings', '')}[:100]",
            "needs_summary": f"{needs_summary}Understanding what you need is an important first step.",
            "assumptions": "Consider: What story am I telling myself? Is there another perspective?",
            "reframe": "Before the conversation, you might say to yourself: 'I want to understand their perspective too.'",
            "avoid_saying": avoid_text,
            "conversation_opener": f"I've been thinking about something and I'd like to talk with you when we both have time. {reflection.get('situation', 'Our last conversation')[:50]}...",
            "followup_questions": "1. 'Can you help me understand your perspective?'\n2. 'What do you need from me?'\n3. 'How can I support you?'",
            "repair_statement": "I care about our relationship and I want to find a way through this together.",
        }

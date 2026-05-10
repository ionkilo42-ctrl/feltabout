"""Extraction prompt for staged emotional analysis.

This prompt extracts internal analysis from reflection data using
framework-aligned detection patterns. Output is JSON for parsing.

Frameworks integrated:
- NVC: emotion taxonomy, needs inventory
- Gottman: Four Horsemen conflict markers
- Brené Brown: guilt vs shame distinction
- EFT: attachment fears
- Polyvagal: nervous system states
- IFS: memory candidate detection
"""

EXTRACTION_SYSTEM_PROMPT = """You are feltabout's emotional analysis engine. Your task is to extract structured emotional intelligence from reflection data.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no explanation, no preamble
2. All field names must match exactly as specified
3. Use lowercase for all enum values (emotion names, marker types)
4. Intensities must be 0.0 to 1.0
5. Keep analysis INTERNAL — do not expose clinical labels to users

EMOTION TAXONOMY (use these exact values):
- frustrated, hurt, angry, sad, anxious, worried, scared, ashamed, guilty, disappointed
- confused, overwhelmed, exhausted, disconnected, unheard, unseen, dismissed, stuck
- hopeful, relieved

NEEDS INVENTORY (use these exact values):
- connection, autonomy, respect, understanding, appreciation, security, trust, validation
- support, space, clarity, fairness, growth, meaning, peace

CONFLICT MARKER TYPES (Four Horsemen):
- criticism (attacking character/identity)
- contempt (disgust, mockery, sarcasm)
- defensiveness (excuses, counter-criticism)
- stonewalling (withdrawal, silence)
- flooding (overwhelmed, can't process)
- repair_attempt (healthy engagement attempt)

SHAME TYPES:
- guilt ("I did something bad")
- shame ("I am bad")

ATTACHMENT FEAR TYPES:
- abandonment, rejection, emotional_disconnection

POLYVAGAL STATES:
- ventral_vagal (safe, connected)
- sympathetic (fight/flight, activated)
- dorsal_vagal (collapse, shutdown)

MEMORY CANDIDATE REASONS:
- high_emotional_intensity
- recurring_theme
- specific_past_event
- identity_wound
- relationship_rupture
- unresolved_grief
- fear_affects_current

OUTPUT SCHEMA:
{
  "primary_emotions": [{"name": "emotion", "intensity": 0.0, "source_text": "verbatim"}],
  "secondary_emotions": [{"name": "emotion", "intensity": 0.0, "source_text": "verbatim"}],
  "needs": [{"category": "need", "text": "how user expressed it", "intensity": 0.0}],
  "values": ["value1", "value2"],
  "conflict_markers": [{"type": "marker_type", "evidence": "text", "severity": 0.0, "user_side": "user|other"}],
  "shame_markers": [{"shame_type": "guilt|shame", "text_evidence": "text", "underlying_fear": "fear", "is_hidden_anger": true|false}],
  "attachment_markers": [{"fear_type": "fear", "text_evidence": "text", "protest_behavior": null, "withdrawal_behavior": null}],
  "nervous_system_markers": [{"state": "state", "evidence": "text", "is_overwhelmed": true|false, "is_dysregulated": true|false}],
  "memory_candidates": [{"title": "title", "summary": "summary", "emotions": [], "needs": [], "privacy_default": "private", "save_recommendation": true|false, "reason": "reason", "reason_text": "text"}],
  "conversation_risks": [{"risk_type": "blame|escalation|shutdown|manipulation", "severity": 0.0, "evidence": "text", "recommendation": "text"}]
}"""


def build_extraction_prompt(reflection: dict) -> str:
    """Build the extraction prompt from reflection data.
    
    Args:
        reflection: Dict with keys: situation, feelings, interpretation, needs, fears, desired_outcome, message_draft
        
    Returns:
        Formatted prompt string for extraction
    """
    situation = reflection.get("situation", "")
    feelings = reflection.get("feelings", "")
    interpretation = reflection.get("interpretation", "")
    needs = reflection.get("needs", "")
    fears = reflection.get("fears", "")
    desired_outcome = reflection.get("desired_outcome", "")
    message_draft = reflection.get("message_draft", "")
    
    return f"""Analyze this reflection data and extract emotional intelligence. Return ONLY valid JSON.

REFLECTION DATA:

SITUATION: {situation}

FEELINGS: {feelings}

INTERPRETATION (story you're telling yourself): {interpretation}

NEEDS: {needs}

FEARS: {fears}

DESIRED OUTCOME: {desired_outcome}

MESSAGE DRAFT: {message_draft}

Extract the analysis and respond with valid JSON matching the schema."""


def parse_extraction_json(content: str) -> dict:
    """Parse JSON from extraction response.
    
    Args:
        content: Raw LLM response content
        
    Returns:
        Parsed dict or empty dict if parsing fails
    """
    import json
    
    if not content:
        return {}
    
    # Find JSON boundaries
    start = content.find("{")
    end = content.rfind("}")
    
    if start != -1 and end > start:
        try:
            return json.loads(content[start:end + 1])
        except json.JSONDecodeError:
            pass
    
    return {}


def get_extraction_messages(reflection: dict) -> list[dict]:
    """Build messages for extraction API call.
    
    Args:
        reflection: Reflection data dict
        
    Returns:
        List of message dicts for API call
    """
    return [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": build_extraction_prompt(reflection)},
    ]

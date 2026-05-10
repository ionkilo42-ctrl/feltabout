"""
Safety Service — Crisis detection, abuse detection, and safety response generation.

This is the Safety Engine in feltabout's three-engine architecture.
All AI generation must pass through this service first.
"""

import re
from dataclasses import dataclass

from app.models.reflection import SafetyEvent
from app.schemas.reflection import GenerateResponse


# ─── Safety Keywords ────────────────────────────────────────────────────────────

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end it all", "want to die", "take my life",
    "self-harm", "cut myself", "overdose", "hang myself", "jump off",
    "slit my wrists", "ending it all", "don't want to exist",
]

ABUSE_KEYWORDS = [
    "hit me", "hurt me", "abuse", "threatening", "blackmail",
    "coercion", "controlling", "isolating me", "threatened", "attacked me",
    "beat me", "going to hurt them", "kill them",
]

# Manipulation keywords — requests for help controlling/manipulating others
MANIPULATION_KEYWORDS = [
    "make them regret", "get back at", "make them jealous", "force them to",
    "help me manipulate", "how to control", "track their", "spy on",
    "catch them cheating", "evidence of cheating",
]

RISK_PATTERNS = [
    r"\bweapon\b", r"\bgun\b", r"\bknife\b", r"\bgoing to hurt\b",
]

SAFETY_RESOURCES = [
    "988 Suicide & Crisis Lifeline: call or text 988",
    "National Domestic Violence Hotline: 1-800-799-7233",
    "Crisis Text Line: text HOME to 741741",
    "If you are in immediate danger, call 911.",
]


# ─── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class SafetyResult:
    """Result of safety check."""
    is_crisis: bool
    severity: str  # 'none', 'low', 'medium', 'high', 'critical'
    reason: str
    triggered_keywords: list[str]


# ─── Safety Service ────────────────────────────────────────────────────────────

class SafetyService:
    """
    Safety Engine for feltabout.
    
    Responsible for:
    - Rule-based pre-check of all user input
    - Crisis, abuse, and manipulation detection
    - Safety response generation
    - Safety event logging
    
    TODO (MVP 2): Replace placeholder with OpenAI Moderation API or similar.
    TODO (MVP 2): Add AI-based content classification.
    """

    @staticmethod
    def check(text: str) -> SafetyResult:
        """
        Perform rule-based safety check on text.
        
        Args:
            text: User input to check
            
        Returns:
            SafetyResult with is_crisis, severity, and reason
        """
        if not text:
            return SafetyResult(is_crisis=False, severity="none", reason="", triggered_keywords=[])
        
        t = text.lower()
        triggered = []
        
        # Check crisis keywords
        for kw in CRISIS_KEYWORDS:
            if kw in t:
                return SafetyResult(
                    is_crisis=True,
                    severity="critical",
                    reason=f"Crisis keyword: '{kw}'",
                    triggered_keywords=[kw]
                )
        
        # Check abuse keywords
        for kw in ABUSE_KEYWORDS:
            if kw in t:
                return SafetyResult(
                    is_crisis=True,
                    severity="high",
                    reason=f"Abuse concern: '{kw}'",
                    triggered_keywords=[kw]
                )
        
        # Check manipulation keywords
        for kw in MANIPULATION_KEYWORDS:
            if kw in t:
                return SafetyResult(
                    is_crisis=True,
                    severity="high",
                    reason=f"Manipulation keyword: '{kw}'",
                    triggered_keywords=[kw]
                )
        
        # Check risk patterns
        for pattern in RISK_PATTERNS:
            if re.search(pattern, t):
                return SafetyResult(
                    is_crisis=True,
                    severity="high",
                    reason=f"Risk pattern: '{pattern}'",
                    triggered_keywords=[pattern]
                )
        
        return SafetyResult(is_crisis=False, severity="none", reason="", triggered_keywords=[])

    @staticmethod
    async def check_with_ai(text: str, api_key: str) -> dict:
        """
        Placeholder AI moderation check.
        
        In MVP 2, this will call OpenAI Moderation API or equivalent.
        For MVP 1, we rely on rule-based check() only.
        
        TODO (MVP 2): Implement AI-based moderation.
        """
        return {"flagged": False, "categories": []}

    @staticmethod
    def build_crisis_response(severity: str) -> GenerateResponse:
        """
        Build crisis response for high-severity safety events.
        
        Args:
            severity: 'critical', 'high', 'medium'
            
        Returns:
            GenerateResponse with crisis message and resources
        """
        return GenerateResponse(
            is_crisis=True,
            severity=severity,
            message=(
                "I'm glad you shared what you're going through. What you're experiencing sounds really hard, "
                "and I want to make sure you have the right support. "
                "If you're feeling unsafe or in crisis, please reach out right now:"
            ),
            resources=SAFETY_RESOURCES,
            output=None,
        )

    @staticmethod
    async def log_safety_event(
        db,
        user_id: str,
        reflection_id: str | None,
        event_type: str,
        severity: str,
        reason: str,
    ) -> SafetyEvent:
        """
        Log a safety event to the database.
        
        Args:
            db: Database session
            user_id: User ID
            reflection_id: Optional reflection ID
            event_type: Type of safety event
            severity: Severity level
            reason: Reason for the event
            
        Returns:
            Created SafetyEvent
        """
        event = SafetyEvent(
            user_id=user_id,
            reflection_id=reflection_id,
            event_type=event_type,
            severity=severity,
            model_response=f"Safety check triggered: {reason}",
        )
        db.add(event)
        await db.commit()
        return event


# ─── Convenience Functions ─────────────────────────────────────────────────────

def check_safety(text: str) -> SafetyResult:
    """Convenience function for SafetyService.check()"""
    return SafetyService.check(text)


def build_crisis_response(severity: str) -> GenerateResponse:
    """Convenience function for SafetyService.build_crisis_response()"""
    return SafetyService.build_crisis_response(severity)
"""
RelateFX — Conflict pattern detection

Lightweight rule-based detection of escalation signals in text.
Returns a ConflictPattern or None.
"""
import re
from typing import Optional

from .types import ConflictPattern


# Accusation: blame language escalating (you/your repeated, "always", "never", "because you")
ACCUSATION_PATTERNS = [
    r"\byou\b.*\byou\b.*\byou\b",  # "you you you"
    r"\byou always\b",
    r"\byou never\b",
    r"\bbecause you\b",
    r"\byou don't\b.*\byou\b",
    r"\byou're (wrong|lying|lying|at fault)\b",
    r"\bit's all your\b",
]

# Defensiveness: "you're wrong because", "but I", "I didn't"
DEFENSIVENESS_PATTERNS = [
    r"\bI didn't\b",
    r"\bI wasn't\b",
    r"\bbut I\b",
    r"\bI was trying\b",
    r"\bI already\b",
    r"\bthat's not true\b",
    r"\bthat's wrong\b",
    r"\bI wasn't\b",
]

# Stonewalling: very short response after conflict history, or "whatever", "fine", "ok"
STONEWALL_PATTERNS = [
    r"^[\s]*(whatever|fine|ok|k|whatever|told you|don't care)[\s.!]*$",
    r"^[\s]{0,20}$",  # Very short (under ~3 words)
]

# Demand-withdrawal: one participant pressing, then the other retreating
DEMAND_WITHDRAWAL_INDICATORS = [
    # Consecutive questions back-to-back from same speaker (demanding)
    r"\?.*\?",  # Two questions in one message
    r"\bwhy don't you\b",
    r"\bwhy can't you\b",
    r"\byou should\b.*\byou should\b",
]


def detect_conflict_patterns(text: str, speaker_id: str, recent_messages: list[dict]) -> Optional[ConflictPattern]:
    """
    Analyze text and recent history for conflict patterns.
    Returns a ConflictPattern or None.
    """
    t = text.lower().strip()

    # Check accusation
    for pattern in ACCUSATION_PATTERNS:
        if re.search(pattern, t):
            return ConflictPattern.ACCUSATION

    # Check defensiveness
    for pattern in DEFENSIVENESS_PATTERNS:
        if re.search(pattern, t):
            return ConflictPattern.DEFENSIVENESS

    # Check demand-withdrawal (pressing signals in text)
    for pattern in DEMAND_WITHDRAWAL_INDICATORS:
        if re.search(pattern, t):
            return ConflictPattern.DEMAND_WITHDRAWAL

    # Check stonewalling: very short message after at least 2 prior messages (conflict history)
    if len(recent_messages) >= 2:
        for pattern in STONEWALL_PATTERNS:
            if re.search(pattern, t):
                # Confirm there was prior conflict (last 3 messages have escalating tension)
                recent_texts = " ".join(m.get("text", "").lower() for m in recent_messages[-3:])
                conflict_indicators = ["but", "because", "you", "don't", "wrong", "fine", "whatever"]
                tension_count = sum(1 for w in conflict_indicators if w in recent_texts)
                if tension_count >= 2:
                    return ConflictPattern.STONEWALLING

    return None


def get_pattern_severity(pattern: ConflictPattern) -> float:
    """Return a severity score 0.0-1.0 for a detected pattern."""
    return {
        ConflictPattern.ACCUSATION: 0.8,
        ConflictPattern.DEFENSIVENESS: 0.5,
        ConflictPattern.STONEWALLING: 0.7,
        ConflictPattern.DEMAND_WITHDRAWAL: 0.75,
    }.get(pattern, 0.0)
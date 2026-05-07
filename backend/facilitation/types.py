"""
RelateFX — Facilitation type definitions
"""
from enum import Enum
from typing import Optional


class InterventionType(str, Enum):
    REFLECT = "reflect"       # Paraphrase emotion, validate
    PAUSE = "pause"           # Slow down, invite a breath
    INVITE = "invite"         # Bring quiet person in
    EXERCISE = "exercise"     # Shift to structured format
    REBALANCE = "rebalance"   # Redirect dominant speaker
    NONE = "none"             # No intervention


class ConflictPattern(str, Enum):
    ACCUSATION = "accusation"     # Blame spiral
    DEFENSIVENESS = "defensiveness"  # "you're wrong because"
    STONEWALLING = "stonewalling"    # Minimal responses after conflict
    DEMAND_WITHDRAWAL = "demand_withdrawal"  # Press then retreat


class TurnPhase(str, Enum):
    SPEAKER_TURN = "speaker_turn"       # Speaker is sharing
    LISTENER_REFLECT = "listener_reflect"  # Listener paraphrases
    COMPLETE = "complete"              # Turn cycle done


class InterventionDecision:
    should_speak: bool
    intervention_type: InterventionType
    confidence: float  # 0.0 to 1.0
    reason: str
    conflict_pattern: Optional[ConflictPattern] = None

    def __init__(
        self,
        should_speak: bool,
        intervention_type: InterventionType,
        confidence: float = 0.0,
        reason: str = "",
        conflict_pattern: Optional[ConflictPattern] = None,
    ):
        self.should_speak = should_speak
        self.intervention_type = intervention_type
        self.confidence = confidence
        self.reason = reason
        self.conflict_pattern = conflict_pattern

    def to_dict(self) -> dict:
        return {
            "should_speak": self.should_speak,
            "intervention_type": self.intervention_type.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "conflict_pattern": self.conflict_pattern.value if self.conflict_pattern else None,
        }


class FacilitatorOutput:
    response: str
    intervention_type: InterventionType
    confidence: float

    def __init__(self, response: str, intervention_type: InterventionType, confidence: float = 1.0):
        self.response = response
        self.intervention_type = intervention_type
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "response": self.response,
            "intervention_type": self.intervention_type.value,
            "confidence": self.confidence,
        }
"""
RelateFX — Intervention Policy

Lightweight rule-based decision engine.
Only calls LLM when a rule fires and the facilitator should intervene.
"""
from typing import Optional

from .types import (
    InterventionType,
    InterventionDecision,
    ConflictPattern,
    TurnPhase,
)
from .conflict_detector import detect_conflict_patterns, get_pattern_severity


# Threshold: how many consecutive messages before facilitator speaks in facilitation mode
MESSAGE_BUDGET_NEUTRAL = 1  # Speak every N neutral messages (1 = respond on every message)
MESSAGE_BUDGET_ACTIVE = 1    # Speak more often when topics are active

# Minimum words to be considered substantive (not just "ok", "yeah", etc.)
MIN_SUBSTANTIVE_WORDS = 3


class InterventionPolicy:
    """
    Evaluates a message and decides whether/how the facilitator should intervene.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.silent_count = 0      # consecutive messages without facilitator speaking
        self.total_messages = 0     # total user messages in session
        self.last_intervention_type: Optional[InterventionType] = None

    def evaluate(
        self,
        text: str,
        mode: str,
        turn_manager: Optional["TurnManager"],  # noqa: F821
        history: list[dict],
    ) -> InterventionDecision:
        """
        Main entry point: given a message and session state, decide if facilitator should speak.

        Returns InterventionDecision with should_speak, intervention_type, confidence, reason.
        """
        # Temporary force reply every message
        should_speak = True

        if should_speak:
            self.silent_count = 0
            intervention_type = self._select_facilitation_type(history)
            self.last_intervention_type = intervention_type
            return InterventionDecision(
                should_speak=True,
                intervention_type=intervention_type,
                confidence=0.8,
                reason="FORCED: Always speak (debug mode)",
            )

        self.total_messages += 1
        recent = history[-6:] if history else []

        # Rule 1: Conflict pattern → always intervene
        conflict = detect_conflict_patterns(text, "", recent)
        if conflict:
            self.silent_count = 0
            self.last_intervention_type = self._intervention_for_conflict(conflict)
            return InterventionDecision(
                should_speak=True,
                intervention_type=self.last_intervention_type,
                confidence=get_pattern_severity(conflict),
                reason=f"Conflict pattern detected: {conflict.value}",
                conflict_pattern=conflict,
            )

        # Rule 2: Mode-specific evaluation
        if mode == "speaker-listener" and turn_manager:
            # TurnManager handles phase enforcement separately.
            # Policy evaluates whether facilitator should add process guidance.
            return self._evaluate_speaker_listener(text, turn_manager)

        # Rule 3: Facilitation mode — message budget
        budget = MESSAGE_BUDGET_NEUTRAL if self.total_messages < 5 else MESSAGE_BUDGET_ACTIVE
        if self.silent_count >= budget and self._is_substantive(text):
            # Time to speak
            self.silent_count = 0
            intervention_type = self._select_facilitation_type(history)
            self.last_intervention_type = intervention_type
            return InterventionDecision(
                should_speak=True,
                intervention_type=intervention_type,
                confidence=0.6,
                reason=f"Message budget reached ({budget})",
            )

        # Neutral message, no intervention needed
        self.silent_count += 1
        return InterventionDecision(
            should_speak=False,
            intervention_type=InterventionType.NONE,
            confidence=1.0,
            reason="Neutral message, no intervention needed",
        )

    def _evaluate_speaker_listener(
        self,
        text: str,
        turn_manager: "TurnManager",  # noqa: F821
    ) -> InterventionDecision:
        """Speaker-listener mode: facilitator stays mostly quiet, intervenes only on pattern."""
        # Let TurnManager handle turn logic; facilitator only speaks on pattern
        # For now, just track silence
        self.silent_count += 1
        if self.silent_count >= MESSAGE_BUDGET_ACTIVE:
            return InterventionDecision(
                should_speak=True,
                intervention_type=InterventionType.INVITE,
                confidence=0.5,
                reason="Speaker-listener budget reached",
            )
        return InterventionDecision(
            should_speak=False,
            intervention_type=InterventionType.NONE,
            confidence=1.0,
            reason="Speaker-listener mode: no intervention needed",
        )

    def _is_substantive(self, text: str) -> bool:
        """Check if message has enough substance to count toward budget."""
        if len(text.split()) < MIN_SUBSTANTIVE_WORDS:
            return False
        # Filter out very common non-substantive responses
        non_substantive = {"ok", "yeah", "yes", "no", "sure", "maybe", "okay", "yep", "nope"}
        words = set(text.lower().split())
        if words.issubset(non_substantive):
            return False
        return True

    def _intervention_for_conflict(self, pattern: ConflictPattern) -> InterventionType:
        """Map conflict pattern to intervention type."""
        return {
            ConflictPattern.ACCUSATION: InterventionType.PAUSE,
            ConflictPattern.DEFENSIVENESS: InterventionType.REFLECT,
            ConflictPattern.STONEWALLING: InterventionType.EXERCISE,
            ConflictPattern.DEMAND_WITHDRAWAL: InterventionType.REBALANCE,
        }.get(pattern, InterventionType.PAUSE)

    def _select_facilitation_type(self, history: list[dict]) -> InterventionType:
        """Select an intervention type based on conversation history."""
        if not history:
            return InterventionType.INVITE

        # Count message distribution — if one person dominates, rebalance
        recent = history[-8:]
        speakers = [m.get("speaker_id") for m in recent if m.get("speaker_id") != "facilitator"]
        if speakers:
            from collections import Counter
            counts = Counter(speakers)
            if counts and max(counts.values()) / len(speakers) > 0.65:
                return InterventionType.REBALANCE

        # Rotate through intervention types
        rotation = [
            InterventionType.INVITE,
            InterventionType.REFLECT,
            InterventionType.PAUSE,
            InterventionType.EXERCISE,
        ]
        if self.last_intervention_type and self.last_intervention_type in rotation:
            idx = rotation.index(self.last_intervention_type)
            return rotation[(idx + 1) % len(rotation)]

        return InterventionType.INVITE

    def reset(self) -> None:
        self.silent_count = 0
        self.total_messages = 0
        self.last_intervention_type = None
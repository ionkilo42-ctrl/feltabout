"""
RelateFX — Turn Manager for speaker-listener mode

Enforces structured turn-taking:
  SPEAKER_TURN → LISTENER_REFLECT → COMPLETE → (next speaker) SPEAKER_TURN...
"""
from typing import Optional

from .types import TurnPhase


class TurnManager:
    """Manages turn phases in speaker-listener structured format."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.phase = TurnPhase.SPEAKER_TURN
        self.current_speaker_id: Optional[str] = None
        self.current_listener_id: Optional[str] = None
        self.turn_history: list[dict] = []  # {speaker_id, listener_id, phase}
        self.speaker_queue: list[str] = []  # participant IDs waiting to speak

    def initialize(self, participants: dict[str, "Participant"]) -> None:
        """
        Set up the turn order from participants dict.
        Participants: dict of {participant_id: Participant}
        """
        pids = list(participants.keys())
        if len(pids) < 2:
            # Single participant — can't run speaker-listener
            return
        # Alternate speakers
        self.speaker_queue = pids.copy()
        # Store all participant IDs for name lookups
        self._all_participants = set(pids)
        self._participant_names = {pid: participants[pid].name for pid in pids}
        self._advance_to_next_speaker()

    def _advance_to_next_speaker(self) -> None:
        if self.speaker_queue:
            self.current_speaker_id = self.speaker_queue.pop(0)
            self.speaker_queue.append(self.current_speaker_id)  # add to back for rotation
        self.phase = TurnPhase.SPEAKER_TURN
        # The listener is whoever is NOT the speaker
        listeners = [p for p in (self._all_participants or []) if p != self.current_speaker_id]
        self.current_listener_id = listeners[0] if listeners else None

    def handle_message(self, speaker_id: str, text: str) -> dict:
        """
        Called when a message arrives during speaker-listener mode.
        Returns a dict with:
          - allowed: bool (whether the speaker can speak right now)
          - whisper: optional str (message to send only to the speaker if not allowed)
          - advance: bool (whether to advance to next phase)
          - next_phase: TurnPhase
        """
        from .conflict_detector import detect_conflict_patterns

        result = {
            "allowed": True,
            "whisper": None,
            "advance": False,
            "next_phase": self.phase,
            "is_reflect_valid": False,
        }

        if self.phase == TurnPhase.SPEAKER_TURN:
            if speaker_id != self.current_speaker_id:
                # Wrong person trying to speak
                result["allowed"] = False
                result["whisper"] = (
                    f"It's {self._get_name(self.current_speaker_id)}'s turn to share. "
                    "When they finish, you'll be asked to reflect back what you heard."
                )
                return result
            # Valid speaker — check for conflict patterns
            pattern = detect_conflict_patterns(text, speaker_id, [])
            if pattern:
                # Let it through but flag it — facilitator will handle via policy
                result["advance"] = True
                return result

            # Speaker turn ends when they say something concluding OR after ~3 messages
            if self._is_concluding(text) or self._count_current_speaker_turn() >= 3:
                self.phase = TurnPhase.LISTENER_REFLECT
                result["advance"] = True
                result["next_phase"] = TurnPhase.LISTENER_REFLECT
                result["whisper"] = None  # Don't whisper to speaker, inform listener
                return result

        elif self.phase == TurnPhase.LISTENER_REFLECT:
            if speaker_id != self.current_listener_id:
                if speaker_id == self.current_speaker_id:
                    # Speaker trying to respond to listener's reflect
                    result["allowed"] = False
                    result["whisper"] = (
                        f"Before you respond, let's make sure {self._get_name(self.current_listener_id)} "
                        "was able to reflect back what they heard. Give them a moment."
                    )
                else:
                    result["allowed"] = False
                    result["whisper"] = "Please wait for the speaker-listener exercise to complete."
                return result

            # Listener is reflecting — check if it's a valid reflection (not empty)
            if text.strip() and len(text.strip()) > 5:
                result["is_reflect_valid"] = True
                self.phase = TurnPhase.COMPLETE
                result["advance"] = True
                result["next_phase"] = TurnPhase.COMPLETE
                # Record the completed turn
                self.turn_history.append({
                    "speaker_id": self.current_speaker_id,
                    "listener_id": self.current_listener_id,
                })
                # Advance to next speaker
                self._advance_to_next_speaker()
                result["next_speaker_id"] = self.current_speaker_id
                return result

        return result

    def _is_concluding(self, text: str) -> bool:
        """Heuristic: speaker is wrapping up their turn."""
        t = text.strip().lower()
        concluding = ["anyway", "that's it", "that's all", "i'm done", "i think that's everything",
                      "does that make sense", "have I said enough", "let me finish", "to sum up", "in short"]
        return any(c in t for c in concluding) or text.count(".") >= 4

    def _count_current_speaker_turn(self) -> int:
        """Count consecutive messages from current speaker without phase change."""
        count = 0
        for entry in reversed(self.turn_history):
            if entry.get("speaker_id") == self.current_speaker_id:
                count += 1
        return count

    def _get_name(self, participant_id: Optional[str]) -> str:
        """Look up participant name, fall back to ID."""
        if participant_id and hasattr(self, '_participant_names'):
            return self._participant_names.get(participant_id, participant_id)
        return participant_id or "Unknown"

    def get_state(self) -> dict:
        return {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "current_speaker_id": self.current_speaker_id,
            "current_listener_id": self.current_listener_id,
        }

    def advance(self) -> dict:
        """Manually advance to next phase (e.g., facilitator intervention)."""
        if self.phase == TurnPhase.SPEAKER_TURN:
            self.phase = TurnPhase.LISTENER_REFLECT
        elif self.phase == TurnPhase.LISTENER_REFLECT:
            self.phase = TurnPhase.COMPLETE
            self.turn_history.append({
                "speaker_id": self.current_speaker_id,
                "listener_id": self.current_listener_id,
            })
            self._advance_to_next_speaker()
        return self.get_state()

    def reset(self) -> None:
        """Reset turn cycle."""
        self.phase = TurnPhase.SPEAKER_TURN
        self.turn_history.clear()
        if self.speaker_queue:
            self.current_speaker_id = self.speaker_queue[0]
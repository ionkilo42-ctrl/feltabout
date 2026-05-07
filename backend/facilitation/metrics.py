"""
RelateFX — Facilitator decision logging for monitoring and tuning.

One insert per user message — fire-and-forget, never blocks facilitation.
"""
import os
import uuid
import time
import asyncio
import logging

from models import FacilitatorDecision, async_session

USE_POSTGRES = os.environ.get("USE_POSTGRES", "false") == "true"
logger = logging.getLogger("relatefx.metrics")


async def log_facilitator_decision(
    session_id: str,
    utterance_id: str | None,
    should_speak: bool,
    intervention_type: str | None,
    confidence: float | None,
    trigger_reason: str,
    latency_ms: int,
    mode: str,
    turn_phase: str | None = None,
    conflict_pattern: str | None = None,
    # Voice-specific fields (Phase 7/8)
    voice_latency_ms: int | None = None,
    is_voice_utterance: bool = False,
) -> None:
    """
    Insert a facilitator_decisions row. Safe to call on every message.

    If USE_POSTGRES=false, logs to stdout instead (dev mode).
    Never raises — errors are swallowed so they never block facilitation.

    Voice-specific fields:
      voice_latency_ms: end-to-end voice latency (mic → STT → LLM → TTS → speaker).
                         Measured from the first audio frame to the last TTS audio byte.
                         null for text-only utterances.
      is_voice_utterance: True if this utterance came from a voice/STT pipeline
                          rather than a direct text WebSocket message.
    """
    if not USE_POSTGRES:
        print(
            f"[metrics] session={session_id} | should_speak={should_speak} | "
            f"type={intervention_type} | confidence={confidence} | "
            f"trigger={trigger_reason} | latency_ms={latency_ms} | "
            f"voice_latency_ms={voice_latency_ms} | is_voice={is_voice_utterance} | "
            f"mode={mode} | phase={turn_phase} | conflict={conflict_pattern}"
        )
        return

    decision = FacilitatorDecision(
        id=uuid.uuid4().hex[:16],
        session_id=session_id,
        utterance_id=utterance_id,
        should_speak=should_speak,
        intervention_type=intervention_type,
        confidence=confidence,
        trigger_reason=trigger_reason,
        latency_ms=latency_ms,
        mode=mode,
        turn_phase=turn_phase,
        conflict_pattern=conflict_pattern,
        voice_latency_ms=voice_latency_ms,
        is_voice_utterance=is_voice_utterance,
    )
    try:
        async with async_session() as db:
            db.add(decision)
            await db.commit()
    except Exception as e:
        # Never let metrics failures affect facilitation
        logger.warning(f"Failed to log facilitator decision: {e}")


class DecisionTimer:
    """Context manager to measure latency from message receipt to decision."""

    __slots__ = ("start",)

    def __init__(self) -> None:
        self.start: float = time.monotonic()

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.start) * 1000)

    def __enter__(self) -> "DecisionTimer":
        self.start = time.monotonic()
        return self

    def __exit__(self, *args) -> None:
        pass
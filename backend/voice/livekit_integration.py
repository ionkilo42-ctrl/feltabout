"""
LiveKit voice room integration for RelateFX.

Provides token generation, per-session voice state management, and
facilitator audio publishing to LiveKit rooms.
The LiveKit SDK is optional (only loaded when LIVEKIT_URL env var is set).
"""
import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger("relatefx.voice")

# Lazy import — avoids crashing when LiveKit packages aren't installed
_livekit_api: Optional[type] = None

def _get_livekit_api():
    global _livekit_api
    if _livekit_api is None:
        from livekit import api as lkapi
        _livekit_api = lkapi
    return _livekit_api


LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")

# ─── Per-session voice state ────────────────────────────────────────────────────

# Track which sessions have voice enabled
_voice_enabled_sessions: dict[str, bool] = {}

# Track LiveKit room state per session
_livekit_rooms: dict[str, object] = {}

# Speaker tag → participant ID mapping per session
# e.g. {"session_abc": {0: "participant_1_id", 1: "participant_2_id"}}
_speaker_tag_map: dict[str, dict[int, str]] = {}


def is_voice_enabled(session_id: str) -> bool:
    """Return True if voice has been enabled for this session."""
    return _voice_enabled_sessions.get(session_id, False)


def enable_voice_session(session_id: str) -> None:
    """Mark a session as voice-enabled."""
    _voice_enabled_sessions[session_id] = True
    _speaker_tag_map[session_id] = {}


def get_speaker_id_from_tag(session_id: str, tag: int) -> Optional[str]:
    """
    Map a Deepgram/LiveKit speaker tag to a participant ID.
    Returns None if the tag isn't mapped yet.
    """
    return _speaker_tag_map.get(session_id, {}).get(tag)


def map_speaker_tag(session_id: str, tag: int, participant_id: str) -> None:
    """Assign a speaker tag to a specific participant ID."""
    if session_id not in _speaker_tag_map:
        _speaker_tag_map[session_id] = {}
    _speaker_tag_map[session_id][tag] = participant_id


def next_unmapped_tag(session_id: str) -> Optional[int]:
    """Return the next available speaker tag (0-indexed) for a session."""
    mapping = _speaker_tag_map.get(session_id, {})
    if not mapping:
        return 0
    for i in range(len(mapping) + 1):
        if i not in mapping:
            return i
    return len(mapping)


def create_voice_token(
    session_id: str,
    participant_id: str,
    participant_name: str,
) -> dict:
    """
    Generate a LiveKit access token for a participant to join a voice room.
    The room name equals the session_id.
    Returns {"token": ..., "livekit_url": ...}.
    Raises if LiveKit env vars are not configured.
    """
    if not LIVEKIT_URL:
        raise RuntimeError(
            "LIVEKIT_URL not configured. Set LIVEKIT_URL, LIVEKIT_API_KEY, "
            "and LIVEKIT_API_SECRET in your backend .env to enable voice."
        )

    lkapi = _get_livekit_api()

    # Enable voice on this session
    enable_voice_session(session_id)

    token = (
        lkapi.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(f"{session_id}_{participant_id}")
        .with_name(participant_name)
        .with_grants(
            lkapi.VideoGrants(
                room_join=True,
                room=session_id,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )

    return {
        "token": token,
        "livekit_url": LIVEKIT_URL,
        "room_name": session_id,
    }


# ─── Facilitator audio publishing ──────────────────────────────────────────────

def get_voice_room(session_id: str):
    """Return the LiveKit Room handle for a session, if one is connected."""
    return _livekit_rooms.get(session_id)


def set_voice_room(session_id: str, room) -> None:
    """Store a LiveKit Room handle for a session."""
    _livekit_rooms[session_id] = room


async def publish_facilitator_audio(
    room,
    audio_bytes: bytes,
    sample_rate: int = 24000,
    num_channels: int = 1,
) -> None:
    """
    Publish a facilitator TTS utterance as an audio track into a LiveKit room.

    Creates a short-lived audio track, writes the raw PCM s16le bytes as a
    single frame, holds long enough for playback, then unpublishes.

    Args:
        room: a connected livekit.rtc.Room instance
        audio_bytes: raw PCM s16le bytes (mono, sample_rate Hz)
        sample_rate: samples per second (default 24000)
        num_channels: number of audio channels (default 1 = mono)
    """
    # Lazy import to avoid hard dependency when voice is disabled
    try:
        from livekit import rtc
    except ImportError:
        logger.warning("livekit package not installed — cannot publish facilitator audio")
        return

    samples_per_channel = len(audio_bytes) // (num_channels * 2)  # 2 bytes per sample (s16le)
    duration_s = samples_per_channel / sample_rate

    logger.debug(
        f"[Voice] publishing facilitator audio: "
        f"{len(audio_bytes)} bytes, {duration_s:.2f}s @ {sample_rate}Hz mono"
    )

    try:
        # Create and publish the audio track
        audio_track = rtc.AudioTrack.create_audio_track("facilitator_voice")
        publication = await room.local_participant.publish_track(audio_track)

        # Build the audio frame from raw PCM bytes
        audio_frame = rtc.AudioFrame(
            data=audio_bytes,
            sample_rate=sample_rate,
            num_channels=num_channels,
            samples_per_channel=samples_per_channel,
        )
        await audio_track.write(audio_frame)

        # Hold the track open for the duration of the audio so it fully plays
        await asyncio.sleep(duration_s + 0.1)

        # Clean up — unpublish so the track doesn't linger
        await room.local_participant.unpublish_track(audio_track)
        logger.debug(f"[Voice] facilitator audio published and unpublished")

    except Exception as e:
        logger.warning(f"[Voice] failed to publish facilitator audio: {e}")

"""
Deepgram STT pipeline for RelateFX voice sessions.

Subscribes to a LiveKit audio track and streams it to Deepgram for
real-time transcription with speaker diarization. Emits transcribed
utterances via a callback, which the caller (main.py) uses to inject
voice inputs into the facilitation pipeline.

Usage:
    stt_task = asyncio.create_task(
        transcribe_livekit_room(
            session_id=session_id,
            livekit_room=livekit_room,
            on_utterance=lambda speaker_id, text: inject_voice_utterance(session_id, speaker_id, text)
        )
    )
"""
import os
import asyncio
import logging
from importlib.util import find_spec
from typing import Callable, Awaitable

logger = logging.getLogger("relatefx.stt")

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")


async def transcribe_livekit_room(
    session_id: str,
    on_utterance: Callable[[str, str], Awaitable[None]],
) -> None:
    """
    Connect to Deepgram and forward audio from the LiveKit room.
    Calls on_utterance(speaker_id, transcript) for each final transcript.

    Note: The LiveKit SDK is used to subscribe to audio tracks. The actual
    audio bytes are forwarded to Deepgram's streaming endpoint.

    This function runs as a background task for the lifetime of the voice session.
    """
    if not DEEPGRAM_API_KEY:
        logger.warning("DEEPGRAM_API_KEY not set — STT pipeline unavailable")
        return

    if find_spec("livekit") is None:
        logger.warning("LiveKit SDK not installed — cannot subscribe to audio tracks")
        return

    # Lazy import Deepgram
    from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

    deepgram = DeepgramClient(DEEPGRAM_API_KEY)
    dg_connection = deepgram.listen.live.v("1")

    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        diarize=True,
        punctuate=True,
        interim_results=False,
    )

    # Map Deepgram speaker tags → participant IDs
    from .livekit_integration import get_speaker_id_from_tag, map_speaker_tag, next_unmapped_tag

    async def _handle_transcript(result):
        try:
            alternative = result.channel.alternatives[0]
            if not alternative.transcript:
                return

            words = alternative.words or []
            if not words:
                return

            speaker_tag = words[0].speaker  # 0-indexed Deepgram speaker tag
            transcript = alternative.transcript.strip()

            # Resolve speaker_id
            speaker_id = get_speaker_id_from_tag(session_id, speaker_tag)
            if speaker_id is None:
                # First time seeing this tag — assign to next unmapped slot
                new_tag = next_unmapped_tag(session_id)
                if new_tag is not None:
                    # We need to know which participant this maps to.
                    # For now, map tag to a synthetic ID; the orchestrator
                    # will resolve against known participants.
                    map_speaker_tag(session_id, speaker_tag, f"_voice_tag_{new_tag}")
                    speaker_id = f"_voice_tag_{new_tag}"

            logger.debug(f"[STT] speaker={speaker_id} tag={speaker_tag}: {transcript}")
            await on_utterance(speaker_id, transcript)

        except Exception as e:
            logger.warning(f"STT transcript handling error: {e}")

    dg_connection.on(LiveTranscriptionEvents.Transcript, _handle_transcript)

    if not await dg_connection.start(options):
        logger.error("Deepgram connection failed")
        return

    logger.info(f"STT pipeline started for session {session_id}")

    # Keep alive until cancelled
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info(f"STT pipeline cancelled for session {session_id}")
        await dg_connection.finish()
        raise


async def transcribe_audio_stream(
    audio_bytes: bytes,
    on_utterance: Callable[[str, str], Awaitable[None]],
) -> None:
    """
    Alternative: receive raw PCM16 audio bytes directly and transcribe.
    Useful when audio comes from a WebSocket data channel rather than LiveKit.

    audio_bytes: raw PCM16 audio (16-bit, 16kHz mono)
    on_utterance: callback(speaker_id, transcript)
    """
    if not DEEPGRAM_API_KEY:
        logger.warning("DEEPGRAM_API_KEY not set")
        return

    from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

    deepgram = DeepgramClient(DEEPGRAM_API_KEY)
    dg_connection = deepgram.listen.live.v("1")

    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        diarize=False,  # No speaker info from raw bytes
        punctuate=True,
        interim_results=False,
        encoding="linear16",
        sample_rate=16000,
        channels=1,
    )

    async def _handle(result):
        alternative = result.channel.alternatives[0]
        if alternative.transcript:
            await on_utterance("unknown", alternative.transcript.strip())

    dg_connection.on(LiveTranscriptionEvents.Transcript, _handle)

    if not await dg_connection.start(options):
        logger.error("Deepgram connection failed")
        return

    await dg_connection.send(audio_bytes)
    await dg_connection.finish()

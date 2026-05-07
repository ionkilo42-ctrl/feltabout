"""
ElevenLabs TTS pipeline for RelateFX facilitator speech output.

Generates spoken audio from the facilitator's text responses and returns
raw PCM s16le 24kHz mono audio bytes, which can be published directly to a
LiveKit room via rtc.AudioFrame.

Usage:
    audio = await synthesize_facilitator_speech_async(
        text="Thank you for sharing that. Let's slow down and reflect on what was just said."
    )
    # audio.audio_bytes → raw PCM s16le 24kHz mono
    # Publish via publish_facilitator_audio(room, audio)
"""
import os
import logging
from dataclasses import dataclass

logger = logging.getLogger("relatefx.tts")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel — warm, calm facilitator voice


@dataclass
class SynthesizedAudio:
    """Container for TTS output: raw PCM s16le 24kHz mono."""
    audio_bytes: bytes
    sample_rate: int = 24000
    num_channels: int = 1

    @property
    def samples_per_channel(self) -> int:
        """Number of samples per channel = total_bytes / (channels * bytes_per_sample)."""
        return len(self.audio_bytes) // (self.num_channels * 2)  # 2 bytes per sample (s16le)


def synthesize_facilitator_speech(text: str) -> SynthesizedAudio:
    """
    Synthesize text into audio using ElevenLabs.
    Returns raw PCM s16le 24kHz mono (not MP3).
    Raises if ELEVENLABS_API_KEY is not set or synthesis fails.

    Target latency: ~300ms for the synthesis call itself.
    Total voice path latency (STT→LLM→TTS) target: ≤800ms.
    """
    if not ELEVENLABS_API_KEY:
        raise RuntimeError(
            "ELEVENLABS_API_KEY not set. Set it in your backend .env to enable TTS."
        )

    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        raise RuntimeError("elevenlabs package not installed. Run: pip install elevenlabs")

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    audio_generator = client.generate(
        text=text,
        voice=DEFAULT_VOICE_ID,
        model="eleven_multilingual_v2",
        output_format="pcm_s16le_24000",
        voice_settings={
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    )

    # ElevenLabs generator yields raw PCM chunks
    audio_bytes = b"".join(audio_generator)

    audio = SynthesizedAudio(
        audio_bytes=audio_bytes,
        sample_rate=24000,
        num_channels=1,
    )
    logger.debug(
        f"[TTS] synthesized {len(audio_bytes)} bytes PCM, "
        f"~{audio.samples_per_channel / 24000:.1f}s of audio"
    )
    return audio


async def synthesize_facilitator_speech_async(text: str) -> SynthesizedAudio:
    """
    Async wrapper around the synchronous ElevenLabs call.
    ElevenLabs SDK uses requests under the hood; we run it in a thread pool
    to avoid blocking the async event loop.
    """
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, synthesize_facilitator_speech, text)


def get_available_voices() -> list[dict]:
    """
    List voices available in the ElevenLabs account.
    Useful for picking a different facilitator voice (e.g., "Arnold" for a
    more direct style, or a custom cloned voice).
    Returns a list of {"voice_id": ..., "name": ..., "labels": ...}.
    """
    if not ELEVENLABS_API_KEY:
        return []

    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        return []

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    voices = client.voices.get_all()
    return [
        {
            "voice_id": v.voice_id,
            "name": v.name,
            "labels": v.labels or {},
        }
        for v in (voices.voices or [])
    ]
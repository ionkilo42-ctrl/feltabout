"""
Voice error types and user-facing error messages for RelateFX.

All voice service failures map to one of these categories.
The frontend uses `VoiceError.code` to determine UI treatment:
  - TRANSIENT  → show warning, retry button
  - PERMANENT  → show error, fall back to text-only
  - UNAVAILABLE → graceful degradation, text-only mode
"""
from enum import Enum


class VoiceErrorCode(str, Enum):
    LIVEKIT_CONNECTION_FAILED = "livekit_connection_failed"
    LIVEKIT_TOKEN_ERROR = "livekit_token_error"
    TTS_SYNTHESIS_FAILED = "tts_synthesis_failed"
    TTS_TIMEOUT = "tts_timeout"
    STT_CONNECTION_FAILED = "stt_connection_failed"
    STT_TRANSCRIPTION_ERROR = "stt_transcription_error"
    PERMISSION_DENIED = "permission_denied"
    SESSION_NOT_FOUND = "session_not_found"
    UNKNOWN = "unknown"


class VoiceError(Exception):
    def __init__(
        self,
        code: VoiceErrorCode,
        message: str,
        session_id: str | None = None,
        is_transient: bool = True,
    ):
        super().__init__(message)
        self.code = code
        self.session_id = session_id
        # TRANSIENT = retry may succeed; PERMANENT = no point retrying
        # UNAVAILABLE = service is down globally
        self.is_transient = is_transient

    def to_dict(self) -> dict:
        return {
            "code": self.code.value,
            "message": str(self),
            "session_id": self.session_id,
            "transient": self.is_transient,
        }


# ─── Error factory helpers ──────────────────────────────────────────────────────

def livekit_connection_error(session_id: str, detail: str = "") -> VoiceError:
    return VoiceError(
        code=VoiceErrorCode.LIVEKIT_CONNECTION_FAILED,
        message=(
            "Could not connect to the voice server. "
            "You can continue in text mode. "
            + (detail if detail else "")
        ),
        session_id=session_id,
        is_transient=True,
    )


def livekit_token_error(session_id: str) -> VoiceError:
    return VoiceError(
        code=VoiceErrorCode.LIVEKIT_TOKEN_ERROR,
        message="Voice authentication failed. Please refresh and try again.",
        session_id=session_id,
        is_transient=False,
    )


def tts_synthesis_error(session_id: str, detail: str = "") -> VoiceError:
    return VoiceError(
        code=VoiceErrorCode.TTS_SYNTHESIS_FAILED,
        message=(
            "The facilitator's voice could not be generated. "
            "The text response will still appear in chat."
            + (f" ({detail})" if detail else "")
        ),
        session_id=session_id,
        is_transient=True,
    )


def tts_timeout_error(session_id: str) -> VoiceError:
    return VoiceError(
        code=VoiceErrorCode.TTS_TIMEOUT,
        message="The facilitator's voice is taking too long. The text response will appear instead.",
        session_id=session_id,
        is_transient=True,
    )


def stt_connection_error(session_id: str) -> VoiceError:
    return VoiceError(
        code=VoiceErrorCode.STT_CONNECTION_FAILED,
        message="Speech recognition is unavailable. Please type your message.",
        session_id=session_id,
        is_transient=True,
    )


def stt_transcription_error(session_id: str, detail: str = "") -> VoiceError:
    return VoiceError(
        code=VoiceErrorCode.STT_TRANSCRIPTION_ERROR,
        message=(
            "Could not transcribe your speech. Please try again or type your message."
            + (f" ({detail})" if detail else "")
        ),
        session_id=session_id,
        is_transient=True,
    )
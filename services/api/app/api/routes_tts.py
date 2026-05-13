"""
TTS API Routes — Text-to-Speech generation using OpenAI TTS

Provides high-quality voice synthesis for Aimee using the 'allay' voice.
Falls back to browser TTS if no OpenAI API key is configured.
"""

import os
import uuid
import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/tts", tags=["tts"])

class SpeakRequest(BaseModel):
    text: str
    provider: str = "auto"  # "openai" or "auto"

class SpeakResponse(BaseModel):
    audio_base64: str | None
    provider: str
    duration_ms: int | None

@router.post("/speak", response_model=SpeakResponse)
async def speak(text: str) -> SpeakResponse:
    """
    Generate speech audio for the given text.
    
    Uses OpenAI TTS with 'allay' voice if OPENAI_API_KEY is set.
    Falls back to returning null audio (client uses browser TTS).
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    
    if not api_key:
        return SpeakResponse(
            audio_base64=None,
            provider="browser",
            duration_ms=None
        )
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Use 'allay' voice - warm, female, friendly - perfect for Amy
        response = client.audio.speech.create(
            model="tts-1",
            voice="allay",
            input=text,
            response_format="mp3"
        )
        
        # Convert to base64 for transmission
        audio_bytes = response.content()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # Estimate duration (roughly 150 chars per second for allay)
        duration_ms = int(len(text) / 150 * 1000)
        
        return SpeakResponse(
            audio_base64=audio_base64,
            provider="openai",
            duration_ms=duration_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@router.get("/voices")
async def list_voices():
    """List available TTS voices"""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    
    if api_key:
        return {
            "provider": "openai",
            "voices": [
                {"id": "allay", "name": "Allay", "gender": "female", "style": "warm, friendly"},
                {"id": "echo", "name": "Echo", "gender": "male", "style": "calm"},
                {"id": "fable", "name": "Fable", "gender": "male", "style": "expressive"},
                {"id": "onyx", "name": "Onyx", "gender": "male", "style": "deep"},
                {"id": "nova", "name": "Nova", "gender": "female", "style": "bright"},
                {"id": "shimmer", "name": "Shimmer", "gender": "female", "style": "soft"},
            ]
        }
    else:
        return {
            "provider": "browser",
            "voices": "Use browser speechSynthesis API"
        }

@router.post("/stop")
async def stop_speech():
    """Signal to stop any ongoing speech (for client coordination)"""
    return {"status": "ok"}
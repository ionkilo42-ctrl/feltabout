"""
Piper TTS API Routes — High-quality free text-to-speech using Piper

Piper is a fast, local neural TTS engine. No API key needed.

Voice options for Amy:
- en_US/amy (female, warm) - ONNX model

Setup:
1. Install piper: pip install piper-tts
2. Download model: piper-download en_US/amy
3. Models stored in /data/piper/voices/

Docker: Add to Dockerfile:
RUN pip install piper-tts && \
    mkdir -p /data/piper/voices && \
    piper-download en_US/amy --output /data/piper/voices/
"""

import os
import uuid
import subprocess
import base64
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/tts", tags=["tts"])

# Piper configuration - check local models first, then Docker volume
LOCAL_MODELS_DIR = "/app/models/piper"  # Bundled models in Docker
PIPER_VOICES_DIR = os.environ.get("PIPER_VOICES_DIR", "/data/piper/voices")
DEFAULT_VOICE = "en_US-lessac-medium"

class SpeakRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE

class SpeakResponse(BaseModel):
    audio_base64: str | None
    provider: str
    voice: str
    duration_ms: int | None

def is_piper_available() -> bool:
    """Check if Piper is installed and configured"""
    try:
        result = subprocess.run(
            ["piper", "--help"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def get_available_voices() -> list[dict]:
    """Get list of available Piper voices"""
    voices = []
    voices_dir = Path(PIPER_VOICES_DIR)
    
    if voices_dir.exists():
        for voice_dir in voices_dir.iterdir():
            if voice_dir.is_dir():
                # Look for .onnx model file
                onnx_files = list(voice_dir.glob("*.onnx"))
                if onnx_files:
                    voices.append({
                        "id": str(voice_dir.name),
                        "path": str(voice_dir),
                        "model": onnx_files[0].name
                    })
    
    # If no voices downloaded, return default info
    if not voices:
        voices.append({
            "id": "en_US/amy",
            "path": f"{PIPER_VOICES_DIR}/en_US/amy",
            "model": "en_US/amy.onnx",
            "status": "not_downloaded",
            "install_hint": "Run: piper-download en_US/amy"
        })
    
    return voices

@router.post("/speak", response_model=SpeakResponse)
async def speak(request: SpeakRequest) -> SpeakResponse:
    """
    Generate speech audio using Piper TTS.
    
    Piper is a free, high-quality neural TTS system.
    No API key required.
    """
    text = request.text
    voice = request.voice
    import time
    start_time = time.time()
    
    if not is_piper_available():
        return SpeakResponse(
            audio_base64=None,
            provider="piper",
            voice=voice,
            duration_ms=None,
            error="Piper not installed"
        )
    
    # Build voice path - check local bundled models first, then Docker volume
    # Local models: /app/models/piper/en_US-lessac-medium.onnx
    # Docker volume: /data/piper/voices/{voice}/model.onnx
    local_model = f"{LOCAL_MODELS_DIR}/{voice}.onnx"
    
    # Check local bundled model first
    if Path(local_model).exists():
        model_file = local_model
    else:
        # Fall back to Docker volume path
        voice_path = f"{PIPER_VOICES_DIR}/{voice}"
        model_file = f"{voice_path}/{voice.split('/')[-1]}.onnx"
    
    # Check if model exists
    if not Path(model_file).exists():
        return SpeakResponse(
            audio_base64=None,
            provider="piper",
            voice=voice,
            duration_ms=None,
            error=f"Voice model not found: {model_file}"
        )
    
    try:
        # Create temp output file
        output_wav = f"/tmp/piper_output_{uuid.uuid4().hex[:8]}.wav"
        
        # Run Piper TTS
        result = subprocess.run(
            [
                "piper",
                "--model", model_file,
                "--output-file", output_wav
            ],
            input=text,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Piper error: {result.stderr}")
        
        # Read audio file and convert to base64
        with open(output_wav, "rb") as f:
            audio_bytes = f.read()
        
        # Clean up temp file
        os.remove(output_wav)
        
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        duration_ms = int((time.time() - start_time) * 1000)
        
        return SpeakResponse(
            audio_base64=audio_base64,
            provider="piper",
            voice=voice,
            duration_ms=duration_ms
        )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="TTS generation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@router.get("/voices")
async def list_voices():
    """List available TTS voices"""
    return {
        "provider": "piper",
        "voices": get_available_voices(),
        "default": DEFAULT_VOICE,
        "note": "Piper is free and runs locally. Download voices using: piper-download <voice-id>"
    }

@router.get("/status")
async def tts_status():
    """Check TTS service status"""
    available = is_piper_available()
    voices = get_available_voices()
    
    return {
        "provider": "piper",
        "available": available,
        "voices_installed": len([v for v in voices if "status" not in v]),
        "voices_total": len(voices),
        "default_voice": DEFAULT_VOICE
    }

@router.post("/stop")
async def stop_speech():
    """Signal to stop any ongoing speech (for client coordination)"""
    return {"status": "ok"}
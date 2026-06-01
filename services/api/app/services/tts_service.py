/**
 * Text-to-Speech Service
 * 
 * MVP implementation using OpenAI TTS API with allay (Amy-style) voice.
 * Falls back to browser TTS if no API key is configured.
 * 
 * Features:
 * - High-quality OpenAI TTS (tts-1 model)
 * - allay voice (warm, female, friendly)
 * - Graceful fallback to browser TTS
 * - Audio streamed to frontend for playback
 */

import os

# Check if OpenAI API key is available
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

def is_openai_configured() -> bool:
    """Check if OpenAI TTS is configured"""
    return bool(OPENAI_API_KEY)

async def speak_with_openai(text: str, output_path: str = "/tmp/tts_output.mp3") -> str | None:
    """
    Generate speech using OpenAI TTS API.
    
    Args:
        text: Text to speak
        output_path: Path to save audio file
        
    Returns:
        Path to audio file, or None if failed
    """
    if not OPENAI_API_KEY:
        return None
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="allay",  # Warm, female voice - good for Amy
            input=text,
            response_format="mp3"
        )
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(response.content())
            
        return output_path
    except Exception as e:
        print(f"OpenAI TTS error: {e}")
        return None

def get_voice_config() -> dict:
    """Get current voice configuration"""
    return {
        "provider": "openai" if is_openai_configured() else "browser",
        "voice": "allay" if is_openai_configured() else "default",
        "model": "tts-1" if is_openai_configured() else None
    }
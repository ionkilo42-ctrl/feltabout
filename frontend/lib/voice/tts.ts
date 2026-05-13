/**
 * Text-to-Speech Service
 * 
 * Primary: OpenAI TTS with 'allay' voice (warm, female, friendly - perfect for Amy)
 * Fallback: Browser Web Speech API
 * 
 * Usage:
 *   import { speak, stopSpeaking, isTtsSupported } from '@/lib/voice/tts'
 *   speak('Hello, this is Aimee.')
 *   stopSpeaking()
 */

export interface SpeakOptions {
  /** Speech rate: 0.1 to 10 (default: 1) */
  rate?: number
  /** Pitch: 0 to 2 (default: 1) */
  pitch?: number
  /** Volume: 0 to 1 (default: 1) */
  volume?: number
  /** BCP 47 language tag (default: 'en-US') */
  lang?: string
}

// API endpoint for server-side TTS
const TTS_API_URL = '/api/tts/speak'

/**
 * Check if TTS is supported in the current browser
 */
export function isTtsSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

/**
 * Speak the given text using server-side OpenAI TTS
 * Falls back to browser TTS if API is not available
 */
export async function speak(text: string, options?: SpeakOptions): Promise<boolean> {
  try {
    // Try OpenAI TTS via API
    const response = await fetch(TTS_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    })
    
    if (response.ok) {
      const data = await response.json()
      
      if (data.audio_base64 && data.provider === 'openai') {
        // Play OpenAI audio
        await playAudioFromBase64(data.audio_base64)
        return true
      }
    }
    
    // Fallback to browser TTS
    return speakWithBrowser(text, options)
  } catch (err) {
    console.warn('Server TTS failed, falling back to browser TTS:', err)
    return speakWithBrowser(text, options)
  }
}

/**
 * Play audio from base64 MP3 data
 */
async function playAudioFromBase64(base64: string): Promise<void> {
  return new Promise((resolve, reject) => {
    // Convert base64 to blob
    const audioData = atob(base64)
    const audioArray = new Uint8Array(audioData.length)
    for (let i = 0; i < audioData.length; i++) {
      audioArray[i] = audioData.charCodeAt(i)
    }
    const blob = new Blob([audioArray], { type: 'audio/mp3' })
    const url = URL.createObjectURL(blob)
    
    const audio = new Audio(url)
    audio.onended = () => {
      URL.revokeObjectURL(url)
      resolve()
    }
    audio.onerror = (e) => {
      URL.revokeObjectURL(url)
      reject(e)
    }
    audio.play()
  })
}

/**
 * Speak using browser's speech synthesis API (fallback)
 */
function speakWithBrowser(text: string, options?: SpeakOptions): boolean {
  if (!isTtsSupported()) {
    console.warn('TTS not supported in this browser')
    return false
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel()

  const utterance = new SpeechSynthesisUtterance(text)
  
  if (options) {
    if (options.rate !== undefined) utterance.rate = options.rate
    if (options.pitch !== undefined) utterance.pitch = options.pitch
    if (options.volume !== undefined) utterance.volume = options.volume
    if (options.lang) utterance.lang = options.lang
  }

  window.speechSynthesis.speak(utterance)
  return true
}

/**
 * Stop any ongoing speech
 */
export function stopSpeaking(): void {
  if (isTtsSupported()) {
    window.speechSynthesis.cancel()
  }
}

/**
 * Pause speech (if supported)
 */
export function pauseSpeaking(): void {
  if (isTtsSupported() && window.speechSynthesis.speaking) {
    window.speechSynthesis.pause()
  }
}

/**
 * Resume speech (if supported)
 */
export function resumeSpeaking(): void {
  if (isTtsSupported() && window.speechSynthesis.paused) {
    window.speechSynthesis.resume()
  }
}

/**
 * Check if currently speaking
 */
export function isSpeaking(): boolean {
  return isTtsSupported() && window.speechSynthesis.speaking
}

/**
 * Check if paused
 */
export function isPaused(): boolean {
  return isTtsSupported() && window.speechSynthesis.paused
}

/**
 * Get available TTS provider info
 */
export async function getTtsInfo(): Promise<{ provider: string; voices: string[] }> {
  try {
    const response = await fetch('/api/tts/voices')
    if (response.ok) {
      return await response.json()
    }
  } catch {
    // Ignore errors
  }
  
  // Fallback info
  return { provider: 'browser', voices: ['default'] }
}

// ─── Future Provider Interface ───────────────────────────────────────────────
// To add ElevenLabs:
//   import { ElevenLabsClient } from '@/lib/voice/elevenlabs'
//   const elevenlabs = new ElevenLabsClient(process.env.ELEVENLABS_API_KEY!)
//   elevenlabs.speak(text, options)
//
// To add OpenAI Realtime:
//   import { OpenAIRealtime } from '@/lib/voice/openai-realtime'
//   const realtime = new OpenAIRealtime(process.env.OPENAI_API_KEY!)
//   realtime.speak(text, options)
//
// Both would implement the same interface as above, making them swappable.
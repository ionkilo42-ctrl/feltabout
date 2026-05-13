/**
 * Text-to-Speech Service
 * 
 * Primary: Piper (free, local neural TTS)
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

// API endpoint for server-side TTS (Piper)
const TTS_API_URL = '/api/tts/speak'

/**
 * Check if TTS is supported in the current browser
 */
export function isTtsSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

/**
 * Speak the given text using server-side Piper TTS
 * Falls back to browser TTS if API is not available
 */
export async function speak(text: string, options?: SpeakOptions): Promise<boolean> {
  try {
    // Try Piper TTS via API
    const response = await fetch(TTS_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    })
    
    if (response.ok) {
      const data = await response.json()
      
      if (data.audio_base64 && data.provider === 'piper') {
        // Play Piper audio (WAV format)
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
 * Play audio from base64 WAV data
 */
async function playAudioFromBase64(base64: string): Promise<void> {
  return new Promise((resolve, reject) => {
    // Convert base64 to blob (WAV format)
    const audioData = atob(base64)
    const audioArray = new Uint8Array(audioData.length)
    for (let i = 0; i < audioData.length; i++) {
      audioArray[i] = audioData.charCodeAt(i)
    }
    const blob = new Blob([audioArray], { type: 'audio/wav' })
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

/**
 * Get TTS status (is Piper available?)
 */
export async function getTtsStatus(): Promise<{ provider: string; available: boolean }> {
  try {
    const response = await fetch('/api/tts/status')
    if (response.ok) {
      const data = await response.json()
      return { provider: data.provider, available: data.available }
    }
  } catch {
    // Ignore errors
  }
  
  return { provider: 'browser', available: false }
}
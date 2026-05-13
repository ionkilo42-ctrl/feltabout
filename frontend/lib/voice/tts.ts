/**
 * Text-to-Speech Service
 * 
 * Primary: Browser Web Speech API (instant, no server call)
 * Fallback: Piper (server-side neural TTS) - disabled for speed
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

// API endpoint for server-side TTS (Piper) - DISABLED for speed
// const TTS_API_URL = '/api/tts/speak'

/**
 * Check if TTS is supported in the current browser
 */
export function isTtsSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

/**
 * Speak the given text using browser speech synthesis (primary)
 * Piper TTS is disabled - browser TTS is faster and sufficient
 */
export async function speak(text: string, options?: SpeakOptions): Promise<boolean> {
  return speakWithBrowser(text, options)
}

/**
 * Speak using browser's speech synthesis API
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
  // Browser TTS - no server call needed
  return { provider: 'browser', voices: ['default'] }
}

/**
 * Get TTS status
 */
export async function getTtsStatus(): Promise<{ provider: string; available: boolean }> {
  return { provider: 'browser', available: isTtsSupported() }
}
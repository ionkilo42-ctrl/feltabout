/**
 * Text-to-Speech Abstraction Layer
 * 
 * MVP implementation using browser Web Speech API.
 * Swappable with ElevenLabs, OpenAI Realtime, or other providers later.
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

/**
 * Check if TTS is supported in the current browser
 */
export function isTtsSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

/**
 * Speak the given text using browser TTS
 */
export function speak(text: string, options?: SpeakOptions): boolean {
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
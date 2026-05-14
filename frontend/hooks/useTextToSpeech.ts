/**
 * useTextToSpeech Hook
 * 
 * Provides text-to-speech functionality with proper state management.
 * Wraps the tts utility functions with React hooks pattern.
 * 
 * Usage:
 *   const { isSpeaking, isSupported, speak, stopSpeaking, toggle } = useTextToSpeech()
 */

import { useState, useCallback, useEffect } from 'react'
import { 
  isTtsSupported, 
  speak as ttsSpeak, 
  stopSpeaking as ttsStop, 
  isSpeaking as ttsIsSpeaking,
  SpeakOptions 
} from '@/lib/voice/tts'

export interface UseTextToSpeechReturn {
  /** Whether browser supports TTS */
  isSupported: boolean
  /** Whether currently speaking */
  isSpeaking: boolean
  /** Speak the given text */
  speak: (text: string, options?: SpeakOptions) => Promise<boolean>
  /** Stop current speech */
  stop: () => void
  /** Toggle speaking state */
  toggle: () => void
  /** Toggle TTS enabled state */
  toggleEnabled: () => void
  /** Whether TTS is enabled (user preference) */
  isEnabled: boolean
  /** Set enabled state */
  setEnabled: (enabled: boolean) => void
}

const STORAGE_KEY = 'feltabout-tts'

export function useTextToSpeech(): UseTextToSpeechReturn {
  const [isSupported, setIsSupported] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isEnabled, setIsEnabledState] = useState(false)
  
  // Check support and load preference on mount
  useEffect(() => {
    const supported = isTtsSupported()
    setIsSupported(supported)
    
    // Load saved preference
    if (supported) {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved === 'true') {
        setIsEnabledState(true)
      }
    }
  }, [])
  
  // Poll speaking state
  useEffect(() => {
    if (!isSupported) return
    
    const interval = setInterval(() => {
      setIsSpeaking(ttsIsSpeaking())
    }, 500)
    
    return () => clearInterval(interval)
  }, [isSupported])
  
  const speak = useCallback(async (text: string, options?: SpeakOptions): Promise<boolean> => {
    if (!isSupported || !isEnabled) return false
    // ttsSpeak is sync in browser, wrap in promise for consistency
    return ttsSpeak(text, options)
  }, [isSupported, isEnabled])
  
  const stop = useCallback(() => {
    ttsStop()
    setIsSpeaking(false)
  }, [])
  
  const toggle = useCallback(() => {
    if (isSpeaking) {
      stop()
    }
  }, [isSpeaking, stop])
  
  const setEnabled = useCallback((enabled: boolean) => {
    if (!isSupported) return
    
    setIsEnabledState(enabled)
    localStorage.setItem(STORAGE_KEY, enabled ? 'true' : 'false')
    
    // Stop any current speech when disabling
    if (!enabled) {
      ttsStop()
      setIsSpeaking(false)
    }
  }, [isSupported])
  
  const toggleEnabled = useCallback(() => {
    setEnabled(!isEnabled)
  }, [isEnabled, setEnabled])
  
  return {
    isSupported,
    isSpeaking,
    speak,
    stop,
    toggle,
    toggleEnabled,
    isEnabled,
    setEnabled,
  }
}
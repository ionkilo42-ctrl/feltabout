/**
 * useSpeechToText Hook
 * 
 * Provides speech-to-text functionality with proper state management.
 * Wraps the stt utility functions with React hooks pattern.
 * 
 * Usage:
 *   const { isListening, transcript, error, startListening, stopListening } = useSpeechToText()
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { isSttSupported, startListening } from '@/lib/voice/stt'

interface UseSpeechToTextOptions {
  /** Callback when transcript is finalized */
  onTranscript?: (transcript: string) => void
  /** Callback on errors */
  onError?: (error: string) => void
}

export interface UseSpeechToTextReturn {
  /** Whether browser supports speech recognition */
  isSupported: boolean
  /** Whether currently listening */
  isListening: boolean
  /** Current transcript (interim results included) */
  transcript: string
  /** Error message if any */
  error: string | null
  /** Start listening */
  startListening: () => void
  /** Stop listening */
  stopListening: () => void
  /** Toggle listening state */
  toggle: () => void
  /** Clear transcript */
  clearTranscript: () => void
}

export function useSpeechToText(options?: UseSpeechToTextOptions): UseSpeechToTextReturn {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  
  const stopFnRef = useRef<(() => void) | null>(null)
  const transcriptRef = useRef('')
  
  // Check support on mount
  const [isSupported, setIsSupported] = useState(false)
  
  useEffect(() => {
    setIsSupported(isSttSupported())
  }, [])
  
  const handleTranscript = useCallback((text: string, isFinal: boolean) => {
    if (isFinal) {
      transcriptRef.current = (transcriptRef.current ? transcriptRef.current + ' ' : '') + text
      setTranscript(transcriptRef.current)
      options?.onTranscript?.(text)
    } else {
      // Interim results - show live preview
      setTranscript((transcriptRef.current ? transcriptRef.current + ' ' : '') + text)
    }
  }, [options])
  
  const handleError = useCallback((err: string) => {
    setError(err)
    setIsListening(false)
    stopFnRef.current = null
    options?.onError?.(err)
  }, [options])
  
  const start = useCallback(() => {
    if (!isSupported || isListening) return
    
    setError(null)
    setIsListening(true)
    
    stopFnRef.current = startListening(handleTranscript, handleError)
  }, [isSupported, isListening, handleTranscript, handleError])
  
  const stop = useCallback(() => {
    if (stopFnRef.current) {
      stopFnRef.current()
      stopFnRef.current = null
    }
    setIsListening(false)
  }, [])
  
  const toggle = useCallback(() => {
    if (isListening) {
      stop()
    } else {
      start()
    }
  }, [isListening, start, stop])
  
  const clearTranscript = useCallback(() => {
    setTranscript('')
    transcriptRef.current = ''
  }, [])
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (stopFnRef.current) {
        stopFnRef.current()
      }
    }
  }, [])
  
  return {
    isSupported,
    isListening,
    transcript,
    error,
    startListening: start,
    stopListening: stop,
    toggle,
    clearTranscript,
  }
}
/**
 * VoiceComposer Component
 * 
 * Reusable voice input component for chat interfaces.
 * Provides STT (speech-to-text) with transcript preview.
 * 
 * Usage:
 *   <VoiceComposer
 *     onTranscript={(text) => setInputText(prev => prev + ' ' + text)}
 *     disabled={isLoading}
 *   />
 */

'use client'

import { useState, useEffect } from 'react'
import { useSpeechToText } from '@/hooks/useSpeechToText'
import styles from './VoiceComposer.module.css'

interface VoiceComposerProps {
  /** Callback when transcript is finalized */
  onTranscript?: (transcript: string) => void
  /** Callback on errors */
  onError?: (error: string) => void
  /** Whether input is disabled (e.g., during loading) */
  disabled?: boolean
  /** Additional CSS class */
  className?: string
}

export default function VoiceComposer({
  onTranscript,
  onError,
  disabled = false,
  className = '',
}: VoiceComposerProps) {
  const [showMicHint, setShowMicHint] = useState(false)
  
  const { 
    isSupported, 
    isListening, 
    transcript, 
    error, 
    toggle, 
    clearTranscript 
  } = useSpeechToText({
    onTranscript: (text) => {
      onTranscript?.(text)
      clearTranscript()
    },
    onError: (err) => {
      onError?.(err)
    },
  })
  
  // Show mic hint on first visit for supported browsers
  useEffect(() => {
    if (isSupported && !localStorage.getItem('feltabout-mic-hint-seen')) {
      setShowMicHint(true)
    }
  }, [isSupported])
  
  const handleDismissHint = () => {
    setShowMicHint(false)
    localStorage.setItem('feltabout-mic-hint-seen', 'true')
  }
  
  // Handle permission denied specifically
  const permissionError = error?.includes('not-allowed') || error?.includes('permission')
  
  if (!isSupported) {
    return null
  }
  
  return (
    <div className={`${styles.voiceComposer} ${className}`}>
      <button
        className={`${styles.micBtn} ${isListening ? styles.recording : ''}`}
        onClick={toggle}
        disabled={disabled}
        aria-label={isListening ? 'Stop listening' : 'Start listening'}
        title={isListening ? 'Tap to stop listening' : 'Tap to speak'}
        type="button"
      >
        {isListening ? (
          <>
            <span className={styles.recordingIcon}>●</span>
            <span className={styles.recordingPulse} />
          </>
        ) : (
          <span className={styles.micIcon}>🎤</span>
        )}
      </button>
      
      {/* Permission denied error */}
      {permissionError && (
        <div className={styles.errorHint}>
          <span>⚠️ Mic access denied.</span>
          <button 
            className={styles.errorDismiss}
            onClick={() => onError?.('')}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}
      
      {/* General error */}
      {error && !permissionError && (
        <div className={styles.errorHint}>
          <span>Voice error: {error}</span>
          <button 
            className={styles.errorDismiss}
            onClick={() => onError?.('')}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}
      
      {/* Mic hint tooltip */}
      {showMicHint && !isListening && (
        <div className={styles.micHint} onClick={handleDismissHint}>
          <span>Tap to dictate. Review before sending.</span>
          <button 
            className={styles.hintClose} 
            onClick={(e) => { e.stopPropagation(); handleDismissHint(); }}
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      )}
    </div>
  )
}
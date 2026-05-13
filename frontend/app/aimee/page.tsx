"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import ExtractionCard, { ExtractionData } from '../../components/v2/ExtractionCard'
import {
  extractWithAimee,
  confirmAimeeExtraction,
  chatWithAimee,
  ExtractionResponse,
  ConfirmRequest,
  EMOTION_COLORS,
  PrimaryEmotion,
} from '../../lib/v2-api'
import { speak, stopSpeaking, isTtsSupported } from '../../lib/voice/tts'
import { isSttSupported, startListening, stopListening } from '../../lib/voice/stt'
import styles from './AimeePage.module.css'

// Convert API extraction to ExtractionData format
function apiToExtractionData(api: ExtractionResponse): ExtractionData {
  const feeling = api.feelings[0]
  return {
    feeling: feeling?.label || 'uncertain',
    primary_emotion: (feeling?.primary_emotion || 'sadness') as string,
    intensity: feeling?.intensity || 5,
    entity: feeling?.entities?.[0]?.name || '',
    topic: feeling?.topics?.[0]?.title || '',
    needs: feeling?.needs?.map(n => n.name) || [],
    confidence: feeling?.confidence || 0.8,
    suggestedMemoryTitle: api.suggested_memory_title,
  }
}

// Convert ExtractionData to ConfirmRequest
function extractionToConfirm(
  data: ExtractionData,
  sourceText: string
): ConfirmRequest {
  return {
    source_text: sourceText,
    memory_title: data.suggestedMemoryTitle || 'New reflection',
    memory_narrative: '',
    feelings: [{
      primary_emotion: data.primary_emotion as PrimaryEmotion,
      label: data.feeling,
      intensity: data.intensity,
      confidence: data.confidence,
      source_text: sourceText,
      entity_names: data.entity ? [data.entity] : [],
      topic_titles: data.topic ? [data.topic] : [],
      need_names: data.needs,
    }],
  }
}

export default function AimeePage() {
  const router = useRouter()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  const hasHydratedScrollRef = useRef(false)
  const currentRequestIdRef = useRef(0)
  const stopListeningRef = useRef<(() => void) | null>(null)
  
  // Chat state - initialize with empty time for SSR hydration safety
  const [messages, setMessages] = useState<Array<{
    id: number
    speaker: 'aimee' | 'user'
    text: string
    time: string
  }>>([
    {
      id: 1,
      speaker: 'aimee',
      text: "Hi, I'm Aimee. What would you like help thinking through today?",
      time: '',  // Empty for SSR, set via useEffect after mount
    },
  ])
  
  const [inputText, setInputText] = useState('')
  
  // Extraction state
  const [extraction, setExtraction] = useState<ExtractionData | null>(null)
  const [showCard, setShowCard] = useState(true)
  const [cardMinimized, setCardMinimized] = useState(false)
  
  // API state
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [safetyFlagged, setSafetyFlagged] = useState(false)
  const [safetyMessage, setSafetyMessage] = useState('')
  
  // Success state
  const [saved, setSaved] = useState(false)
  const [savedMemoryId, setSavedMemoryId] = useState<string | null>(null)
  
  // Source text for confirm
  const [sourceText, setSourceText] = useState('')
  
  // Message counter
  const [msgId, setMsgId] = useState(2)
  
  // TTS state
  const [ttsEnabled, setTtsEnabled] = useState(false)
  const [ttsSupported, setTtsSupported] = useState(false)
  
  // STT state - now toggle mode
  const [sttSupported, setSttSupported] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [showMicHint, setShowMicHint] = useState(false)
  
  // Initialize TTS state from localStorage and browser support
  useEffect(() => {
    setTtsSupported(isTtsSupported())
    setSttSupported(isSttSupported())
    const saved = localStorage.getItem('feltabout-tts')
    if (saved === 'true' && isTtsSupported()) {
      setTtsEnabled(true)
    }
    // Show mic hint on first visit
    if (isSttSupported() && !localStorage.getItem('feltabout-mic-hint-seen')) {
      setShowMicHint(true)
    }
  }, [])
  
  // Get consistent time format that won't cause hydration mismatch
  const getTimeString = useCallback(() => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }, [])
  
  // Set initial timestamp only after client mounts (SSR hydration safety)
  useEffect(() => {
    setMessages((prev) =>
      prev.map((msg) =>
        !msg.time ? { ...msg, time: getTimeString() } : msg
      )
    )
  }, [getTimeString])

  useEffect(() => {
    const behavior = hasHydratedScrollRef.current ? 'smooth' : 'auto'
    hasHydratedScrollRef.current = true

    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({
        behavior,
        block: 'end',
      })
    })
  }, [messages, loading, extraction, showCard, cardMinimized, saved])

  // Re-focus input after AI response completes
  useEffect(() => {
    if (!loading && inputRef.current) {
      const timer = setTimeout(() => {
        inputRef.current?.focus()
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [loading])
  
  const addMessage = useCallback((speaker: 'aimee' | 'user', text: string) => {
    setMessages(prev => [
      ...prev,
      {
        id: msgId,
        speaker,
        text,
        time: getTimeString(),
      },
    ])
    setMsgId(prev => prev + 1)
  }, [msgId, getTimeString])
  
  const handleSubmit = async () => {
    if (!inputText.trim() || loading || saving) return
    
    const text = inputText.trim()
    const requestId = currentRequestIdRef.current + 1
    currentRequestIdRef.current = requestId
    setInputText('')
    setSourceText(text)
    
    // Add user message
    addMessage('user', text)
    
    // Reset states
    setLoading(true)
    setError(null)
    setExtraction(null)
    setSafetyFlagged(false)
    setSafetyMessage('')
    setSaved(false)
    setSavedMemoryId(null)
    setShowCard(true)
    setCardMinimized(false)
    
    try {
      // Build conversation context from recent messages (last 8)
      const conversationContext = messages
        .slice(-8)
        .map((msg) => `${msg.speaker === 'user' ? 'User' : 'Aimee'}: ${msg.text}`)
        .join('\n')

      // 1. First: get a real conversational Aimee reply
      const chatResponse = await chatWithAimee(text, conversationContext)
      if (currentRequestIdRef.current !== requestId) return

      addMessage('aimee', chatResponse.reply)
      setLoading(false)

      // Speak AI response if TTS is enabled
      if (ttsEnabled && chatResponse.reply) {
        stopSpeaking() // Stop any current speech first
        speak(chatResponse.reply)
      }

      // Handle safety flagged from chat
      if (chatResponse.safety_status === 'flagged') {
        setSafetyFlagged(true)
        setSafetyMessage(chatResponse.reply)
        setExtraction(null)
        setShowCard(false)
      } else {
        // 2. Second: quietly try extraction so the memory card can still work
        try {
          const extractionResponse = await extractWithAimee(text)
          if (currentRequestIdRef.current !== requestId) return

          if (extractionResponse.safety_status === 'flagged') {
            setSafetyFlagged(true)
            setSafetyMessage(extractionResponse.suggested_response)
            setExtraction(null)
            setShowCard(false)
          } else if (extractionResponse.feelings.length > 0) {
            const extractionData = apiToExtractionData(extractionResponse)
            setExtraction(extractionData)
            setShowCard(true)
            setCardMinimized(true)
          } else {
            setExtraction(null)
            setShowCard(false)
          }
        } catch (extractErr) {
          if (currentRequestIdRef.current !== requestId) return
          console.warn('Extraction failed, but chat succeeded:', extractErr)
          setExtraction(null)
          setShowCard(false)
        }
      }
    } catch (err) {
      if (currentRequestIdRef.current !== requestId) return
      console.error('Aimee chat error:', err)
      setError('Aimee had trouble responding. Please try again.')
      addMessage('aimee', "I'm having trouble responding right now. Can you try again in a moment?")
    } finally {
      if (currentRequestIdRef.current === requestId) {
        setLoading(false)
      }
    }
  }
  
  const handleConfirm = (data: ExtractionData) => {
    // Edit mode - update local state
    setExtraction(data)
  }
  
  const handleEdit = (data: ExtractionData) => {
    setExtraction(data)
  }
  
  const handleSaveMemory = async () => {
    if (!extraction || !sourceText || saving) return
    
    setSaving(true)
    setError(null)
    
    try {
      const confirmPayload = extractionToConfirm(extraction, sourceText)
      const response = await confirmAimeeExtraction(confirmPayload)
      
      setSaved(true)
      setSavedMemoryId(response.memory_id)
      
      addMessage('aimee', "Saved! Your reflection has been stored privately.")
    } catch (err) {
      console.error('Save error:', err)
      setError('Failed to save. Please try again.')
      addMessage('aimee', "I had trouble saving that. Please try again in a moment.")
    } finally {
      setSaving(false)
    }
  }
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }
  
  // Toggle talk mode - click to start, click again to stop
  const handleTalkToggle = async () => {
    if (!sttSupported || loading || saving) return
    
    if (isRecording) {
      // Stop recording
      if (stopListeningRef.current) {
        stopListeningRef.current()
        stopListeningRef.current = null
      }
      setIsRecording(false)
    } else {
      // Start recording
      setIsRecording(true)
      
      // Use continuous listening
      stopListeningRef.current = startListening(
        (transcript, isFinal) => {
          if (isFinal) {
            // Add final transcript to input
            setInputText((prev) => {
              const newText = (prev ? prev + ' ' : '') + transcript
              return newText
            })
          }
        },
        (error) => {
          console.warn('Speech recognition error:', error)
          setIsRecording(false)
          stopListeningRef.current = null
        }
      )
    }
  }
  
  const dismissMicHint = () => {
    setShowMicHint(false)
    localStorage.setItem('feltabout-mic-hint-seen', 'true')
  }
  
  const handleStartNew = () => {
    setExtraction(null)
    setSaved(false)
    setSavedMemoryId(null)
    setSafetyFlagged(false)
    setSafetyMessage('')
    setShowCard(false)
    setCardMinimized(false)
    addMessage('aimee', "Ready when you are. What would you like help thinking through?")
  }
  
  return (
    <main className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <Link href="/" className={styles.backLink}>
          <span className={styles.backArrow}>←</span>
          <img src="/logo.png" alt="Feltabout" className={styles.headerLogo} />
        </Link>
        <div className={styles.titleGroup}>
          <span className={styles.guideName}>Aimee</span>
          <span className={styles.guideStatus}>Your reflection guide</span>
        </div>
        <div className={styles.headerSpacer} />
        {ttsSupported && (
          <button
            className={styles.ttsToggle}
            onClick={() => {
              if (ttsEnabled) {
                stopSpeaking() // Stop speech when turning off
                setTtsEnabled(false)
                localStorage.setItem('feltabout-tts', 'false')
              } else {
                setTtsEnabled(true)
                localStorage.setItem('feltabout-tts', 'true')
              }
            }}
            title={ttsEnabled ? 'Turn voice responses off' : 'Turn voice responses on'}
            aria-label={ttsEnabled ? 'Turn voice responses off' : 'Turn voice responses on'}
          >
            {ttsEnabled ? '🔊' : '🔇'}
          </button>
        )}
      </header>

      {/* Chat section */}
      <section className={styles.chatSection}>
        <div className={styles.messagesContainer}>
          {messages.map((msg) => (
            <div key={msg.id} className={`${styles.message} ${styles[msg.speaker]}`}>
              {msg.speaker === 'aimee' && (
                <div className={styles.msgAvatar}>
                  <span>A</span>
                </div>
              )}
              <div className={styles.msgBubble}>
                <p className={styles.msgText}>{msg.text}</p>
                <span className={styles.msgTime}>{msg.time}</span>
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {loading && (
            <div className={`${styles.message} ${styles.aimee}`}>
              <div className={styles.msgAvatar}>
                <span>A</span>
              </div>
              <div className={styles.msgBubble}>
                <p className={`${styles.msgText} ${styles.loadingDots}`}>
                  <span>.</span><span>.</span><span>.</span>
                </p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} className={styles.messagesEndAnchor} />
        </div>

        {/* Success state */}
        {saved && (
          <div className={styles.successContainer}>
            <div className={styles.successCard}>
              <div className={styles.successIcon}>✨</div>
              <h3>Memory saved</h3>
              <p>Your reflection has been stored privately.</p>
              <div className={styles.successActions}>
                <button 
                  className="btn-primary"
                  onClick={() => router.push(`/memories`)}
                >
                  View memories
                </button>
                <button 
                  className="btn-secondary"
                  onClick={handleStartNew}
                >
                  New reflection
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className={styles.errorBanner}>
            <span>⚠️</span> {error}
          </div>
        )}
      </section>

      {!saved && showCard && extraction && !safetyFlagged && !cardMinimized && (
        <div className={styles.floatingCardShell}>
          <div className={styles.floatingCardBackdrop} onClick={() => setCardMinimized(true)} />
          <div className={styles.floatingCardPanel}>
            <div className={styles.extractionContainer}>
              <ExtractionCard
                extraction={extraction}
                onConfirm={handleConfirm}
                onEdit={handleEdit}
                onAddFeeling={() => console.log('Add feeling')}
                onAddNeed={() => console.log('Add need')}
                onSkipNeed={() => console.log('Skip need')}
                onSaveMemory={handleSaveMemory}
                onClose={() => setCardMinimized(true)}
                saving={saving}
              />
            </div>
          </div>
        </div>
      )}

      {/* Input area */}
      <section className={styles.inputSection}>
        {!saved && showCard && extraction && !safetyFlagged && cardMinimized && (
          <div className={styles.composerCardZone}>
            <button
              className={styles.minimizedCardIndicator}
              onClick={() => setCardMinimized(false)}
            >
              <div
                className={styles.minimizedDot}
                style={{ background: EMOTION_COLORS[extraction.primary_emotion] }}
              />
              <span>Aimee noticed: {extraction.feeling}</span>
              <span className={styles.minimizedExpand}>Review</span>
            </button>
          </div>
        )}

        <div className={styles.inputArea}>
          <textarea
            ref={inputRef}
            className={styles.chatInput}
            placeholder="Tell Aimee what's on your mind..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={loading || saving}
          />
          {sttSupported && (
            <button
              className={`${styles.talkBtn} ${isRecording ? styles.recording : ''}`}
              onClick={handleTalkToggle}
              disabled={loading || saving}
              aria-label={isRecording ? 'Stop listening' : 'Start listening'}
              title={isRecording ? 'Tap to stop listening' : 'Tap to start listening'}
            >
              {isRecording ? '⏹️' : '🎤'}
            </button>
          )}
          {showMicHint && sttSupported && (
            <div className={styles.micHint} onClick={dismissMicHint}>
              <span>Tap the mic to dictate. Review before sending.</span>
              <button className={styles.micHintClose} onClick={(e) => { e.stopPropagation(); dismissMicHint(); }} aria-label="Dismiss">×</button>
            </div>
          )}
          <button
            className={styles.sendBtn}
            onClick={handleSubmit}
            disabled={!inputText.trim() || loading || saving}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
        <div className={styles.inputFooter}>
          <span className={styles.privacyNote}>🔒 Your feelings are private</span>
        </div>
      </section>
    </main>
  )
}
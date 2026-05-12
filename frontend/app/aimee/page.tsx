"use client"

import { useState, useEffect, useCallback } from 'react'
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
      text: "Hi, I'm Aimee. Who's starting Feltabout today?",
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
      const response = await extractWithAimee(text)
      
      if (response.safety_status === 'flagged') {
        // Safety flagged - show supportive message only
        setSafetyFlagged(true)
        setSafetyMessage(response.suggested_response)
        addMessage('aimee', response.suggested_response)
      } else if (response.feelings.length > 0) {
        // Safe - show extraction card
        const extractionData = apiToExtractionData(response)
        setExtraction(extractionData)
        addMessage('aimee', response.suggested_response)
      } else {
        // No feelings extracted
        addMessage('aimee', "Thank you for sharing. I'm not quite sure what you're feeling yet. Could you tell me more?")
      }
    } catch (err) {
      console.error('Extraction error:', err)
      setError('Something went wrong. Please try again.')
      addMessage('aimee', "I'm having trouble processing that. Let's try again.")
    } finally {
      setLoading(false)
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
  
  const handleStartNew = () => {
    setExtraction(null)
    setSaved(false)
    setSavedMemoryId(null)
    setSafetyFlagged(false)
    setSafetyMessage('')
    setShowCard(false)
    setCardMinimized(false)
    addMessage('aimee', "Ready when you are. What's on your mind?")
  }
  
  return (
    <main className="aimee-page">
      {/* Header */}
      <header className="aimee-header">
        <Link href="/" className="back-link">
          <span className="back-arrow">←</span>
          <img src="/logo.png" alt="Feltabout" className="header-logo" />
        </Link>
        <div className="header-title-group">
          <span className="guide-name">Aimee</span>
          <span className="guide-status">Your reflection guide</span>
        </div>
        <div className="header-spacer" />
      </header>

      {/* Chat section */}
      <section className="chat-section">
        <div className="messages-container">
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.speaker}`}>
              {msg.speaker === 'aimee' && (
                <div className="msg-avatar">
                  <span>A</span>
                </div>
              )}
              <div className="msg-bubble">
                <p className="msg-text">{msg.text}</p>
                <span className="msg-time">{msg.time}</span>
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {loading && (
            <div className="message aimee loading-message">
              <div className="msg-avatar">
                <span>A</span>
              </div>
              <div className="msg-bubble">
                <p className="msg-text loading-dots">
                  <span>.</span><span>.</span><span>.</span>
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Success state */}
        {saved && (
          <div className="success-container">
            <div className="success-card">
              <div className="success-icon">✨</div>
              <h3>Memory saved</h3>
              <p>Your reflection has been stored privately.</p>
              <div className="success-actions">
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

        {/* Extraction Card */}
        {!saved && showCard && extraction && !cardMinimized && !safetyFlagged && (
          <div className="extraction-container">
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
        )}

        {/* Minimized card indicator */}
        {!saved && showCard && extraction && cardMinimized && !safetyFlagged && (
          <button
            className="minimized-card-indicator"
            onClick={() => setCardMinimized(false)}
          >
            <div 
              className="minimized-dot" 
              style={{ background: EMOTION_COLORS[extraction.primary_emotion] }} 
            />
            <span>Aimee noticed: {extraction.feeling}</span>
            <span className="minimized-expand">+</span>
          </button>
        )}

        {/* Error display */}
        {error && (
          <div className="error-banner">
            <span>⚠️</span> {error}
          </div>
        )}
      </section>

      {/* Input area */}
      <section className="input-section">
        <div className="input-area">
          <textarea
            className="chat-input"
            placeholder="Tell Aimee what's on your mind..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={loading || saving}
          />
          <button
            className="send-btn"
            onClick={handleSubmit}
            disabled={!inputText.trim() || loading || saving}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
        <div className="input-footer">
          <span className="privacy-note">🔒 Your feelings are private</span>
        </div>
      </section>

      <style>{`
        .aimee-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          background: var(--bg);
        }

        /* Header */
        .aimee-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem clamp(1.5rem, 5vw, 2rem);
          border-bottom: 1px solid var(--border-subtle);
          background: var(--card);
          backdrop-filter: blur(20px);
          position: sticky;
          top: 0;
          z-index: 10;
        }

        .back-link {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          text-decoration: none;
          flex-shrink: 0;
        }

        .back-arrow {
          font-size: 1.25rem;
          color: var(--text-muted);
          font-weight: 300;
        }

        .header-logo {
          height: 26px;
          width: auto;
        }

        .header-title-group {
          display: flex;
          flex-direction: column;
          gap: 0.1rem;
          flex: 1;
          min-width: 0;
        }

        .guide-name {
          font-size: 1rem;
          font-weight: 600;
          color: var(--text);
        }

        .guide-status {
          font-size: 0.75rem;
          color: var(--text-quiet);
        }

        .header-spacer {
          width: 60px;
          flex-shrink: 0;
        }

        /* Chat */
        .chat-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding: 1.5rem clamp(1.5rem, 5vw, 2rem);
          max-width: 720px;
          margin: 0 auto;
          width: 100%;
        }

        .messages-container {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .message {
          display: flex;
          gap: 0.75rem;
          max-width: 85%;
          animation: messageIn 0.3s var(--ease-soft);
        }

        @keyframes messageIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
          align-self: flex-end;
          flex-direction: row-reverse;
        }

        .message.aimee {
          align-self: flex-start;
        }

        .msg-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: var(--gradient-core);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.875rem;
          font-weight: 600;
          flex-shrink: 0;
        }

        .msg-bubble {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .msg-text {
          padding: 1rem 1.25rem;
          border-radius: 20px;
          font-size: 0.95rem;
          line-height: 1.55;
          color: var(--text-soft);
          background: var(--card-solid);
          border: 1px solid var(--border-subtle);
          margin: 0;
        }

        .message.user .msg-text {
          background: var(--accent-soft);
          border-color: var(--accent-border);
          color: var(--text);
        }

        .message.aimee .msg-text {
          border-top-left-radius: 6px;
        }

        .message.user .msg-text {
          border-top-right-radius: 6px;
        }

        .msg-time {
          font-size: 0.7rem;
          color: var(--text-quiet);
          padding: 0 0.5rem;
        }

        .message.user .msg-time {
          text-align: right;
        }

        /* Loading dots animation */
        .loading-dots span {
          animation: blink 1.4s infinite both;
        }
        .loading-dots span:nth-child(2) {
          animation-delay: 0.2s;
        }
        .loading-dots span:nth-child(3) {
          animation-delay: 0.4s;
        }
        @keyframes blink {
          0%, 80%, 100% { opacity: 0; }
          40% { opacity: 1; }
        }

        /* Error banner */
        .error-banner {
          padding: 0.75rem 1rem;
          background: rgba(255, 107, 107, 0.1);
          border: 1px solid rgba(255, 107, 107, 0.3);
          border-radius: 12px;
          color: #FF6B6B;
          font-size: 0.875rem;
          text-align: center;
        }

        /* Success container */
        .success-container {
          animation: cardAppear 0.4s var(--ease-spring);
        }

        @keyframes cardAppear {
          from { opacity: 0; transform: translateY(20px) scale(0.98); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .success-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 24px;
          padding: 2rem;
          text-align: center;
        }

        .success-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }

        .success-card h3 {
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text);
          margin: 0 0 0.5rem;
        }

        .success-card p {
          font-size: 0.9rem;
          color: var(--text-muted);
          margin: 0 0 1.5rem;
        }

        .success-actions {
          display: flex;
          gap: 0.75rem;
          justify-content: center;
        }

        .btn-primary {
          padding: 0.75rem 1.5rem;
          background: var(--gradient-core);
          color: white;
          border: none;
          border-radius: 999px;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          text-decoration: none;
        }

        .btn-secondary {
          padding: 0.75rem 1.5rem;
          background: var(--card-solid);
          color: var(--text-soft);
          border: 1px solid var(--border);
          border-radius: 999px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
        }

        /* Extraction container */
        .extraction-container {
          animation: cardAppear 0.4s var(--ease-spring);
        }

        /* Minimized card */
        .minimized-card-indicator {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.875rem 1.25rem;
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 16px;
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-soft);
          width: 100%;
          max-width: 400px;
          margin: 0 auto;
        }

        .minimized-card-indicator:hover {
          background: var(--card-solid);
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
        }

        .minimized-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .minimized-card-indicator span:nth-child(2) {
          flex: 1;
          font-size: 0.9rem;
          font-weight: 500;
          color: var(--text);
          text-transform: capitalize;
        }

        .minimized-expand {
          font-size: 1.25rem;
          color: var(--text-muted);
          font-weight: 300;
        }

        /* Input */
        .input-section {
          padding: 1rem clamp(1.5rem, 5vw, 2rem);
          border-top: 1px solid var(--border-subtle);
          background: var(--card);
          backdrop-filter: blur(20px);
        }

        .input-area {
          display: flex;
          gap: 0.75rem;
          align-items: flex-end;
          max-width: 720px;
          margin: 0 auto;
        }

        .chat-input {
          flex: 1;
          min-height: 48px;
          max-height: 120px;
          padding: 0.875rem 1.25rem;
          border: 1px solid var(--border);
          border-radius: 20px;
          background: var(--card-solid);
          font-size: 0.95rem;
          color: var(--text);
          resize: none;
          outline: none;
          line-height: 1.5;
          transition: border-color var(--duration-fast) var(--ease-soft);
        }

        .chat-input:focus {
          border-color: var(--accent);
          box-shadow: 0 0 0 3px var(--accent-soft);
        }

        .chat-input::placeholder {
          color: var(--text-quiet);
        }

        .send-btn {
          min-height: 48px;
          padding: 0 1.5rem;
          border: none;
          border-radius: 999px;
          background: var(--gradient-core);
          color: white;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          box-shadow: 0 2px 12px rgba(51, 214, 200, 0.2);
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .send-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(51, 214, 200, 0.35);
        }

        .send-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .input-footer {
          max-width: 720px;
          margin: 0.75rem auto 0;
          text-align: center;
        }

        .privacy-note {
          font-size: 0.75rem;
          color: var(--text-quiet);
        }

        /* Responsive */
        @media (max-width: 640px) {
          .message {
            max-width: 92%;
          }

          .msg-avatar {
            width: 32px;
            height: 32px;
            font-size: 0.8rem;
          }
          
          .success-actions {
            flex-direction: column;
          }
        }
      `}</style>
    </main>
  )
}
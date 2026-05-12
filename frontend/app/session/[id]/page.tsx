'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useParticipantStore } from '@/store/sessionStore'

interface Message {
  id: string
  conversation_space_id: string
  participant_id: string | null
  sender_name: string
  is_aimee: boolean
  content: string
  created_at: string
}

interface Participant {
  id: string
  display_name: string
  is_owner: boolean
  is_aimee: boolean
}

export default function SharedSessionPage() {
  const params = useParams()
  const router = useRouter()
  const spaceId = params.id as string

  const participant = useParticipantStore((s) => s.participant)
  const setParticipant = useParticipantStore((s) => s.setParticipant)

  const [messages, setMessages] = useState<Message[]>([])
  const [participants, setParticipants] = useState<Participant[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inviteToken, setInviteToken] = useState<string | null>(null)
  const [showCopied, setShowCopied] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  const currentParticipant = participant
  const displayName = currentParticipant?.displayName || 'Guest'

  // Fetch participants and initial messages
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [msgsRes, partsRes] = await Promise.all([
          fetch(apiUrl(`/conversation-spaces/${spaceId}/messages`)),
          fetch(apiUrl(`/conversation-spaces/${spaceId}/participants`)),
        ])

        if (!msgsRes.ok || !partsRes.ok) {
          throw new Error('Failed to load session')
        }

        const msgsData = await msgsRes.json()
        const partsData = await partsRes.json()

        setMessages(msgsData.messages || [])
        setParticipants(partsData.participants || [])
        
        // Get invite token from localStorage
        const storedToken = localStorage.getItem('invite_token')
        if (storedToken) {
          setInviteToken(storedToken)
        }
        
        setIsLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session')
        setIsLoading(false)
      }
    }

    fetchInitialData()
  }, [spaceId])

  // Start polling for new messages
  useEffect(() => {
    const pollMessages = async () => {
      try {
        const res = await fetch(apiUrl(`/conversation-spaces/${spaceId}/messages`))
        if (res.ok) {
          const data = await res.json()
          setMessages(data.messages || [])
        }
      } catch {
        // Silently fail polling
      }
    }

    // Poll every 3 seconds
    pollingRef.current = setInterval(pollMessages, 3000)

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [spaceId])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || isTyping) return

    setIsTyping(true)
    const messageContent = newMessage.trim()
    setNewMessage('')

    try {
      const res = await fetch(apiUrl(`/conversation-spaces/${spaceId}/messages`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          content: messageContent,
          sender_name: displayName,
        }),
      })

      if (!res.ok) {
        throw new Error('Failed to send message')
      }

      // Refresh messages after sending
      const msgsRes = await fetch(apiUrl(`/conversation-spaces/${spaceId}/messages`))
      if (msgsRes.ok) {
        const msgsData = await msgsRes.json()
        setMessages(msgsData.messages || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setIsTyping(false)
    }
  }

  const copyInviteLink = async () => {
    if (!inviteToken) return
    
    const inviteUrl = `${window.location.origin}/join/${inviteToken}`
    try {
      await navigator.clipboard.writeText(inviteUrl)
      setShowCopied(true)
      setTimeout(() => setShowCopied(false), 2000)
    } catch {
      // Fallback: select the text
      prompt('Copy this link to share:', inviteUrl)
    }
  }

  if (isLoading) {
    return (
      <main className="session-page">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading session...</p>
        </div>
        <style>{styles}</style>
      </main>
    )
  }

  if (error) {
    return (
      <main className="session-page">
        <div className="error-state">
          <h2>Session unavailable</h2>
          <p>{error}</p>
          <Link href="/" className="btn-secondary">
            Go home
          </Link>
        </div>
        <style>{styles}</style>
      </main>
    )
  }

  return (
    <main className="session-page">
      {/* Header */}
      <header className="session-header">
        <Link href="/" className="brand-lockup">
          <img className="brand-mark" src="/logo.png" alt="Feltabout" />
        </Link>
        <div className="session-title">
          <span className="live-dot"></span>
          Shared Session
        </div>
        {inviteToken && (
          <button className="share-btn" onClick={copyInviteLink}>
            {showCopied ? '✓ Copied!' : 'Share'}
          </button>
        )}
      </header>

      {/* Participants bar */}
      <div className="participants-bar">
        {participants.map((p) => (
          <div
            key={p.id}
            className={`participant-badge ${p.is_aimee ? 'aimee' : ''}`}
          >
            <span className="participant-avatar">
              {p.is_aimee ? '✨' : p.display_name.charAt(0).toUpperCase()}
            </span>
            <span className="participant-name">
              {p.display_name}
              {p.is_owner && ' (host)'}
            </span>
          </div>
        ))}
      </div>

      {/* Messages */}
      <div className="messages-container">
        <div className="messages-list">
          {messages.length === 0 ? (
            <div className="empty-state">
              <p>No messages yet. Start the conversation!</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`message ${msg.is_aimee ? 'aimee' : ''} ${msg.sender_name === displayName ? 'own' : ''}`}
              >
                <div className="message-header">
                  <span className="message-sender">
                    {msg.is_aimee ? '✨ Aimee' : msg.sender_name}
                  </span>
                  <span className="message-time">
                    {new Date(msg.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <div className="message-content">{msg.content}</div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Message input */}
      <form className="message-input-form" onSubmit={sendMessage}>
        <input
          type="text"
          placeholder="Type a message..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          disabled={isTyping}
        />
        <button type="submit" disabled={!newMessage.trim() || isTyping}>
          {isTyping ? '...' : 'Send'}
        </button>
      </form>

      <style>{styles}</style>
    </main>
  )
}

const styles = `
.session-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--page-bg, #FAF9F7);
}

.loading, .error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.error-state h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text, #111827);
  margin: 0;
}

.error-state p {
  color: var(--text-muted, #6b7280);
  margin: 0;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border, #e5e7eb);
  border-top-color: var(--accent, #e07a5f);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Header */
.session-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border, #e5e7eb);
  background: white;
}

.brand-lockup {
  display: inline-flex;
}

.brand-mark {
  height: 24px;
  width: auto;
}

.session-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text, #111827);
}

.live-dot {
  width: 8px;
  height: 8px;
  background: #22c55e;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.share-btn {
  padding: 0.5rem 1rem;
  background: var(--gradient-core, linear-gradient(135deg, #33d6c8, #e07a5f));
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: transform 0.15s;
}

.share-btn:hover {
  transform: scale(1.05);
}

/* Participants bar */
.participants-bar {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--border, #e5e7eb);
  background: var(--card, #fafafa);
  overflow-x: auto;
}

.participant-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem;
  background: white;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 999px;
  font-size: 0.85rem;
  white-space: nowrap;
}

.participant-badge.aimee {
  background: linear-gradient(135deg, #33d6c8, #e07a5f);
  border-color: transparent;
  color: white;
}

.participant-avatar {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--hover-bg, #f3f4f6);
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
}

.aimee .participant-avatar {
  background: rgba(255, 255, 255, 0.3);
}

.participant-name {
  font-weight: 500;
}

/* Messages */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.messages-list {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted, #6b7280);
}

.empty-state p {
  margin: 0;
}

.message {
  max-width: 80%;
  padding: 1rem;
  background: white;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 16px;
  border-bottom-left-radius: 4px;
}

.message.own {
  align-self: flex-end;
  background: var(--gradient-core);
  color: white;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 4px;
}

.message.aimee {
  background: linear-gradient(135deg, rgba(51, 214, 200, 0.1), rgba(224, 122, 95, 0.1));
  border-color: rgba(51, 214, 200, 0.3);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.message-sender {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary, #374151);
}

.message.aimee .message-sender {
  color: var(--accent, #e07a5f);
}

.message.own .message-sender {
  color: rgba(255, 255, 255, 0.8);
}

.message-time {
  font-size: 0.7rem;
  color: var(--text-quiet, #9ca3af);
}

.message.own .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.message-content {
  font-size: 0.95rem;
  line-height: 1.55;
  white-space: pre-wrap;
}

/* Message input */
.message-input-form {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border, #e5e7eb);
  background: white;
}

.message-input-form input {
  flex: 1;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 12px;
  font-size: 0.95rem;
  background: var(--card, #fafafa);
}

.message-input-form input:focus {
  outline: none;
  border-color: var(--accent, #e07a5f);
}

.message-input-form button {
  padding: 0.875rem 1.5rem;
  background: var(--gradient-core, linear-gradient(135deg, #33d6c8, #e07a5f));
  border: none;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  white-space: nowrap;
}

.message-input-form button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.25rem;
  background: white;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-secondary, #374151);
  text-decoration: none;
  cursor: pointer;
}
`
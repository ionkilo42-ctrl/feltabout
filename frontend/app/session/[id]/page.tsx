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

// Aimee's welcome message
const AIME_WELCOME = "I'm here with both of you. Start with what you want the other person to understand, and I'll help keep this clear and respectful."

export default function SharedSessionPage() {
  const params = useParams()
  const router = useRouter()
  const spaceId = params.id as string

  const participant = useParticipantStore((s) => s.participant)

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
  const isOwner = currentParticipant?.isOwner || false

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
        
        // Get invite token from localStorage (with safety check)
        const storedToken = localStorage.getItem('invite_token')
        if (storedToken && storedToken !== 'undefined' && storedToken.length > 0) {
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
      prompt('Copy this link to share:', inviteUrl)
    }
  }

  // Show Aimee's welcome if no messages exist
  const showWelcome = messages.length === 0 && !isLoading

  if (isLoading) {
    return (
      <main className="shared-session-page">
        <div className="shared-session-shell">
          <div className="session-loading">
            <div className="debrief-loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="shared-session-page">
        <div className="shared-session-shell">
          <div className="session-error card">
            <h2>Session unavailable</h2>
            <p>{error}</p>
            <Link href="/" className="btn-secondary">Go home</Link>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="shared-session-page">
      <div className="shared-session-shell">
        {/* Header */}
        <header className="shared-session-header card">
          <div className="header-left">
            <Link href="/" className="brand-lockup">
              <img className="brand-mark-sm" src="/logo.png" alt="Feltabout" />
            </Link>
            <div className="header-titles">
              <h1 className="session-title">Shared session</h1>
              <p className="session-subtitle">Aimee is here to help both people understand each other.</p>
            </div>
          </div>
          {inviteToken && (
            <button className="btn-secondary small" onClick={copyInviteLink}>
              {showCopied ? '✓ Copied!' : 'Share invite'}
            </button>
          )}
        </header>

        {/* Participant chips */}
        <div className="session-participants">
          {participants.map((p) => (
            <div
              key={p.id}
              className={`participant-chip ${p.is_aimee ? 'aimee' : ''} ${p.display_name === displayName ? 'you' : ''}`}
            >
              <span className="chip-avatar">
                {p.is_aimee ? '✨' : p.display_name.charAt(0).toUpperCase()}
              </span>
              <span className="chip-name">
                {p.display_name}
                {p.is_owner && ' (host)'}
                {p.is_aimee && ' (facilitator)'}
              </span>
            </div>
          ))}
        </div>

        {/* Conversation card */}
        <section className="shared-room card-elevated">
          {/* Messages */}
          <div className="messages shared-messages">
            {showWelcome && (
              <div className="message facilitator">
                <div className="msg-text">{AIME_WELCOME}</div>
              </div>
            )}
            {messages.map((msg) => {
              const isOwn = msg.sender_name === displayName
              const isAimee = msg.is_aimee
              
              return (
                <div
                  key={msg.id}
                  className={`message ${isAimee ? 'facilitator' : isOwn ? 'speaker-b' : 'speaker-a'}`}
                >
                  <span className="msg-speaker">
                    {isAimee ? '✨ Aimee' : msg.sender_name}
                    {isOwn && ' (you)'}
                  </span>
                  <div className="msg-text">{msg.content}</div>
                  <span className="msg-time">
                    {new Date(msg.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <form className="input-area shared-input" onSubmit={sendMessage}>
            <input
              type="text"
              placeholder="Say what you want them to understand…"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              disabled={isTyping}
            />
            <button type="submit" className="send-btn" disabled={!newMessage.trim() || isTyping}>
              {isTyping ? '...' : 'Send'}
            </button>
          </form>
        </section>
      </div>
    </main>
  )
}
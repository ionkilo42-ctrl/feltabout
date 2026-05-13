'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useParticipantStore } from '@/store/sessionStore'
import styles from './SharedSessionRoom.module.css'

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

const AIME_WELCOME_BOTH = "I'm here with both of you. Start with what you want the other person to understand, and I'll help keep this clear and respectful."
const AIME_WELCOME_ONE = "I'm here with you. Share the invite when you're ready, or start by saying what you want the other person to understand."
const SCROLL_BOTTOM_THRESHOLD = 120

export default function SharedSessionRoom() {
  const params = useParams()
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
  const [showScrollToBottom, setShowScrollToBottom] = useState(false)

  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const userScrolledUpRef = useRef(false)
  const lastMessageIdRef = useRef<string | null>(null)

  const currentParticipant = participant
  const displayName = currentParticipant?.displayName || 'Guest'
  const isOwner = currentParticipant?.isOwner || false

  // Compute participant-based messages
  const humanParticipants = participants.filter(p => !p.is_aimee)
  const hasOtherPerson = humanParticipants.length >= 2
  const aimeeWelcome = hasOtherPerson ? AIME_WELCOME_BOTH : AIME_WELCOME_ONE
  const sessionSubtitle = hasOtherPerson
    ? 'Aimee is here to help both people understand each other.'
    : 'Invite the other person, or start preparing what you want them to understand.'

  const scrollMessagesToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    const container = messagesContainerRef.current
    if (!container) return

    requestAnimationFrame(() => {
      container.scrollTo({
        top: container.scrollHeight,
        behavior,
      })
    })
  }, [])

  const handleScroll = () => {
    const container = messagesContainerRef.current
    if (!container) return

    const { scrollTop, scrollHeight, clientHeight } = container
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight
    const isAwayFromBottom = distanceFromBottom > SCROLL_BOTTOM_THRESHOLD

    userScrolledUpRef.current = isAwayFromBottom
    setShowScrollToBottom(isAwayFromBottom)
  }

  const scrollToBottom = () => {
    userScrolledUpRef.current = false
    setShowScrollToBottom(false)
    scrollMessagesToBottom('smooth')
  }

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
        const initialMessages = msgsData.messages || []

        lastMessageIdRef.current = initialMessages.at(-1)?.id || null
        setMessages(initialMessages)
        setParticipants(partsData.participants || [])

        const storedToken = localStorage.getItem('invite_token')
        if (storedToken && storedToken !== 'undefined' && storedToken.length > 0) {
          setInviteToken(storedToken)
        }

        setIsLoading(false)
        scrollMessagesToBottom('auto')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session')
        setIsLoading(false)
      }
    }

    fetchInitialData()
  }, [spaceId, scrollMessagesToBottom])

  // Start polling for new messages
  useEffect(() => {
    const pollMessages = async () => {
      try {
        const res = await fetch(apiUrl(`/conversation-spaces/${spaceId}/messages`))
        if (res.ok) {
          const data = await res.json()
          const nextMessages = data.messages || []

          setMessages(prev => {
            const prevLastId = prev.at(-1)?.id || null
            const nextLastId = nextMessages.at(-1)?.id || null

            if (prev.length === nextMessages.length && prevLastId === nextLastId) {
              return prev
            }

            if (userScrolledUpRef.current && nextLastId !== prevLastId) {
              setShowScrollToBottom(true)
            }

            return nextMessages
          })
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

  // Auto-scroll only when a genuinely new last message arrives
  useEffect(() => {
    const newestMessageId = messages.at(-1)?.id || null
    if (!newestMessageId || newestMessageId === lastMessageIdRef.current) return

    lastMessageIdRef.current = newestMessageId

    if (userScrolledUpRef.current) {
      setShowScrollToBottom(true)
      return
    }

    setShowScrollToBottom(false)
    scrollMessagesToBottom('smooth')
  }, [messages, scrollMessagesToBottom])

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

      const data = await res.json()
      const newMessages = data.messages || []
      setMessages(prev => {
        const existingIds = new Set(prev.map((m: Message) => m.id))
        const uniqueNewMessages = newMessages.filter((m: Message) => !existingIds.has(m.id))
        return [...prev, ...uniqueNewMessages]
      })

      userScrolledUpRef.current = false
      setShowScrollToBottom(false)
      scrollMessagesToBottom('smooth')
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (newMessage.trim()) {
        sendMessage(e as unknown as React.FormEvent)
      }
    }
  }

  const showWelcome = messages.length === 0 && !isLoading

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingSpinner}>
          <span></span>
          <span></span>
          <span></span>
        </div>
        <p className={styles.loadingText}>Loading session...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <span className={styles.errorIcon}>⚠️</span>
        <h2 className={styles.errorTitle}>Session unavailable</h2>
        <p className={styles.errorMessage}>{error}</p>
        <Link href="/" className={styles.errorButton}>Go home</Link>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarInner}>
          <Link href="/" className={styles.logoLink}>
            <img className={styles.logo} src="/logo.png" alt="Feltabout" />
          </Link>
          
          <nav className={styles.sidebarNav}>
            <Link href={`/session/${spaceId}`} className={`${styles.navItem} ${styles.active}`}>
              <span className={styles.navIcon}>💬</span>
              <span className={styles.navLabel}>Shared session</span>
            </Link>
            <Link href="/" className={styles.navItem}>
              <span className={styles.navIcon}>🏠</span>
              <span className={styles.navLabel}>Home</span>
            </Link>
            <Link href="/library" className={styles.navItem}>
              <span className={styles.navIcon}>📚</span>
              <span className={styles.navLabel}>Library</span>
            </Link>
          </nav>

          <div className={styles.sidebarFooter}>
            <p className={styles.footerNote}>🔒 Your reflections stay private.</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={styles.main}>
        {/* Page Header */}
        <header className={styles.pageHeader}>
          <div className={styles.headerLeft}>
            <div className={styles.headerTitles}>
              <h1 className={styles.headerTitle}>Shared session</h1>
              <p className={styles.headerSubtitle}>{sessionSubtitle}</p>
            </div>
          </div>
          {inviteToken && (
            <button className={styles.shareButton} onClick={copyInviteLink}>
              {showCopied ? '✓ Copied!' : 'Share invite'}
            </button>
          )}
        </header>

        {/* Participants Strip */}
        <div className={styles.participantsStrip}>
          {participants.map((p) => (
            <div
              key={p.id}
              className={`${styles.participantChip} ${p.is_aimee ? styles.aimee : ''} ${p.display_name === displayName ? styles.you : ''}`}
            >
              <span className={styles.chipAvatar}>
                {p.is_aimee ? '✨' : p.display_name.charAt(0).toUpperCase()}
              </span>
              <span className={styles.chipName}>
                {p.display_name}
                {p.is_owner && ' (host)'}
              </span>
            </div>
          ))}
        </div>

        {/* Conversation Room */}
        <div className={styles.conversationRoom}>
          {/* Ambient glow decoration */}
          <div className={styles.ambientGlow} />
          
          {/* Messages */}
          <div
            ref={messagesContainerRef}
            className={styles.messagesContainer}
            onScroll={handleScroll}
          >
            {showWelcome && (
              <div className={`${styles.message} ${styles.facilitator}`}>
                <div className={styles.msgBubble}>{aimeeWelcome}</div>
              </div>
            )}
            {messages.map((msg) => {
              const isOwn = msg.sender_name === displayName
              const isAimee = msg.is_aimee

              return (
                <div
                  key={msg.id}
                  className={`${styles.message} ${isAimee ? styles.facilitator : isOwn ? styles.speakerB : styles.speakerA}`}
                >
                  <span className={styles.msgSpeaker}>
                    {isAimee ? '✨ Aimee' : msg.sender_name}
                    {isOwn && ' (you)'}
                  </span>
                  <div className={styles.msgBubble}>{msg.content}</div>
                  <span className={styles.msgTime}>
                    {new Date(msg.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Scroll to bottom button */}
          {showScrollToBottom && (
            <button className={styles.scrollToBottomBtn} onClick={scrollToBottom}>
              ↓ New messages
            </button>
          )}

          {/* Composer */}
          <div className={styles.composerArea}>
            {/* Safe space note */}
            <p className={styles.safeSpaceNote}>
              🔒 This is a safe, private space. Only invited people can see this.
            </p>
            
            {/* Input row */}
            <div className={styles.inputRow}>
              <button className={styles.helperBtn} title="Sparkle helper">
                ✨
              </button>
              <textarea
                className={styles.messageInput}
                placeholder="Say what you want them to understand…"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={isTyping}
              />
              <button 
                className={styles.sendBtn} 
                onClick={(e) => sendMessage(e as unknown as React.FormEvent)}
                disabled={!newMessage.trim() || isTyping}
              >
                {isTyping ? '...' : '→'}
              </button>
            </div>
            <p className={styles.inputHint}>
              Press Enter to send • Shift + Enter for new line
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useSessionStore } from '@/store/sessionStore'
import { useAuthStore } from '@/store/sessionStore'
import { apiUrl, wsUrl } from '@/lib/api'
import Link from 'next/link'

// ─── MVP 1 Configuration ─────────────────────────────────────────────────────

/**
 * Live guided sessions are an MVP 2 feature.
 * Set to true once the WebSocket session backend is implemented.
 */
const LIVE_SESSIONS_ENABLED = false;

// ─── Types ────────────────────────────────────────────────────────────────────

interface Participant {
  id: string
  name: string
  role: string
  emotion: string
}

interface Utterance {
  id: string
  speaker_id: string
  speaker_name: string
  text: string
  timestamp: string
  client_id?: string
}

interface SafetyFlag {
  level: string
  reason: string
  triggered_by: string
}

interface Message {
  id: string
  speaker: string
  text: string
  isFacilitator?: boolean
  timestamp: string
  safetyFlag?: SafetyFlag
  clientId?: string
  pending?: boolean
  deliveryError?: boolean
}

// ─── Session Setup View ───────────────────────────────────────────────────────

function SessionSetupView({ onCreateSpace }: { onCreateSpace: (name: string) => void }) {
  const [conversationName, setConversationName] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const handleCreate = () => {
    if (isCreating) return
    setIsCreating(true)
    onCreateSpace(conversationName.trim())
  }

  return (
    <main className="app">
      <header className="app-header">
        <div className="brand-lockup">
          <Link href="/">
            <img className="brand-mark" src="/logo.png" alt="Feltabout" />
          </Link>
        </div>
      </header>

      <div className="session-intro">
        <p>Start a conversation that matters.</p>
      </div>

      <div className="session-setup">
        <div className="create-form">
          <div className="form-intro">
            <h2>Start a conversation</h2>
            <p>Create a private space and share an invite link when you're ready.</p>
          </div>

          <input
            type="text"
            placeholder="Name this conversation (optional)"
            value={conversationName}
            onChange={e => setConversationName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
            disabled={isCreating}
          />

          <button
            onClick={handleCreate}
            disabled={isCreating}
          >
            {isCreating ? 'Creating...' : 'Create conversation space'}
          </button>
        </div>

        <aside className="setup-aside">
          <span className="setup-aside-title">Private & secure</span>
          <p>
            Your conversation is private. Share the invite link when
            the other person is ready. Feltabout helps keep difficult
            conversations clearer and more grounded.
          </p>
        </aside>
      </div>
    </main>
  )
}

// ─── Space Ready View ─────────────────────────────────────────────────────────

function SpaceReadyView({
  inviteUrl,
  onStartNow
}: {
  inviteUrl: string
  onStartNow: () => void
}) {
  const [copied, setCopied] = useState(false)

  const handleCopyInvite = () => {
    navigator.clipboard.writeText(inviteUrl).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <main className="app">
      <header className="app-header">
        <div className="brand-lockup">
          <Link href="/">
            <img className="brand-mark" src="/logo.png" alt="Feltabout" />
          </Link>
        </div>
      </header>

      <div className="session-setup" style={{ maxWidth: 520, margin: '0 auto' }}>
        <div className="space-ready-card">
          <div className="ready-icon">✓</div>
          <h2>Your conversation space is ready</h2>
          <p>
            Share this private link when the other person is ready to join.
            The link expires in 7 days.
          </p>

          <div className="invite-link-box">
            <span className="invite-link-text">{inviteUrl}</span>
          </div>

          <div className="invite-actions">
            <button onClick={handleCopyInvite} className={copied ? 'copied' : ''}>
              {copied ? '✓ Copied!' : 'Copy invite link'}
            </button>
            <button className="secondary" onClick={onStartNow}>
              I'm ready to start
            </button>
          </div>

          <p className="waiting-note">
            You can start the conversation solo and the other person
            can join later using the same link.
          </p>
        </div>
      </div>
    </main>
  )
}

// ─── Main Session Page ────────────────────────────────────────────────────────

export default function SessionPage() {
  const [sessionId, setSessionId] = useState('')
  const [name, setName] = useState('')
  const [joined, setJoined] = useState(false)
  const [myId, setMyId] = useState('')
  const [otherParticipant, setOtherParticipant] = useState<Participant | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  const [status, setStatus] = useState('')
  const [wsReady, setWsReady] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [streamingText, setStreamingText] = useState<string>('')
  const [streamingIndex, setStreamingIndex] = useState<number | null>(null)
  const [currentMode, setCurrentMode] = useState<string>('facilitation')
  const [debrief, setDebrief] = useState<{
    text: string
    topics: string[]
    emotional_arc: string
    unresolved_items: string[]
    recommendations: string
    safety_flags: SafetyFlag[]
  } | null>(null)
  const [debriefLoading, setDebriefLoading] = useState(false)
  const [escalated, setEscalated] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [historySessions, setHistorySessions] = useState<{
    session_id: string
    mode: string
    created_at: string
    participant_count: number
  }[]>([])
  const [playbackSession, setPlaybackSession] = useState<string | null>(null)
  const [playbackMessages, setPlaybackMessages] = useState<Message[]>([])
  const [playbackLoading, setPlaybackLoading] = useState(false)

  // Setup states
  const [setupStep, setSetupStep] = useState<'input' | 'ready' | 'active' | 'joining'>('input')
  const [inviteUrl, setInviteUrl] = useState('')
  const [spaceId, setSpaceId] = useState('')
  const [websocketSessionId, setWebsocketSessionId] = useState<string | null>(null)

  // Check for joiner data on mount
  useEffect(() => {
    const joinData = sessionStorage.getItem('feltabout_joining')
    if (joinData) {
      sessionStorage.removeItem('feltabout_joining')
      try {
        const data = JSON.parse(joinData)
        setWebsocketSessionId(data.websocket_session_id)
        setName(data.display_name || 'Guest')
        if (!LIVE_SESSIONS_ENABLED) {
          setJoined(true)
          setSetupStep('active')
          return
        }
        // Start connecting immediately with the scoped token
        setSetupStep('joining')
        setTimeout(() => {
          connectToSession(data.websocket_session_id, data.display_name || 'Guest', data.ws_access_token)
        }, 100)
      } catch {
        // Invalid data, show normal flow
      }
    }
  }, [])

  const wsRef = useRef<WebSocket | null>(null)
  const clientIdRef = useRef<() => string>(() => Math.random().toString(36).slice(2))
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const thinkingTimeoutRef = useRef<number | null>(null)
  const nameRef = useRef('')
  const router = useRouter()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => { scrollToBottom() }, [messages])
  useEffect(() => { nameRef.current = name }, [name])

  // ─── Create Conversation Space ─────────────────────────────────────────────

  const handleCreateSpace = async (conversationName: string) => {
    const token = useAuthStore.getState().token
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const res = await fetch(apiUrl('/conversation-spaces'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ name: conversationName || null }),
      })

      if (!res.ok) {
        setStatus('Error creating conversation space')
        return
      }

      const data = await res.json()
      setSpaceId(data.id)
      setInviteUrl(data.invite_url)
      setSetupStep('ready')
    } catch {
      setStatus('Connection error — is the backend running?')
    }
  }

  const handleStartNow = () => {
    // MVP 1 fallback: Live guided sessions are not yet available
    if (!LIVE_SESSIONS_ENABLED) {
      const displayName = useAuthStore.getState().userName || 'Guest'
      setName(displayName)
      setJoined(true)
      setSetupStep('active')
      // Don't connect to WebSocket - show the "coming soon" state instead
      return
    }

    // Original flow for when LIVE_SESSIONS_ENABLED is true
    const token = useAuthStore.getState().token
    if (!token || !spaceId) return

    fetch(apiUrl(`/conversation-spaces/${spaceId}`), {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(res => res.json())
      .then(data => {
        if (data.websocket_session_id) {
          const displayName = useAuthStore.getState().userName || 'Host'
          setName(displayName)
          connectToSession(data.websocket_session_id, displayName)
        }
      })
      .catch(() => {
        setStatus('Error starting conversation')
      })
  }

  const connectToSession = (sid: string, participantName: string, wsAccessToken?: string) => {
    nameRef.current = participantName
    useSessionStore.getState().clearSession()
    const wsEndpoint = wsAccessToken
      ? wsUrl(`/ws/${sid}?token=${encodeURIComponent(wsAccessToken)}`)
      : wsUrl(`/ws/${sid}`)
    const ws = new WebSocket(wsEndpoint)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      ws.send(JSON.stringify({ type: 'join', name: participantName }))
    }

    ws.onmessage = (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch {
        console.error('Non-JSON message received from backend:', event.data)
        return
      }

      if (data.type === 'session_created') {
        setSessionId(data.session_id)
      }

      if (data.type === 'participant_joined') {
        const p = data.participant
        const store = useSessionStore.getState()
        if (!store.myId) {
          setMyId(p.id)
          store.setMyId(p.id)
          setStatus(`Joined as ${p.name}`)
          setJoined(true)
          setSetupStep('active')
        } else if (p.id !== store.myId) {
          const otherP = { id: p.id, name: p.name, role: p.role, emotion: p.emotion }
          setOtherParticipant(otherP)
          store.setOther(otherP)
          setStatus(`${p.name} joined`)
        }
        setWsReady(true)
      }

      if (data.type === 'utterance') {
        const utt: Utterance = data.utterance

        if (utt.speaker_id === 'facilitator') {
          setMessages(prev => [
            ...prev,
            {
              id: utt.id,
              speaker: utt.speaker_name || 'Feltabout',
              text: utt.text,
              isFacilitator: true,
              timestamp: utt.timestamp,
            }
          ])
          return
        }

        const store = useSessionStore.getState()
        const isMe = utt.speaker_id === store.myId
        const speakerName = isMe
          ? nameRef.current
          : (store.otherParticipant?.name || utt.speaker_name || 'Other')
        const incomingClientId = data.client_id || utt.client_id

        setMessages(prev => {
          if (isMe && incomingClientId) {
            const pendingIndex = prev.findIndex(msg => msg.clientId === incomingClientId)
            if (pendingIndex !== -1) {
              return prev.map((msg, index) =>
                index === pendingIndex
                  ? {
                      ...msg,
                      id: utt.id,
                      speaker: speakerName,
                      text: utt.text,
                      timestamp: utt.timestamp,
                      pending: false,
                    }
                  : msg
              )
            }
          }

          return [
            ...prev,
            {
              id: utt.id,
              speaker: speakerName,
              text: utt.text,
              timestamp: utt.timestamp,
            }
          ]
        })

        if (data.facilitator_response) {
          clearThinkingTimeout()
          setIsThinking(false)
          setErrorMessage(null)
          setMessages(prev => [
            ...prev,
            {
              id: utt.id + '-fx',
              speaker: 'Feltabout',
              text: data.facilitator_response,
              isFacilitator: true,
              timestamp: utt.timestamp,
              safetyFlag: data.safety_flags?.[data.safety_flags.length - 1],
            }
          ])
        }
      }

      if (data.type === 'facilitator_token') {
        clearThinkingTimeout()
        setIsThinking(false)
        setErrorMessage(null)

        const incomingIndex = data.index
        if (streamingIndex !== incomingIndex) {
          setStreamingIndex(incomingIndex)
          setStreamingText(data.token)
        } else {
          setStreamingText(prev => prev + data.token)
        }

        if (thinkingTimeoutRef.current) {
          clearTimeout(thinkingTimeoutRef.current)
        }
        thinkingTimeoutRef.current = window.setTimeout(() => {
          setIsThinking(false)
          setStreamingText('')
          setStreamingIndex(null)
          setErrorMessage("Response streaming stalled. The backend may still finish; you can wait or try again.")
        }, 45000)
      }

      if (data.type === 'facilitator_complete') {
        clearThinkingTimeout()
        if (thinkingTimeoutRef.current) {
          clearTimeout(thinkingTimeoutRef.current)
          thinkingTimeoutRef.current = null
        }
        setIsThinking(false)
        setErrorMessage(null)
        setStreamingText('')
        setStreamingIndex(null)
        setMessages(prev => [
          ...prev,
          {
            id: 'fx-' + data.index,
            speaker: 'Feltabout',
            text: data.full_text,
            isFacilitator: true,
            timestamp: new Date().toISOString(),
          }
        ])
      }

      if (data.type === 'facilitator_idle') {
        clearThinkingTimeout()
        setIsThinking(false)
        setStreamingText('')
        setStreamingIndex(null)
        setErrorMessage(null)
      }

      if (data.type === 'facilitator_error') {
        clearThinkingTimeout()
        if (thinkingTimeoutRef.current) {
          clearTimeout(thinkingTimeoutRef.current)
          thinkingTimeoutRef.current = null
        }
        setIsThinking(false)
        setStreamingText('')
        setStreamingIndex(null)
        setErrorMessage(`Something went wrong: ${data.error}`)
        setMessages(prev => prev.map(msg =>
          msg.id === data.backend_id
            ? { ...msg, deliveryError: true, pending: false }
            : msg
        ))
      }

      if (data.type === 'mode_changed') {
        setCurrentMode(data.mode)
        const modeLabels: Record<string, string> = {
          'facilitation': 'Guided Flow',
          'speaker-listener': 'Take Turns',
          'repair': 'Reset',
          'debrief': 'Reflect',
        }
        const friendlyLabel = modeLabels[data.mode] || data.mode
        setMessages(prev => [
          ...prev,
          {
            id: 'mode-' + Date.now(),
            speaker: 'Guide',
            text: `Now using ${friendlyLabel}.`,
            isSystemMessage: true,
            timestamp: new Date().toISOString(),
          }
        ])
      }

      if (data.type === 'message_ack') {
        setMessages(prev => prev.map(msg =>
          msg.clientId === data.client_id
            ? { ...msg, pending: false }
            : msg
        ))
      }

      if (data.type === 'debrief_response') {
        setDebriefLoading(false)
        setDebrief({
          text: data.text,
          topics: data.topics || [],
          emotional_arc: data.emotional_arc || '',
          unresolved_items: data.unresolved_items || [],
          recommendations: data.recommendations || '',
          safety_flags: data.safety_flags || [],
        })
      }

      if (data.type === 'state') {
        const s = data.state
        if (!s) return

        if (s.mode) {
          setCurrentMode(s.mode)
        }

        const store = useSessionStore.getState()
        if (s.participants && Array.isArray(s.participants)) {
          const other = s.participants.find((p: Participant) => p.id !== store.myId)
          if (other) {
            setOtherParticipant(other)
            store.setOther(other)
          }
        }

        if (s.utterances && Array.isArray(s.utterances)) {
          const historyMessages: Message[] = s.utterances.map((u: Utterance) => ({
            id: u.id || `hist-${Math.random().toString(36).slice(2)}`,
            speaker: u.speaker_name || (u.speaker_id === 'facilitator' ? 'Feltabout' : 'Unknown'),
            text: u.text,
            isFacilitator: u.speaker_id === 'facilitator',
            timestamp: u.timestamp || new Date().toISOString(),
          }))
          setMessages(historyMessages)
        }

        if (s.participants && Array.isArray(s.participants)) {
          const myName = s.participants.find((p: Participant) => p.id === store.myId)?.name
          if (myName) {
            setStatus(`Rejoined as ${myName}`)
          }
        }
      }
    }

    ws.onclose = () => {
      setConnected(false)
      setWsReady(false)
      setStatus('Disconnected')
    }

    ws.onerror = () => {
      setStatus('Connection error — is backend running?')
    }
  }

  // ─── Setup Views ───────────────────────────────────────────────────────────

  if (setupStep === 'ready') {
    return (
      <SpaceReadyView
        inviteUrl={inviteUrl}
        onStartNow={handleStartNow}
      />
    )
  }

  if (setupStep === 'input') {
    return (
      <SessionSetupView onCreateSpace={handleCreateSpace} />
    )
  }

  // ─── MVP 1 Fallback: Live sessions not available ───────────────────────────

  // Early return when live sessions are disabled - show fallback instead of conversation UI
  if (!LIVE_SESSIONS_ENABLED) {
    return (
      <main className="app">
        <header className="app-header">
          <div className="brand-lockup">
            <Link href="/">
              <img className="brand-mark" src="/logo.png" alt="Feltabout" />
            </Link>
          </div>
        </header>

        <div className="session-room">
          <div className="participants-bar">
            <span className="participant-chip you">{useAuthStore.getState().userName || 'Guest'} (you)</span>
          </div>

          <div className="coming-soon-banner">
            <h3>Live guided sessions are coming soon</h3>
            <p>For now, use reflections and shared conversation spaces to prepare for meaningful conversations.</p>
            <Link href="/reflections" className="coming-soon-link">Go to Reflections →</Link>
          </div>

          <div className="messages">
            <div className="status">Live guided sessions are not yet available.</div>
          </div>

          <div className="input-area">
            <input
              type="text"
              placeholder="Live sessions are not available yet"
              disabled={true}
            />
            <button className="send-btn" disabled={true}>Send</button>
          </div>
        </div>
      </main>
    )
  }

  // ─── Conversation View (joined = true) ─────────────────────────────────────

  const clearThinkingTimeout = () => {
    if (thinkingTimeoutRef.current) {
      clearTimeout(thinkingTimeoutRef.current)
      thinkingTimeoutRef.current = null
    }
  }

  const sendMessage = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    const store = useSessionStore.getState()
    if (!input.trim() || !store.myId) return

    clearThinkingTimeout()
    setIsThinking(true)
    setErrorMessage(null)

    thinkingTimeoutRef.current = window.setTimeout(() => {
      setIsThinking(false)
      setErrorMessage("This is taking longer than expected. The backend may still finish; you can wait or send a shorter message.")
    }, 45000)

    const cid = clientIdRef.current()
    const tempMsg = {
      id: 'pending-' + cid,
      speaker: nameRef.current,
      text: input.trim(),
      timestamp: new Date().toISOString(),
      clientId: cid,
      pending: true,
    }

    setMessages(prev => [...prev, tempMsg])
    setInput('')

    try {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        speaker_id: store.myId,
        text: input.trim(),
        client_id: cid,
      }))
    } catch {
      clearThinkingTimeout()
      setIsThinking(false)
      setMessages(prev => prev.filter(m => m.clientId !== cid))
      setInput(input.trim())
      setErrorMessage("Failed to send message. Are you still connected?")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim()) sendMessage()
    }
  }

  return (
    <main className="app">
      <header className="app-header">
        <div className="brand-lockup">
          <Link href="/">
            <img className="brand-mark" src="/logo.png" alt="Feltabout" />
          </Link>
        </div>
        <div className="session-meta">
          <span className={`connection-pill ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? 'Active' : 'Conversation paused'}
          </span>
          <button className="history-btn" onClick={async () => {
            setShowHistory(true)
            try {
              const res = await fetch(apiUrl('/sessions'))
              const data = await res.json()
              setHistorySessions(Array.isArray(data) ? data : [])
            } catch {
              setHistorySessions([])
            }
          }}>View History</button>
        </div>
      </header>

      <div className="session-room">
        <div className="participants-bar">
          <span className="participant-chip you">{name} (you)</span>
          {otherParticipant && (
            <span className="participant-chip">{otherParticipant.name}</span>
          )}
          {!wsReady && <span className="participant-chip">Waiting for the other person...</span>}
        </div>

        <div className="mode-bar">
          <span className="mode-label">Mode:</span>
          {[
            { key: 'facilitation', label: 'Guided Flow' },
            { key: 'speaker-listener', label: 'Take Turns' },
            { key: 'repair', label: 'Reset' },
            { key: 'debrief', label: 'Reflect' },
          ].map(({ key, label }) => (
            <button
              key={key}
              className={`mode-btn ${currentMode === key ? 'active' : ''}`}
              onClick={() => {
                wsRef.current?.send(JSON.stringify({ type: 'set_mode', mode: key }))
                setCurrentMode(key)
              }}
              disabled={!wsReady}
            >
              {label}
            </button>
          ))}
          <button
            className="mode-btn"
            onClick={() => {
              setDebriefLoading(true)
              setDebrief(null)
              wsRef.current?.send(JSON.stringify({ type: 'request_debrief' }))
            }}
            disabled={!wsReady || debriefLoading}
          >
            {debriefLoading ? 'Summarizing...' : 'Pause & Summarize'}
          </button>
          {!escalated && (
            <button
              className="mode-btn escalate-btn"
              onClick={async () => {
                try {
                  const store = useSessionStore.getState()
                  await fetch(apiUrl(`/sessions/${sessionId}/escalate`), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ triggered_by: store.myId, reason: 'Break requested' }),
                  })
                  setEscalated(true)
                  setMessages(prev => [
                    ...prev,
                    {
                      id: 'escalate-' + Date.now(),
                      speaker: 'Feltabout',
                      text: 'Take your time. When you\'re ready to continue, you can return to this conversation.',
                      isFacilitator: true,
                      timestamp: new Date().toISOString(),
                    }
                  ])
                } catch {
                  setErrorMessage('Connection interrupted — please check if the backend is running.')
                }
              }}
              disabled={!wsReady}
            >
              Take a Break
            </button>
          )}
        </div>

        {!LIVE_SESSIONS_ENABLED && (
          <div className="coming-soon-banner">
            <h3>Live guided sessions are coming soon</h3>
            <p>For now, use reflections and shared conversation spaces to prepare for meaningful conversations.</p>
            <Link href="/reflections" className="coming-soon-link">Go to Reflections →</Link>
          </div>
        )}

        <div className="messages">
          {messages.length === 0 && (
            <div className="status">
              {wsReady
                ? 'Take a moment to share what\'s on your mind...'
                : LIVE_SESSIONS_ENABLED
                  ? 'Preparing your conversation space…'
                  : 'Live guided sessions are not yet available.'}
            </div>
          )}
          {messages.map(msg => (
            <div
              key={msg.id}
              className={`message ${msg.isFacilitator ? 'facilitator' : msg.speaker === name ? 'speaker-b' : 'speaker-a'}${msg.pending ? ' pending' : ''}${msg.deliveryError ? ' delivery-error' : ''}`}
            >
              {msg.safetyFlag && (
                <div className="safety-flag">
                  Safety flagged ({msg.safetyFlag.level}): {msg.safetyFlag.reason}
                </div>
              )}
              <span className="msg-speaker">{msg.speaker}</span>
              <div className="msg-text">{msg.text}</div>
              <span className="msg-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
          {isThinking && !streamingText && (
            <div className="message facilitator thinking">
              <span className="msg-speaker">Feltabout</span>
              <div className="msg-text">Feltabout is thinking...</div>
            </div>
          )}
          {streamingText && (
            <div className="message facilitator streaming">
              <span className="msg-speaker">Feltabout</span>
              <div className="msg-text">{streamingText}</div>
            </div>
          )}
          {errorMessage && (
            <div className="message error">
              <span className="msg-speaker">Error</span>
              <div className="msg-text">{errorMessage}</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {debrief && (
          <div className="debrief-panel">
            <div className="debrief-header">
              <span className="debrief-title">Session Summary</span>
              <button className="debrief-close" onClick={() => setDebrief(null)}>×</button>
            </div>
            {debrief.topics.length > 0 && (
              <div className="debrief-section">
                <span className="debrief-label">Topics</span>
                <div className="debrief-tags">
                  {debrief.topics.map((t, i) => (
                    <span key={i} className="debrief-tag">{t}</span>
                  ))}
                </div>
              </div>
            )}
            {debrief.emotional_arc && (
              <div className="debrief-section">
                <span className="debrief-label">Emotional arc</span>
                <p className="debrief-text">{debrief.emotional_arc}</p>
              </div>
            )}
            {debrief.unresolved_items.length > 0 && (
              <div className="debrief-section">
                <span className="debrief-label">Unresolved</span>
                <ul className="debrief-list">
                  {debrief.unresolved_items.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {debrief.recommendations && (
              <div className="debrief-section">
                <span className="debrief-label">Next steps</span>
                <p className="debrief-text">{debrief.recommendations}</p>
              </div>
            )}
            {debrief.safety_flags.length > 0 && (
              <div className="debrief-section">
                <div className="safety-flag">
                  {debrief.safety_flags.length} safety flag(s) flagged for human review
                </div>
              </div>
            )}
            {debrief.text && (
              <div className="debrief-section">
                <p className="debrief-text debrief-human">{debrief.text}</p>
              </div>
            )}
          </div>
        )}

        {showHistory && (
          <div className="history-panel">
            <div className="history-header">
              <span className="history-title">Session History</span>
              <button className="debrief-close" onClick={() => { setShowHistory(false); setPlaybackSession(null) }}>×</button>
            </div>
            {!playbackSession ? (
              <div className="history-list">
                {historySessions.length === 0 && (
                  <p className="history-empty">No past sessions found.</p>
                )}
                {historySessions.map(s => (
                  <button key={s.session_id} className="history-item" onClick={async () => {
                    setPlaybackSession(s.session_id)
                    setPlaybackLoading(true)
                    try {
                      const res = await fetch(apiUrl(`/sessions/${s.session_id}`))
                      const data = await res.json()
                      setPlaybackMessages(
                        (data.utterances || []).map((u: Utterance) => ({
                          id: u.id,
                          speaker: u.speaker_name,
                          text: u.text,
                          timestamp: u.timestamp,
                          isFacilitator: u.speaker_id === 'facilitator',
                        }))
                      )
                    } catch {
                      setPlaybackMessages([])
                    }
                    setPlaybackLoading(false)
                  }}>
                    <span className="history-sid">{s.session_id}</span>
                    <span className="history-meta">{s.mode} · {new Date(s.created_at).toLocaleDateString()}</span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="playback-view">
                <button className="history-back" onClick={() => setPlaybackSession(null)}>← Back</button>
                <div className="playback-messages">
                  {playbackLoading ? <p className="history-empty">Loading...</p> :
                   playbackMessages.map(msg => (
                    <div key={msg.id} className={`message ${msg.isFacilitator ? 'facilitator' : 'speaker-a'}`}>
                      <span className="msg-speaker">{msg.speaker}</span>
                      <div className="msg-text">{msg.text}</div>
                      <span className="msg-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {debriefLoading && !debrief && (
          <div className="debrief-panel loading">
            <div className="debrief-header">
              <span className="debrief-title">Generating summary...</span>
            </div>
            <div className="debrief-loading-dots">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        )}

        <div className="input-area">
          <input
            type="text"
            placeholder={LIVE_SESSIONS_ENABLED
              ? (wsReady ? "Type your message..." : "Connecting...")
              : "Live sessions are not available yet"}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!wsReady || !LIVE_SESSIONS_ENABLED}
          />
          <button className="send-btn" onClick={sendMessage} disabled={!wsReady || !LIVE_SESSIONS_ENABLED}>
            Send
          </button>
        </div>
      </div>
    </main>
  )
}

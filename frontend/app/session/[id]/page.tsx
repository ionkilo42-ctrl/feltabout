'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useSessionStore, useAuthStore } from '../../../store/sessionStore'
import { apiUrl, wsUrl } from '../../../lib/api'

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
  isSafetyCheck?: boolean
}

export default function SessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

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
  const [sessionLocked, setSessionLocked] = useState(false)
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
  const wsRef = useRef<WebSocket | null>(null)
  const clientIdRef = useRef<() => string>(() => Math.random().toString(36).slice(2))
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const thinkingTimeoutRef = useRef<number | null>(null)
  const nameRef = useRef('')

  const { token, userName } = useAuthStore()
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => { scrollToBottom() }, [messages])
  useEffect(() => { nameRef.current = name }, [name])

  // Redirect to login if no auth token
  useEffect(() => {
    if (!token) {
      router.push('/login')
    }
  }, [token, router])

  const connect = (sid: string, participantName: string) => {
    nameRef.current = participantName
    useSessionStore.getState().clearSession()
    const ws = new WebSocket(wsUrl(`/ws/${sid}`, token || undefined))
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
        // session created
      }

      if (data.type === 'participant_joined') {
        const p = data.participant
        const store = useSessionStore.getState()
        if (!store.myId) {
          setMyId(p.id)
          store.setMyId(p.id)
          setStatus(`Joined as ${p.name}`)
          setJoined(true)
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
              speaker: utt.speaker_name || 'RelateFX',
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
                  ? { ...msg, id: utt.id, speaker: speakerName, text: utt.text, timestamp: utt.timestamp, pending: false }
                  : msg
              )
            }
          }
          return [
            ...prev,
            { id: utt.id, speaker: speakerName, text: utt.text, timestamp: utt.timestamp }
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
              speaker: 'RelateFX',
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
        if (thinkingTimeoutRef.current) clearTimeout(thinkingTimeoutRef.current)
        thinkingTimeoutRef.current = window.setTimeout(() => {
          setIsThinking(false)
          setStreamingText('')
          setStreamingIndex(null)
          setErrorMessage("Response streaming stalled. The backend may still finish; you can wait or try again.")
        }, 45000)
      }

      if (data.type === 'facilitator_complete') {
        clearThinkingTimeout()
        if (thinkingTimeoutRef.current) { clearTimeout(thinkingTimeoutRef.current); thinkingTimeoutRef.current = null }
        setIsThinking(false)
        setErrorMessage(null)
        setStreamingText('')
        setStreamingIndex(null)
        setMessages(prev => [
          ...prev,
          { id: 'fx-' + data.index, speaker: 'RelateFX', text: data.full_text, isFacilitator: true, timestamp: new Date().toISOString() }
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
        if (thinkingTimeoutRef.current) { clearTimeout(thinkingTimeoutRef.current); thinkingTimeoutRef.current = null }
        setIsThinking(false)
        setStreamingText('')
        setStreamingIndex(null)
        setErrorMessage(`Something went wrong: ${data.error}`)
      }

      if (data.type === 'mode_changed') {
        setCurrentMode(data.mode)
        setMessages(prev => [
          ...prev,
          { id: 'mode-' + Date.now(), speaker: 'RelateFX', text: `Mode changed to: ${data.mode}`, isFacilitator: true, timestamp: new Date().toISOString() }
        ])
      }

      if (data.type === 'message_ack') {
        setMessages(prev => prev.map(msg =>
          msg.clientId === data.client_id ? { ...msg, pending: false } : msg
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

      if (data.type === 'facilitator_whisper') {
        // Private whisper — display with safety styling if it's a safety check
        const isSafetyCheck = data.is_safety_check === true
        setMessages(prev => [
          ...prev,
          {
            id: 'whisper-' + Date.now(),
            speaker: 'RelateFX',
            text: data.whisper,
            isFacilitator: true,
            isSafetyCheck,
            timestamp: new Date().toISOString(),
          }
        ])
      }

      if (data.type === 'turn_advanced') {
        // Update UI to show whose turn it is
        const nextSpeaker = data.current_speaker_id
        const phase = data.phase
        setMessages(prev => [
          ...prev,
          {
            id: 'turn-' + Date.now(),
            speaker: 'RelateFX',
            text: `Turn advanced — phase: ${phase}. Current speaker: ${nextSpeaker || 'unassigned'}`,
            isFacilitator: true,
            timestamp: new Date().toISOString(),
          }
        ])
      }

      // Phase 2: Handle state message with full session history on join
      if (data.type === 'state') {
        const s = data.state
        if (!s) return
        if (s.mode) setCurrentMode(s.mode)
        if (s.locked !== undefined) setSessionLocked(s.locked)
        const store = useSessionStore.getState()
        if (s.participants && Array.isArray(s.participants)) {
          const other = s.participants.find((p: Participant) => p.id !== store.myId)
          if (other) { setOtherParticipant(other); store.setOther(other) }
        }
        if (s.utterances && Array.isArray(s.utterances)) {
          const historyMessages: Message[] = s.utterances.map((u: Utterance) => ({
            id: u.id || `hist-${Math.random().toString(36).slice(2)}`,
            speaker: u.speaker_name || (u.speaker_id === 'facilitator' ? 'RelateFX' : 'Unknown'),
            text: u.text,
            isFacilitator: u.speaker_id === 'facilitator',
            timestamp: u.timestamp || new Date().toISOString(),
          }))
          setMessages(historyMessages)
        }
      }
    }

    ws.onclose = () => { setConnected(false); setWsReady(false); setStatus('Disconnected') }
    ws.onerror = () => { setStatus('Connection error — is backend running?') }
  }

  const joinSession = () => {
    if (!name.trim()) return
    connect(sessionId, name.trim())
  }

  const clearThinkingTimeout = () => {
    if (thinkingTimeoutRef.current) { clearTimeout(thinkingTimeoutRef.current); thinkingTimeoutRef.current = null }
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
    const tempMsg = { id: 'pending-' + cid, speaker: nameRef.current, text: input.trim(), timestamp: new Date().toISOString(), clientId: cid, pending: true }
    setMessages(prev => [...prev, tempMsg])
    setInput('')
    try {
      wsRef.current.send(JSON.stringify({ type: 'message', speaker_id: store.myId, text: input.trim(), client_id: cid }))
    } catch {
      clearThinkingTimeout()
      setIsThinking(false)
      setMessages(prev => prev.filter(m => m.clientId !== cid))
      setInput(input.trim())
      setErrorMessage("Failed to send message. Are you still connected?")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (input.trim()) sendMessage() }
  }

  if (!joined) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <div className="brand-lockup">
            <img className="brand-mark" src="/favicon.svg" alt="" />
            <div>
              <h1>Join Session</h1>
              <p className="subtitle">Session <span className="session-id">{sessionId}</span></p>
            </div>
          </div>
          <div className="session-actions">
            <input type="text" placeholder="Your name" value={name} onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && name.trim() && joinSession()} />
            <button onClick={joinSession} disabled={!name.trim()}>Join Session</button>
          </div>
          <p className="subtitle">Need the authenticated dashboard? <a href="/dashboard">Open dashboard</a></p>
        </section>
      </main>
    )
  }

  return (
    <main className="app">
      <header className="app-header">
        <div className="brand-lockup">
          <img className="brand-mark" src="/favicon.svg" alt="" />
          <div>
            <h1>RelateFX</h1>
            <p className="subtitle">Live facilitation room</p>
          </div>
        </div>
        <div className="session-meta">
          <span className="session-id">{sessionId}</span>
          <span className={`connection-pill ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </header>
      <div className="session-room">
        <div className="participants-bar">
          <span className="participant-chip you">{name} (you)</span>
          {otherParticipant && <span className="participant-chip">{otherParticipant.name}</span>}
          {!wsReady && <span className="participant-chip">connecting...</span>}
        </div>
        <div className="mode-bar">
          <span className="mode-label">Mode:</span>
          {['facilitation', 'speaker-listener', 'repair', 'debrief'].map(mode => (
            <button key={mode} className={`mode-btn ${currentMode === mode ? 'active' : ''}`}
              onClick={() => { wsRef.current?.send(JSON.stringify({ type: 'set_mode', mode })); setCurrentMode(mode) }}
              disabled={!wsReady}>{mode}</button>
          ))}
          <button className="mode-btn" onClick={() => { setDebriefLoading(true); setDebrief(null); wsRef.current?.send(JSON.stringify({ type: 'request_debrief' })) }}
            disabled={!wsReady || debriefLoading}>{debriefLoading ? 'Summarizing...' : 'Summarize'}</button>
          {!escalated && (
            <button className="mode-btn escalate-btn" onClick={async () => {
              try {
                await fetch(apiUrl(`/sessions/${sessionId}/escalate`), { method: 'POST' })
                setEscalated(true)
                setMessages(prev => [...prev, { id: 'escalate-' + Date.now(), speaker: 'RelateFX', text: 'Human review has been requested. This local build records the request; no external notification channel is configured yet.', isFacilitator: true, timestamp: new Date().toISOString() }])
              } catch { setErrorMessage('Could not escalate') }
            }} disabled={!wsReady}>Escalate</button>
          )}
        </div>
        <div className="messages">
          {messages.length === 0 && <div className="status">{wsReady ? 'Say something...' : 'Connecting...'}</div>}
          {messages.map(msg => (
            <div key={msg.id} className={`message ${msg.isFacilitator ? 'facilitator' : msg.speaker === name ? 'speaker-b' : 'speaker-a'}${msg.pending ? ' pending' : ''}${msg.deliveryError ? ' delivery-error' : ''}`}>
              {msg.safetyFlag && <div className="safety-flag">Safety flagged ({msg.safetyFlag.level}): {msg.safetyFlag.reason}</div>}
              <span className="msg-speaker">{msg.speaker}</span>
              <div className="msg-text">{msg.text}</div>
              <span className="msg-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
          {isThinking && !streamingText && <div className="message facilitator thinking"><span className="msg-speaker">RelateFX</span><div className="msg-text">RelateFX is thinking...</div></div>}
          {streamingText && <div className="message facilitator streaming"><span className="msg-speaker">RelateFX</span><div className="msg-text">{streamingText}</div></div>}
          {errorMessage && <div className="message error"><span className="msg-speaker">Error</span><div className="msg-text">{errorMessage}</div></div>}
          <div ref={messagesEndRef} />
        </div>
        {debrief && (
          <div className="debrief-panel">
            <div className="debrief-header"><span className="debrief-title">Session Summary</span><button className="debrief-close" onClick={() => setDebrief(null)}>×</button></div>
            {debrief.topics.length > 0 && <div className="debrief-section"><span className="debrief-label">Topics</span><div className="debrief-tags">{debrief.topics.map((t, i) => (<span key={i} className="debrief-tag">{t}</span>))}</div></div>}
            {debrief.emotional_arc && <div className="debrief-section"><span className="debrief-label">Emotional arc</span><p className="debrief-text">{debrief.emotional_arc}</p></div>}
            {debrief.unresolved_items.length > 0 && <div className="debrief-section"><span className="debrief-label">Unresolved</span><ul className="debrief-list">{debrief.unresolved_items.map((item, i) => (<li key={i}>{item}</li>))}</ul></div>}
            {debrief.recommendations && <div className="debrief-section"><span className="debrief-label">Next steps</span><p className="debrief-text">{debrief.recommendations}</p></div>}
            {debrief.safety_flags.length > 0 && <div className="debrief-section"><div className="safety-flag">{debrief.safety_flags.length} safety flag(s)</div></div>}
            {debrief.text && <div className="debrief-section"><p className="debrief-text debrief-human">{debrief.text}</p></div>}
          </div>
        )}
        <div className="input-area">
          <input type="text" placeholder={wsReady ? "Type your message..." : "Connecting..."} value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown} disabled={!wsReady} />
          <button onClick={sendMessage} disabled={!wsReady}>Send</button>
        </div>
      </div>
    </main>
  )
}

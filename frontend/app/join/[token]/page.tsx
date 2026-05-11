'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl, wsUrl } from '@/lib/api'

export default function JoinPage() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string

  const [status, setStatus] = useState<'verifying' | 'ready' | 'joining' | 'error' | 'full'>('verifying')
  const [isJoining, setIsJoining] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [spaceName, setSpaceName] = useState<string | null>(null)
  const [spaceId, setSpaceId] = useState<string | null>(null)
  const [displayName, setDisplayName] = useState('')
  const [nameError, setNameError] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setErrorMessage('No invite token provided.')
      return
    }

    // Verify the invite token
    fetch(apiUrl(`/conversation-spaces/verify-invite/${encodeURIComponent(token)}`))
      .then(res => res.json())
      .then(data => {
        if (!data.valid) {
          setStatus('error')
          setErrorMessage('This invite link has expired or is invalid.')
          return
        }
        if (data.is_full) {
          setStatus('full')
          setErrorMessage('This conversation space is already full.')
          return
        }
        setSpaceName(data.space_name)
        setSpaceId(data.space_id)
        setStatus('ready')
      })
      .catch(() => {
        setStatus('error')
        setErrorMessage('Connection error — is the backend running?')
      })
  }, [token])

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!displayName.trim()) {
      setNameError('Please enter your name')
      return
    }
    if (!spaceId) return

    setStatus('joining')
    setIsJoining(true)
    setNameError('')

    try {
      const res = await fetch(apiUrl(`/conversation-spaces/${spaceId}/join`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: displayName.trim() }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to join')
      }

      const data = await res.json()
      
      // Redirect to session with websocket_session_id
      // We need to pass the session info and connect
      // Store in sessionStorage to persist across the redirect
      sessionStorage.setItem('feltabout_joining', JSON.stringify({
        websocket_session_id: data.websocket_session_id,
        participant_id: data.participant_id,
        display_name: data.display_name,
        space_id: spaceId,
        ws_access_token: data.ws_access_token,
      }))
      
      // Navigate to session page
      router.push('/session')
    } catch (err) {
      setStatus('ready')
      setErrorMessage(err instanceof Error ? err.message : 'Failed to join conversation')
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
      </header>

      <div className="session-setup" style={{ maxWidth: 480, margin: '0 auto' }}>
        {status === 'verifying' && (
          <div className="join-card">
            <div className="spinner"></div>
            <p>Verifying your invite...</p>
          </div>
        )}

        {status === 'ready' && (
          <div className="join-card">
            <div className="invite-icon">🔒</div>
            <h2>Conversation invite</h2>
            <div className="mvp-notice">
              <p><strong>This feature is not yet available in MVP 1.</strong></p>
              <p>MVP 1 focuses on individual reflection and communication preparation.</p>
            </div>
            {spaceName && (
              <p className="space-name-label">Space: "{spaceName}"</p>
            )}
            <p className="join-description">
              Ready to start your own reflection?
            </p>
            <Link href="/session" className="btn-primary">
              Begin reflection
            </Link>
            <button className="secondary" onClick={() => router.push('/')}>
              Go to homepage
            </button>
          </div>
        )}

        {status === 'error' && (
          <div className="join-card error">
            <div className="error-icon">✗</div>
            <h2>Invite unavailable</h2>
            <p>{errorMessage}</p>
            <button className="secondary" onClick={() => router.push('/')}>
              Go to homepage
            </button>
          </div>
        )}

        {status === 'full' && (
          <div className="join-card error">
            <div className="error-icon">✗</div>
            <h2>Conversation full</h2>
            <p>{errorMessage}</p>
            <p className="hint">
              The host can create a new invite link if needed.
            </p>
            <button className="secondary" onClick={() => router.push('/')}>
              Go to homepage
            </button>
          </div>
        )}
      </div>
    </main>
  )
}
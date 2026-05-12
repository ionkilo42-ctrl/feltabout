'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useParticipantStore } from '@/store/sessionStore'

export default function JoinSessionPage() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string

  const setParticipant = useParticipantStore((s) => s.setParticipant)

  const [displayName, setDisplayName] = useState('')
  const [isJoining, setIsJoining] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [spaceName, setSpaceName] = useState<string | null>(null)

  // Validate token and get space info
  useEffect(() => {
    const validateToken = async () => {
      try {
        const res = await fetch(apiUrl(`/conversation-spaces/join/${token}`))
        
        if (!res.ok) {
          if (res.status === 404) {
            setError('This invite link is invalid or has expired.')
          } else {
            setError('Failed to validate invite link.')
          }
          setIsLoading(false)
          return
        }

        const data = await res.json()
        setSpaceName(data.name || 'Shared Session')
        setIsLoading(false)
      } catch {
        setError('Failed to connect. Please check your connection and try again.')
        setIsLoading(false)
      }
    }

    validateToken()
  }, [token])

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!displayName.trim()) return

    setIsJoining(true)
    setError(null)

    try {
      // Join the space
      const joinRes = await fetch(apiUrl(`/conversation-spaces/join/${token}`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: displayName.trim() }),
      })

      if (!joinRes.ok) {
        throw new Error('Failed to join session')
      }

      const data = await joinRes.json()
      const spaceId = data.space_id

      // Store in localStorage
      localStorage.setItem('current_space_id', spaceId)
      localStorage.setItem('invite_token', token)

      // Set participant in store
      setParticipant({
        participantId: data.participant_id || 'guest',
        displayName: displayName.trim(),
        isOwner: false,
        spaceId,
        joinedAt: new Date().toISOString(),
      })

      // Redirect to session
      router.push(`/session/${spaceId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join session')
      setIsJoining(false)
    }
  }

  if (isLoading) {
    return (
      <main className="join-page">
        <div className="join-container">
          <div className="loading">
            <div className="spinner"></div>
            <p>Validating invite...</p>
          </div>
        </div>
        <style>{styles}</style>
      </main>
    )
  }

  if (error && !spaceName) {
    return (
      <main className="join-page">
        <div className="join-container">
          <div className="error-card">
            <span className="error-icon">🔗</span>
            <h2>Invalid invite</h2>
            <p>{error}</p>
            <Link href="/" className="btn-secondary">
              Go to home
            </Link>
          </div>
        </div>
        <style>{styles}</style>
      </main>
    )
  }

  return (
    <main className="join-page">
      <div className="join-container">
        <Link href="/" className="back-link">
          ← Back to home
        </Link>

        <div className="join-card">
          <div className="join-header">
            <span className="join-icon">🤝</span>
            <h1>Join Shared Session</h1>
            <p>
              {spaceName && <strong>{spaceName}</strong>}
              {' '}has invited you to a shared session with Aimee.
            </p>
          </div>

          <form onSubmit={handleJoin} className="join-form">
            <div className="form-group">
              <label htmlFor="displayName">Your name</label>
              <input
                id="displayName"
                type="text"
                placeholder="Enter your name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                disabled={isJoining}
                autoFocus
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              type="submit"
              className="btn-primary"
              disabled={!displayName.trim() || isJoining}
            >
              {isJoining ? 'Joining...' : 'Join Session'}
            </button>
          </form>

          <div className="join-footer">
            <p>You'll be able to chat with Aimee and the session host.</p>
          </div>
        </div>
      </div>

      <style>{styles}</style>
    </main>
  )
}

const styles = `
.join-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--page-bg, #FAF9F7);
}

.join-container {
  width: 100%;
  max-width: 420px;
}

.back-link {
  display: inline-block;
  margin-bottom: 2rem;
  font-size: 0.9rem;
  color: var(--text-secondary, #374151);
  text-decoration: none;
}

.back-link:hover {
  color: var(--accent, #e07a5f);
}

.loading {
  text-align: center;
  padding: 2rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border, #e5e7eb);
  border-top-color: var(--accent, #e07a5f);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-card {
  background: white;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 20px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  display: block;
}

.error-card h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text, #111827);
  margin: 0 0 0.75rem 0;
}

.error-card p {
  font-size: 0.95rem;
  color: var(--text-secondary, #6b7280);
  margin: 0 0 1.5rem 0;
}

.join-card {
  background: white;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

.join-header {
  text-align: center;
  margin-bottom: 2rem;
}

.join-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  display: block;
}

.join-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text, #111827);
  margin: 0 0 0.75rem 0;
}

.join-header p {
  font-size: 0.95rem;
  color: var(--text-secondary, #6b7280);
  margin: 0;
  line-height: 1.5;
}

.join-header strong {
  color: var(--accent, #e07a5f);
}

.join-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary, #374151);
}

.form-group input {
  padding: 0.875rem 1rem;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 12px;
  font-size: 1rem;
  background: var(--card, #fafafa);
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent, #e07a5f);
  box-shadow: 0 0 0 3px rgba(224, 122, 95, 0.1);
}

.error-message {
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #dc2626;
}

.btn-primary {
  padding: 1rem;
  background: var(--gradient-core, linear-gradient(135deg, #33d6c8, #e07a5f));
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(224, 122, 95, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
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
  transition: background 0.15s;
}

.btn-secondary:hover {
  background: var(--card, #fafafa);
}

.join-footer {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border, #e5e7eb);
  text-align: center;
}

.join-footer p {
  font-size: 0.85rem;
  color: var(--text-muted, #9ca3af);
  margin: 0;
}
`
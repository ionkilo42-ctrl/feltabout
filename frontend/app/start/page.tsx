'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useParticipantStore } from '@/store/sessionStore'

export default function StartSessionPage() {
  const router = useRouter()
  const setParticipant = useParticipantStore((s) => s.setParticipant)

  const [displayName, setDisplayName] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreateSpace = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!displayName.trim()) return

    setIsCreating(true)
    setError(null)

    try {
      // Create conversation space
      const spaceRes = await fetch(apiUrl('/conversation-spaces'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Shared Session' }),
      })

      if (!spaceRes.ok) {
        throw new Error('Failed to create session')
      }

      const space = await spaceRes.json()
      const spaceId = space.id
      const inviteToken = space.invite_token

      // Store in localStorage for persistence
      localStorage.setItem('current_space_id', spaceId)
      localStorage.setItem('invite_token', inviteToken)

      // Set participant in store
      setParticipant({
        participantId: 'owner',  // Placeholder until backend sets real ID
        displayName: displayName.trim(),
        isOwner: true,
        spaceId,
        joinedAt: new Date().toISOString(),
      })

      // Redirect to session
      router.push(`/session/${spaceId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session')
      setIsCreating(false)
    }
  }

  return (
    <main className="start-page">
      <div className="start-container">
        <Link href="/" className="back-link">
          ← Back to home
        </Link>

        <div className="start-card">
          <div className="start-header">
            <span className="start-icon">✨</span>
            <h1>Start a Shared Session</h1>
            <p>
              Share this session with someone to communicate together with
              Aimee as your guide.
            </p>
          </div>

          <form onSubmit={handleCreateSpace} className="start-form">
            <div className="form-group">
              <label htmlFor="displayName">Your name</label>
              <input
                id="displayName"
                type="text"
                placeholder="Enter your name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                disabled={isCreating}
                autoFocus
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              type="submit"
              className="btn-primary"
              disabled={!displayName.trim() || isCreating}
            >
              {isCreating ? 'Creating session...' : 'Create Session'}
            </button>
          </form>

          <div className="start-footer">
            <p>After creating, you can share a link with someone to join.</p>
          </div>
        </div>
      </div>

      <style>{styles}</style>
    </main>
  )
}

const styles = `
.start-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--page-bg, #FAF9F7);
}

.start-container {
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

.start-card {
  background: white;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

.start-header {
  text-align: center;
  margin-bottom: 2rem;
}

.start-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  display: block;
}

.start-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text, #111827);
  margin: 0 0 0.75rem 0;
}

.start-header p {
  font-size: 0.95rem;
  color: var(--text-secondary, #6b7280);
  margin: 0;
  line-height: 1.5;
}

.start-form {
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

.start-footer {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border, #e5e7eb);
  text-align: center;
}

.start-footer p {
  font-size: 0.85rem;
  color: var(--text-muted, #9ca3af);
  margin: 0;
}
`
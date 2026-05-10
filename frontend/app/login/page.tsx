'use client'
import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/store/sessionStore'
import { apiUrl } from '@/lib/api'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'sent' | 'error'>('idle')
  const [error, setError] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setStatus('loading')

    try {
      const res = await fetch(apiUrl('/auth/magic-link-request'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })

      if (!res.ok) {
        const data = await res.json()
        setError(data.detail || 'Failed to send magic link')
        setStatus('error')
        return
      }

      setStatus('sent')
    } catch {
      setError('Connection error — is the backend running?')
      setStatus('error')
    }
  }

  if (status === 'sent') {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <div className="brand-lockup">
            <img className="brand-mark" src="/logo.png" alt="" />
          </div>
          <div className="magic-link-sent">
            <div className="sent-icon">✉️</div>
            <h2>Check your email</h2>
            <p>
              We sent a sign-in link to <strong>{email}</strong>.
              <br />
              Click the link to access your reflections.
            </p>
            <p className="dev-note">
              (For development: check the server console for the magic link)
            </p>
            <button
              className="text-btn"
              onClick={() => {
                setStatus('idle')
                setEmail('')
              }}
            >
              Use a different email
            </button>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-lockup">
          <img className="brand-mark" src="/logo.png" alt="" />
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-intro">
            <h2>Sign in to Feltabout</h2>
            <p>Enter your email and we'll send you a private sign-in link.</p>
          </div>
          <input
            type="email"
            placeholder="Your email"
            autoComplete="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            disabled={status === 'loading'}
          />
          {error && <p className="status error">{error}</p>}
          <button type="submit" disabled={status === 'loading' || !email.trim()}>
            {status === 'loading' ? 'Sending...' : 'Send sign-in link'}
          </button>
        </form>
        <div className="auth-footer">
          <p>No password needed. No account required.</p>
        </div>
      </section>
    </main>
  )
}
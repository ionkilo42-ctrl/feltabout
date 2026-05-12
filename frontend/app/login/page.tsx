'use client'
import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/store/sessionStore'
import { apiUrl } from '@/lib/api'

function LoginForm() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle')
  const [error, setError] = useState('')
  const [showPasswordForm, setShowPasswordForm] = useState(false)
  const [password, setPassword] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)

  const next = searchParams.get('next') || '/reflections'

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setStatus('loading')

    try {
      const res = await fetch(apiUrl('/auth/magic-link-request'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, next }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Failed to send magic link')
        setStatus('error')
        return
      }

      setStatus('idle')
      setEmail('')
      alert('Check your email for a sign-in link!')
    } catch {
      setError('Connection error — is the backend running?')
      setStatus('error')
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setStatus('loading')

    try {
      const res = await fetch(apiUrl('/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Failed to sign in')
        setStatus('error')
        return
      }

      setAuth(data.token, data.user.id, data.user.name, data.user.email)
      router.push(next)
    } catch {
      setError('Connection error — is the backend running?')
      setStatus('error')
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-lockup">
          <img className="brand-mark" src="/logo.png" alt="" />
          <h1 className="brand-title">Welcome to Feltabout</h1>
        </div>

        {!showPasswordForm && (
          <div className="auth-form-section">
            <form className="auth-form" onSubmit={handleEmailSubmit}>
              <div className="form-intro">
                <h2>Sign in with email</h2>
                <p>We'll send you a link to your inbox.</p>
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
                {status === 'loading' ? 'Sending...' : 'Send magic link'}
              </button>
              <div className="auth-divider">
                <span>or</span>
              </div>
              <button 
                type="button" 
                className="btn-text"
                onClick={() => setShowPasswordForm(true)}
              >
                Use password instead
              </button>
            </form>
          </div>
        )}

        {showPasswordForm && (
          <div className="auth-form-section">
            <form className="auth-form" onSubmit={handlePasswordSubmit}>
              <div className="form-intro">
                <h2>Sign in with password</h2>
                <p>Enter your email and password.</p>
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
              <input
                type="password"
                placeholder="Your password"
                autoComplete="current-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                disabled={status === 'loading'}
              />
              {error && <p className="status error">{error}</p>}
              <button type="submit" disabled={status === 'loading' || !email.trim() || !password}>
                {status === 'loading' ? 'Signing in...' : 'Sign in'}
              </button>
              <button type="button" className="btn-back" onClick={() => setShowPasswordForm(false)}>
                Back
              </button>
            </form>
          </div>
        )}

        <div className="auth-footer">
          <p>
            New to Feltabout?{' '}
            <a href={`/register${next !== '/reflections' ? `?next=${encodeURIComponent(next)}` : ''}`}>
              Create an account
            </a>
          </p>
        </div>
      </section>
    </main>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="auth-shell" />}>
      <LoginForm />
    </Suspense>
  )
}
'use client'
import { Suspense } from 'react'
import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/store/sessionStore'
import { apiUrl } from '@/lib/api'

function RegisterForm() {
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle')
  const [error, setError] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)

  const next = searchParams.get('next') || '/reflections'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setStatus('loading')

    // Validate password length
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      setStatus('error')
      return
    }

    try {
      const res = await fetch(apiUrl('/auth/register'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          display_name: displayName || email.split('@')[0],
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Failed to create account')
        setStatus('error')
        return
      }

      // Save auth data
      setAuth(data.token, data.user.id, data.user.name)
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
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-intro">
            <h2>Create your private account</h2>
            <p>Keep your account and reflections secure.</p>
          </div>
          <input
            type="text"
            placeholder="Your name"
            autoComplete="name"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            disabled={status === 'loading'}
          />
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
            placeholder="Create a password (8+ characters)"
            autoComplete="new-password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={8}
            disabled={status === 'loading'}
          />
          {error && <p className="status error">{error}</p>}
          <button type="submit" disabled={status === 'loading' || !email.trim() || !password}>
            {status === 'loading' ? 'Creating account...' : 'Create account'}
          </button>
        </form>
        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <a href={`/login${next !== '/reflections' ? `?next=${encodeURIComponent(next)}` : ''}`}>
              Sign in
            </a>
          </p>
        </div>
      </section>
    </main>
  )
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<main className="auth-shell" />}>
      <RegisterForm />
    </Suspense>
  )
}

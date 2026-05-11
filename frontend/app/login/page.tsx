'use client'
import { Suspense } from 'react'
import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/store/sessionStore'
import { apiUrl } from '@/lib/api'

function LoginForm() {
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
              <h2>Welcome back</h2>
              <p>Sign in to your account.</p>
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
        </form>
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

'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '../../store/sessionStore'
import { apiUrl } from '../../lib/api'

export default function LoginPage() {
  const [isSignup, setIsSignup] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const router = useRouter()
  const setAuth = useAuthStore((s) => s.setAuth)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    const endpoint = isSignup ? '/auth/signup' : '/auth/login'
    const body = isSignup ? { email, password, name } : { email, password }
    try {
      const res = await fetch(apiUrl(endpoint), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const data = await res.json()
        setError(data.detail || 'Authentication failed')
        return
      }
      const data = await res.json()
      setAuth(data.token, data.user_id, data.name)
      router.push('/dashboard')
    } catch {
      setError('Connection error — is backend running?')
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-lockup">
          <img className="brand-mark" src="/favicon.svg" alt="" />
          <div>
            <h1>RelateFX</h1>
            <p className="subtitle">{isSignup ? 'Create a facilitator workspace account' : 'Sign in to your workspace'}</p>
          </div>
        </div>
      <form className="auth-form" onSubmit={handleSubmit}>
        {isSignup && (
          <input
            type="text"
            placeholder="Your name"
            value={name}
            onChange={e => setName(e.target.value)}
            required
          />
        )}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
        />
        {error && <p className="status error">{error}</p>}
        <button type="submit">
          {isSignup ? 'Sign up' : 'Sign in'}
        </button>
      </form>
      <button
        className="link-button"
        onClick={() => setIsSignup(!isSignup)}
      >
        {isSignup ? 'Already have an account? Sign in' : 'Need an account? Sign up'}
      </button>
      </section>
    </main>
  )
}

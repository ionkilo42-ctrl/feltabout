'use client'
import { Suspense } from 'react'
import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/store/sessionStore'
import { apiUrl } from '@/lib/api'

function VerifyStatus() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [errorMessage, setErrorMessage] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)

  useEffect(() => {
    async function verifyToken() {
      const token = searchParams.get('token')

      if (!token) {
        setStatus('error')
        setErrorMessage('No verification token provided.')
        return
      }

      try {
        const res = await fetch(apiUrl(`/auth/verify?token=${encodeURIComponent(token)}`))

        if (!res.ok) {
          const data = await res.json()
          setStatus('error')
          setErrorMessage(data.detail || 'Failed to verify token.')
          return
        }

        const data = await res.json()
        
        // Store auth credentials
        setAuth(data.token, data.user_id, data.name)

        setStatus('success')

        // Redirect to ?next= param if present, otherwise dashboard
        const next = searchParams.get('next')
        const redirectTo = next && next.startsWith('/') ? next : '/dashboard'

        setTimeout(() => {
          router.push(redirectTo)
        }, 1500)
      } catch {
        setStatus('error')
        setErrorMessage('Connection error — is the backend running?')
      }
    }

    verifyToken()
  }, [searchParams, setAuth, router])

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-lockup">
          <img className="brand-mark" src="/logo.png" alt="" />
        </div>

        {status === 'loading' && (
          <div className="verify-status">
            <div className="spinner"></div>
            <p>Verifying your sign-in link...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="verify-status success">
            <div className="success-icon">✓</div>
            <h2>You're signed in!</h2>
            <p>Redirecting to your reflections...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="verify-status error">
            <div className="error-icon">✗</div>
            <h2>Verification failed</h2>
            <p>{errorMessage}</p>
            <p className="hint">
              The link may have expired or already been used.
              <br />
              Try signing in again.
            </p>
            <button
              className="text-btn"
              onClick={() => router.push('/login')}
            >
              Go to sign in
            </button>
          </div>
        )}
      </section>
    </main>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<main className="auth-shell" />}>
      <VerifyStatus />
    </Suspense>
  )
}

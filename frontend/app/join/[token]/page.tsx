'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useParticipantStore } from '@/store/sessionStore'
import { SessionEntryCard } from '@/components/ui/SessionEntryCard'
import styles from './JoinPage.module.css'

export default function JoinPage() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string

  const setParticipant = useParticipantStore((s) => s.setParticipant)

  const [isJoining, setIsJoining] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [spaceName, setSpaceName] = useState<string | null>(null)

  useEffect(() => {
    const validateToken = async () => {
      try {
        const verifyUrl = apiUrl(`/conversation-spaces/verify-invite/${encodeURIComponent(token)}`)
        
        const res = await fetch(verifyUrl)
        
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
        setSpaceName(data.space_name || 'Shared Session')
        setIsLoading(false)
      } catch (err) {
        setError('Failed to connect. Please check your connection and try again.')
        setIsLoading(false)
      }
    }

    validateToken()
  }, [token])

  const handleJoin = async (name: string) => {
    setIsJoining(true)
    setError(null)

    try {
      const verifyUrl = apiUrl(`/conversation-spaces/verify-invite/${encodeURIComponent(token)}`)
      const verifyRes = await fetch(verifyUrl)
      
      if (!verifyRes.ok) {
        throw new Error('This invite link is invalid or has expired.')
      }

      const verifyData = await verifyRes.json()
      const spaceId = verifyData.space_id

      if (!spaceId) {
        throw new Error('Could not find the session associated with this invite.')
      }

      const joinUrl = apiUrl(`/conversation-spaces/${spaceId}/join`)
      
      const joinRes = await fetch(joinUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: name }),
      })

      if (!joinRes.ok) {
        const errorData = await joinRes.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to join session')
      }

      const data = await joinRes.json()

      localStorage.setItem('current_space_id', spaceId)
      localStorage.setItem('invite_token', token)

      setParticipant({
        participantId: data.participant_id || 'guest',
        displayName: name,
        isOwner: false,
        spaceId,
        joinedAt: new Date().toISOString(),
      })

      router.push(`/session/${spaceId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join session')
      setIsJoining(false)
    }
  }

  if (isLoading) {
    return (
      <main className={styles.page}>
        <div className={styles.container}>
          <div className={styles.loading}>
            <div className={styles.spinner}>
              <span></span>
              <span></span>
              <span></span>
            </div>
            <p className={styles.loadingText}>Validating invite...</p>
          </div>
        </div>
      </main>
    )
  }

  if (error && !spaceName) {
    return (
      <main className={styles.page}>
        <div className={styles.container}>
          <div className={styles.errorCard}>
            <span className={styles.errorIcon}>🔗</span>
            <h2 className={styles.errorTitle}>Invalid invite</h2>
            <p className={styles.errorMessage}>{error}</p>
            <Link href="/" className={styles.errorButton}>
              Go to home
            </Link>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <Link href="/" className={styles.backLink}>
          ← Back to home
        </Link>

        <SessionEntryCard
          mode="join"
          sessionName={spaceName || undefined}
          onSubmit={handleJoin}
          isLoading={isJoining}
          error={error}
        />
      </div>
    </main>
  )
}
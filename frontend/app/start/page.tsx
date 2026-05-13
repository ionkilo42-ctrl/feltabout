'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useParticipantStore } from '@/store/sessionStore'
import { SessionEntryCard } from '@/components/ui/SessionEntryCard'
import styles from './StartPage.module.css'

export default function StartPage() {
  const router = useRouter()
  const setParticipant = useParticipantStore((s) => s.setParticipant)

  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreateSpace = async (name: string) => {
    setIsCreating(true)
    setError(null)

    try {
      const spaceRes = await fetch(apiUrl('/conversation-spaces'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: 'Shared Session',
          frontend_origin: window.location.origin,
        }),
      })

      if (!spaceRes.ok) {
        throw new Error('Failed to create session')
      }

      const space = await spaceRes.json()
      const spaceId = space.id
      const inviteToken = space.invite_token

      if (!spaceId || !inviteToken) {
        throw new Error('Session was created but invite link was not returned')
      }

      localStorage.setItem('current_space_id', spaceId)
      localStorage.setItem('invite_token', inviteToken)

      setParticipant({
        participantId: 'owner',
        displayName: name,
        isOwner: true,
        spaceId,
        joinedAt: new Date().toISOString(),
      })

      router.push(`/session/${spaceId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session')
      setIsCreating(false)
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <Link href="/" className={styles.backLink}>
          ← Back to home
        </Link>

        <SessionEntryCard
          mode="start"
          onSubmit={handleCreateSpace}
          isLoading={isCreating}
          error={error}
        />
      </div>
    </main>
  )
}
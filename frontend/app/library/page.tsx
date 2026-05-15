'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useAuthStore } from '@/store/sessionStore'
import styles from './LibraryPage.module.css'

interface LibraryItem {
  type: 'reflection' | 'memory' | 'conversation'
  id: string
  name: string
  created_at: string
  status: string
  participant_count: number
  is_owner: boolean
  subtitle?: string | null
}

interface Pattern {
  type: string
  insight: string
  occurrences: number
  confidence: string
  examples: string[]
}

type Filter = 'all' | 'reflection' | 'conversation'

export default function LibraryPage() {
  const [items, setItems] = useState<LibraryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [patternsLoading, setPatternsLoading] = useState(false)
  const token = useAuthStore(s => s.token)

  // Fetch library items
  useEffect(() => {
    if (!token) {
      setLoading(false)
      setError('Please sign in to view your library.')
      return
    }

    fetch(apiUrl('/library'), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to load library')
        return res.json()
      })
      .then(data => {
        setItems(data.items || [])
        setLoading(false)
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : 'Failed to load')
        setLoading(false)
      })
  }, [token])

  const isReflectionLike = (item: LibraryItem) =>
    item.type === 'reflection' || item.type === 'memory'

  // Fetch patterns (separate endpoint, shows only when ≥3 reflections)
  useEffect(() => {
    if (!token) return
    setPatternsLoading(true)
    fetch(apiUrl('/patterns'), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data && data.patterns) {
          setPatterns(data.patterns)
        }
        setPatternsLoading(false)
      })
      .catch(() => setPatternsLoading(false))
  }, [token])

  const filtered = filter === 'all'
    ? items
    : filter === 'reflection'
      ? items.filter(isReflectionLike)
      : items.filter(i => i.type === filter)

  const statusLabel = (type: string, status: string) => {
    if (type === 'reflection' || type === 'memory') {
      const map: Record<string, string> = { draft: 'Draft', completed: 'Complete', archived: 'Archived' }
      return map[status] || status
    }
    const map: Record<string, string> = { pending: 'Waiting', active: 'Active', complete: 'Finished' }
    return map[status] || status
  }

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    } catch {
      return iso
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <Link href="/" className={styles.brandLockup} aria-label="Feltabout home">
            <img className={styles.brandMark} src="/logo.png" alt="Feltabout" />
          </Link>
          <div className={styles.pageTitleGroup}>
            <Link href="/" className={styles.backLink}>← Back</Link>
            <h1>Library</h1>
          </div>
        </div>
        <div className={styles.headerActions}>
          <Link href="/session" className="btn-primary">
            New reflection
          </Link>
        </div>
      </header>

      <div className={styles.container}>
        {/* Filter tabs */}
        <div className={styles.filterBar}>
          {(['all', 'reflection', 'conversation'] as Filter[]).map(f => (
            <button
              key={f}
              className={`${styles.filterBtn} ${filter === f ? styles.active : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f === 'reflection' ? 'Reflections' : 'Conversations'}
              {f !== 'all' && (
                <span className={styles.filterCount}>
                  {f === 'reflection'
                    ? items.filter(isReflectionLike).length
                    : items.filter(i => i.type === f).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Patterns section */}
        {(patterns.length > 0 || patternsLoading) && (
          <div className={styles.patternsSection}>
            <div className={styles.patternsHeader}>
              <h3>Patterns you may notice</h3>
              <span className={styles.patternsPrivacy}>Only you can see these patterns.</span>
            </div>

            {patternsLoading ? (
              <div className={styles.patternsLoading}>
                <div className={styles.spinnerSmall} />
              </div>
            ) : (
              <div className={styles.patternsList}>
                {patterns.map((p, i) => (
                  <div key={i} className={`${styles.patternCard} ${styles[`pattern${p.confidence.charAt(0).toUpperCase() + p.confidence.slice(1)}`]}`}>
                    <div className={styles.patternInsight}>{p.insight}</div>
                    {p.confidence === 'low' && (
                      <div className={styles.patternTentative}>This may be showing up…</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {patterns.length === 0 && !patternsLoading && (
          <div className={styles.patternsEmpty}>
            <p>As you save more reflections, Feltabout can help surface recurring themes gently.</p>
            <span className={styles.patternsPrivacyNote}>Only you can see these patterns.</span>
          </div>
        )}

        {/* Content */}
        {loading && (
          <div className={styles.loading}>
            <div className={styles.spinner} />
            <p>Loading your library...</p>
          </div>
        )}

        {error && (
          <div className={styles.empty}>
            <p className={styles.libraryError}>{error}</p>
            {error.includes('sign in') && (
              <Link href="/login" className="btn-primary">Sign in</Link>
            )}
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>
              {filter === 'all' ? '📚' : filter === 'reflection' ? '📝' : '💬'}
            </div>
            <h2>Nothing here yet</h2>
            <p>
              {filter === 'all'
                ? 'Start a reflection — your history will live here.'
                : filter === 'reflection'
                ? 'Start your first reflection to prepare for an important conversation.'
                : 'Conversation spaces are coming soon.'}
            </p>
            <Link href="/session" className="btn-primary">New reflection</Link>
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <div className={styles.list}>
            {filtered.map(item => (
              <Link
                key={item.id}
                href={
                  item.type === 'memory'
                    ? `/memories/${item.id}`
                    : item.type === 'reflection'
                      ? `/reflections/${item.id}`
                      : `/session`
                }
                className={styles.card}
              >
                <div className={styles.cardIcon}>
                  {item.type === 'conversation' ? '💬' : '📝'}
                </div>
                <div className={styles.cardBody}>
                  <div className={styles.cardName}>{item.name}</div>
                  {item.subtitle && (
                    <div className={styles.cardSubtitle}>{item.subtitle}</div>
                  )}
                  <div className={styles.cardMeta}>
                    <span className={styles.cardDate}>{formatDate(item.created_at)}</span>
                    {item.type === 'conversation' && (
                      <span className={styles.cardParticipants}>
                        {item.participant_count} {item.participant_count === 1 ? 'person' : 'people'}
                      </span>
                    )}
                  </div>
                </div>
                <div className={styles.cardRight}>
                  <span className={`${styles.statusBadge} ${styles[`status${item.status.charAt(0).toUpperCase() + item.status.slice(1)}`]}`}>
                    {statusLabel(item.type, item.status)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}

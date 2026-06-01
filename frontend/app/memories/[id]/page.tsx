"use client"

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

import { EMOTION_COLORS, Memory, getV2Memory } from '@/lib/v2-api'
import { useAuthStore } from '@/store/sessionStore'

function formatDate(value?: string) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  } catch {
    return value
  }
}

export default function MemoryDetailPage() {
  const params = useParams()
  const token = useAuthStore((state) => state.token)
  const id = params.id as string

  const [memory, setMemory] = useState<Memory | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    if (!token) {
      setError('Please sign in to view this reflection.')
      setLoading(false)
      return
    }

    let active = true

    getV2Memory(id)
      .then((data) => {
        if (!active) return
        setMemory(data)
        setLoading(false)
      })
      .catch((err) => {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Could not load reflection.')
        setLoading(false)
      })

    return () => {
      active = false
    }
  }, [id, token])

  if (loading) {
    return (
      <main className="memory-page">
        <div className="state-card">
          <div className="spinner" />
          <p>Loading reflection...</p>
        </div>
        <style>{styles}</style>
      </main>
    )
  }

  if (error || !memory) {
    return (
      <main className="memory-page">
        <div className="state-card error">
          <h1>Could not load reflection</h1>
          <p>{error || 'Reflection not found.'}</p>
          <Link href="/library" className="action-link">Back to Library</Link>
        </div>
        <style>{styles}</style>
      </main>
    )
  }

  const primaryEmotion = memory.feelings[0]?.primary_emotion || 'neutral'
  const accent = EMOTION_COLORS[primaryEmotion] || EMOTION_COLORS.neutral

  return (
    <main className="memory-page">
      <header className="memory-header">
        <Link href="/library" className="back-link">← Library</Link>
        <span className="eyebrow">Aimee reflection</span>
      </header>

      <article className="memory-card" style={{ borderColor: accent }}>
        <div className="accent-bar" style={{ background: accent }} />
        <div className="memory-body">
          <h1>{memory.title || 'Untitled reflection'}</h1>
          <p className="meta">
            {formatDate(memory.created_at || memory.occurred_at)}
          </p>

          {memory.narrative && (
            <section>
              <h2>What you saved</h2>
              <p>{memory.narrative}</p>
            </section>
          )}

          {memory.feelings.length > 0 && (
            <section>
              <h2>Feelings</h2>
              <div className="chips">
                {memory.feelings.map((feeling) => (
                  <span
                    key={feeling.id}
                    className="chip"
                    style={{ borderColor: EMOTION_COLORS[feeling.primary_emotion] || accent }}
                  >
                    {feeling.label} ({feeling.intensity}/10)
                  </span>
                ))}
              </div>
            </section>
          )}

          {memory.needs.length > 0 && (
            <section>
              <h2>Needs</h2>
              <div className="chips">
                {memory.needs.map((need) => (
                  <span key={need.id} className="chip">{need.name}</span>
                ))}
              </div>
            </section>
          )}

          {memory.entities.length > 0 && (
            <section>
              <h2>People or contexts</h2>
              <div className="chips">
                {memory.entities.map((entity) => (
                  <span key={entity.id} className="chip">{entity.canonical_name}</span>
                ))}
              </div>
            </section>
          )}

          {memory.topics.length > 0 && (
            <section>
              <h2>Themes</h2>
              <div className="chips">
                {memory.topics.map((topic) => (
                  <span key={topic.id} className="chip">{topic.title}</span>
                ))}
              </div>
            </section>
          )}
        </div>
      </article>

      <style>{styles}</style>
    </main>
  )
}

const styles = `
  .memory-page {
    min-height: 100vh;
    background: var(--bg-deep);
    padding: 24px 16px 48px;
  }

  .memory-header,
  .memory-card,
  .state-card {
    max-width: 760px;
    margin: 0 auto;
  }

  .memory-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .back-link,
  .action-link {
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
  }

  .eyebrow {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }

  .memory-card,
  .state-card {
    background: var(--card-solid);
    border: 1px solid var(--border-subtle);
    border-radius: 24px;
    box-shadow: var(--shadow-card);
    overflow: hidden;
  }

  .accent-bar {
    height: 8px;
  }

  .memory-body {
    padding: 28px 24px 24px;
  }

  h1 {
    margin: 0 0 8px;
    font-size: clamp(1.6rem, 4vw, 2.2rem);
    color: var(--text);
  }

  h2 {
    margin: 0 0 10px;
    font-size: 0.95rem;
    color: var(--text);
  }

  section + section {
    margin-top: 22px;
  }

  p {
    margin: 0;
    color: var(--text-muted);
    line-height: 1.65;
  }

  .meta {
    margin-bottom: 20px;
    font-size: 0.9rem;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
    font-size: 0.88rem;
  }

  .state-card {
    padding: 32px 24px;
    text-align: center;
  }

  .spinner {
    width: 30px;
    height: 30px;
    margin: 0 auto 12px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .error h1 {
    font-size: 1.2rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`

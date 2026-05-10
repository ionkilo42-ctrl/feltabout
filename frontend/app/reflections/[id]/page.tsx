"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { apiUrl } from '@/lib/api'
import { useAuthStore } from '@/store/sessionStore'

interface ReflectionOutput {
  emotions?: string[]
  reframing?: string
  message_draft?: string
  analysis?: string
}

interface Reflection {
  id: string
  title: string
  situation: string
  feelings: string
  interpretation: string
  needs: string
  fears: string
  desired_outcome: string
  message_draft: string
  status: string
  created_at: string
  output: ReflectionOutput | null
}

export default function ReflectionDetailPage() {
  const params = useParams()
  const router = useRouter()
  const token = useAuthStore(s => s.token)
  const id = params.id as string

  const [reflection, setReflection] = useState<Reflection | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !id) return

    fetch(apiUrl(`/reflections/${id}`), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Reflection not found')
        return res.json()
      })
      .then(data => {
        setReflection(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : 'Failed to load')
        setLoading(false)
      })
  }, [id, token])

  if (loading) {
    return (
      <div className="result-container">
        <div className="loading-card">
          <div className="spinner" />
          <p>Loading your reflection...</p>
        </div>
        <style>{styles}</style>
      </div>
    )
  }

  if (error || !reflection) {
    return (
      <div className="result-container">
        <div className="error-card">
          <h2>Could not load reflection</h2>
          <p>{error || 'Reflection not found.'}</p>
          <Link href="/library" className="btn-secondary">Back to Library</Link>
        </div>
        <style>{styles}</style>
      </div>
    )
  }

  const output = reflection.output || {}

  return (
    <main className="result-container">
      <header className="result-header">
        <Link href="/library" className="back-link">← Library</Link>
        <div className="header-actions">
          {reflection.status === 'draft' && (
            <button
              className="btn-generate"
              onClick={async () => {
                if (!token) return
                const res = await fetch(apiUrl(`/reflections/${id}/generate`), {
                  method: 'POST',
                  headers: { Authorization: `Bearer ${token}` },
                })
                if (res.ok) {
                  const updated = await res.json()
                  setReflection(prev => prev ? { ...prev, ...updated } : prev)
                }
              }}
            >
              Generate plan
            </button>
          )}
        </div>
      </header>

      <div className="result-content">
        {/* Reflection context */}
        <section className="context-section">
          <h1 className="reflection-title">
            {reflection.title || 'Your reflection'}
          </h1>
          {reflection.situation && (
            <p className="context-text">{reflection.situation}</p>
          )}
        </section>

        {/* AI Output */}
        {output && (
          <div className="output-card">
            <div className="output-header">
              <span className="output-icon">✨</span>
              <h2>Your reflection</h2>
            </div>

            {output.emotions && output.emotions.length > 0 && (
              <div className="output-section">
                <h3>What you're carrying</h3>
                <div className="emotion-tags">
                  {output.emotions.map((e, i) => (
                    <span key={i} className="emotion-tag">{e}</span>
                  ))}
                </div>
              </div>
            )}

            {output.reframing && (
              <div className="output-section">
                <h3>What might be happening</h3>
                <p className="output-text">{output.reframing}</p>
              </div>
            )}

            {output.analysis && (
              <div className="output-section">
                <h3>Where things could go</h3>
                <p className="output-text">{output.analysis}</p>
              </div>
            )}

            {output.message_draft && (
              <div className="output-section draft-section">
                <h3>A calmer opening line</h3>
                <blockquote className="message-draft">
                  {output.message_draft}
                </blockquote>
              </div>
            )}
          </div>
        )}

        {/* Your answers (context for the output) */}
        <section className="answers-section">
          <h3 className="section-label">What you shared</h3>
          {reflection.feelings && (
            <div className="answer-block">
              <span className="answer-label">How you feel</span>
              <p>{reflection.feelings}</p>
            </div>
          )}
          {reflection.interpretation && (
            <div className="answer-block">
              <span className="answer-label">Their perspective</span>
              <p>{reflection.interpretation}</p>
            </div>
          )}
          {reflection.needs && (
            <div className="answer-block">
              <span className="answer-label">What you need</span>
              <p>{reflection.needs}</p>
            </div>
          )}
          {reflection.fears && (
            <div className="answer-block">
              <span className="answer-label">What you're worried about</span>
              <p>{reflection.fears}</p>
            </div>
          )}
        </section>

        {/* Actions */}
        <div className="result-actions">
          <Link href="/reflections/new" className="btn-primary">
            Start a new reflection
          </Link>
          <Link href="/session" className="btn-secondary">
            Start a conversation
          </Link>
        </div>
      </div>

      <style>{styles}</style>
    </main>
  )
}

const styles = `
  .result-container {
    min-height: 100vh;
    background: var(--bg-deep);
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 24px 32px;
    border-bottom: 1px solid var(--border-subtle);
  }

  .back-link {
    font-size: 14px;
    color: var(--text-muted);
    text-decoration: none;
    transition: color 0.15s;
  }

  .back-link:hover {
    color: var(--text);
  }

  .header-actions {
    display: flex;
    gap: 8px;
  }

  .btn-generate {
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: white;
    color: var(--text);
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-generate:hover {
    background: var(--bg-deep);
  }

  .result-content {
    max-width: 600px;
    margin: 0 auto;
    padding: 32px 24px 64px;
  }

  .context-section {
    margin-bottom: 32px;
  }

  .reflection-title {
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.02em;
    margin-bottom: 12px;
  }

  .context-text {
    font-size: 1rem;
    color: var(--text-muted);
    line-height: 1.6;
  }

  .output-card {
    background: white;
    border-radius: 20px;
    border: 1px solid var(--border-subtle);
    padding: 28px;
    margin-bottom: 32px;
    box-shadow: var(--shadow-card);
  }

  .output-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 24px;
  }

  .output-icon {
    font-size: 20px;
  }

  .output-header h2 {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
  }

  .output-section {
    margin-bottom: 20px;
  }

  .output-section:last-child {
    margin-bottom: 0;
  }

  .output-section h3 {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-quiet);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
  }

  .emotion-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .emotion-tag {
    padding: 5px 12px;
    background: var(--accent-soft, #e0f7f5);
    color: var(--accent, #33d6c8);
    border-radius: 999px;
    font-size: 13px;
    font-weight: 500;
  }

  .output-text {
    font-size: 15px;
    color: var(--text-soft);
    line-height: 1.65;
  }

  .draft-section {
    background: var(--bg-deep);
    border-radius: 12px;
    padding: 18px 20px;
    margin-top: 16px;
  }

  .message-draft {
    font-size: 15px;
    color: var(--text);
    line-height: 1.65;
    margin: 0;
    font-style: normal;
    border: none;
    padding: 0;
  }

  .answers-section {
    margin-bottom: 32px;
  }

  .section-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-quiet);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 16px;
  }

  .answer-block {
    padding: 14px 0;
    border-bottom: 1px solid var(--border-subtle);
  }

  .answer-block:last-child {
    border-bottom: none;
  }

  .answer-label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-quiet);
    margin-bottom: 6px;
  }

  .answer-block p {
    font-size: 14px;
    color: var(--text-soft);
    line-height: 1.6;
    margin: 0;
  }

  .result-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .btn-primary {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 52px;
    padding: 1rem 1.5rem;
    border: none;
    border-radius: 999px;
    background: var(--gradient-core);
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
  }

  .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(51, 214, 200, 0.35);
  }

  .btn-secondary {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 48px;
    padding: 0.875rem 1.5rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: transparent;
    color: var(--text-soft);
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.2s;
  }

  .btn-secondary:hover {
    background: white;
    border-color: var(--text-quiet);
  }

  .loading-card, .error-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    gap: 16px;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .loading-card p, .error-card p {
    color: var(--text-muted);
    font-size: 15px;
  }

  .error-card h2 {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text);
  }
`
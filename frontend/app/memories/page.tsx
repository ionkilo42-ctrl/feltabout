"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getV2Memories, EMOTION_COLORS, Memory } from '../../lib/v2-api'

// Empty state component
function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">💭</div>
      <h3 className="empty-title">Your memories will appear here</h3>
      <p className="empty-description">
        As you reflect with Aimee, your emotional memories will collect here. 
        Each one tells a piece of your story.
      </p>
      <Link href="/aimee" className="empty-action">
        Start reflecting
      </Link>
    </div>
  )
}

// Loading state
function LoadingState() {
  return (
    <div className="loading-state">
      <div className="loading-spinner" />
      <p>Loading your memories...</p>
    </div>
  )
}

// Error state
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="error-state">
      <div className="error-icon">⚠️</div>
      <p className="error-message">{message}</p>
      <button className="retry-btn" onClick={onRetry}>
        Try again
      </button>
    </div>
  )
}

export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null)
  
  const fetchMemories = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getV2Memories()
      setMemories(data)
    } catch (err) {
      console.error('Failed to fetch memories:', err)
      setError('Could not load memories. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    fetchMemories()
  }, [])
  
  // Get primary emotion from memory
  const getPrimaryEmotion = (memory: Memory): string => {
    return memory.feelings?.[0]?.primary_emotion || 'neutral'
  }
  
  // Format time ago
  const formatTimeAgo = (dateStr: string): string => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }
  
  return (
    <main className="memories-page">
      {/* Header */}
      <header className="page-header">
        <Link href="/" className="back-link">
          <span className="back-arrow">←</span>
          <img src="/logo.png" alt="Feltabout" className="header-logo" />
        </Link>
        <div className="header-title">
          <h1>Memories</h1>
          <p>Your emotional history</p>
        </div>
        <Link href="/aimee" className="header-action">+ New</Link>
      </header>

      {/* Content */}
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={fetchMemories} />}
      {!loading && !error && memories.length === 0 && <EmptyState />}
      {!loading && !error && memories.length > 0 && (
        <>
          {/* Memory count */}
          <div className="memory-count">
            <span>{memories.length} memory{memories.length !== 1 ? 'ies' : ''}</span>
          </div>

          {/* Memory list */}
          <section className="memories-list">
            {memories.map((memory) => (
              <button
                key={memory.id}
                className="memory-card"
                onClick={() => setSelectedMemory(memory)}
              >
                <div className="memory-indicator">
                  <div
                    className="memory-dot"
                    style={{ background: EMOTION_COLORS[getPrimaryEmotion(memory)] }}
                  />
                </div>
                <div className="memory-content">
                  <h3 className="memory-title">{memory.title}</h3>
                  <div className="memory-meta">
                    {/* Linked entity */}
                    {memory.entities?.[0] && (
                      <>
                        <Link
                          href={`/entities?name=${encodeURIComponent(memory.entities[0].canonical_name)}`}
                          className="memory-entity"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {memory.entities[0].canonical_name}
                        </Link>
                        <span className="memory-sep">·</span>
                      </>
                    )}
                    <span className="memory-time">
                      {memory.occurred_at ? formatTimeAgo(memory.occurred_at) : formatTimeAgo(memory.created_at)}
                    </span>
                  </div>
                  <div className="memory-feelings">
                    {memory.feelings?.slice(0, 4).map((f, i) => (
                      <span key={i} className="feeling-tag">
                        {f.label}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="memory-intensity">
                  <div
                    className="intensity-ring"
                    style={{ '--ring-color': EMOTION_COLORS[getPrimaryEmotion(memory)] } as React.CSSProperties}
                  >
                    <span>{memory.feelings?.[0]?.intensity || 5}</span>
                  </div>
                </div>
              </button>
            ))}
          </section>
        </>
      )}

      {/* Navigation hints */}
      <section className="nav-hints">
        <p className="hints-text">Continue exploring</p>
        <div className="hints-links">
          <Link href="/feel-flow" className="hint-link">
            <span>📊</span> Feel Flow
          </Link>
          <Link href="/entities" className="hint-link">
            <span>👤</span> Entities
          </Link>
          <Link href="/feel-map" className="hint-link">
            <span>🗺️</span> Feel Map
          </Link>
        </div>
      </section>

      {/* Trust footer */}
      <footer className="page-footer">
        <div className="trust-pill">
          <span>🔒</span>
          <span>Private by default. Shared only when you choose.</span>
        </div>
      </footer>

      {/* Memory detail modal */}
      {selectedMemory && (
        <div className="modal-overlay" onClick={() => setSelectedMemory(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div
                className="modal-emotion-bar"
                style={{ background: EMOTION_COLORS[getPrimaryEmotion(selectedMemory)] }}
              />
              <div className="modal-header-content">
                <h2>{selectedMemory.title}</h2>
                <span className="modal-time">
                  {selectedMemory.occurred_at ? formatTimeAgo(selectedMemory.occurred_at) : formatTimeAgo(selectedMemory.created_at)}
                </span>
              </div>
              <button className="modal-close" onClick={() => setSelectedMemory(null)}>
                ×
              </button>
            </div>

            <div className="modal-body">
              {/* About - Linked */}
              {selectedMemory.entities?.[0] && (
                <div className="modal-section">
                  <span className="modal-label">About</span>
                  <Link
                    href={`/entities?name=${encodeURIComponent(selectedMemory.entities[0].canonical_name)}`}
                    className="modal-entity-link"
                  >
                    <span>👤</span> {selectedMemory.entities[0].canonical_name}
                  </Link>
                </div>
              )}

              {/* Primary feeling */}
              {selectedMemory.feelings?.[0] && (
                <div className="modal-section">
                  <span className="modal-label">Primary feeling</span>
                  <div className="modal-feeling">
                    <div
                      className="feeling-dot"
                      style={{ background: EMOTION_COLORS[getPrimaryEmotion(selectedMemory)] }}
                    />
                    <span>{selectedMemory.feelings[0].label}</span>
                    <span className="feeling-intensity">({selectedMemory.feelings[0].intensity}/10)</span>
                  </div>
                </div>
              )}

              {/* All feelings */}
              {selectedMemory.feelings && selectedMemory.feelings.length > 0 && (
                <div className="modal-section">
                  <span className="modal-label">All feelings</span>
                  <div className="modal-feelings">
                    {selectedMemory.feelings.map((f, i) => (
                      <span key={i} className="modal-feeling-tag">{f.label}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Needs - Linked */}
              {selectedMemory.needs && selectedMemory.needs.length > 0 && (
                <div className="modal-section">
                  <span className="modal-label">Needs</span>
                  <div className="modal-needs">
                    {selectedMemory.needs.map((n, i) => (
                      <Link
                        key={i}
                        href={`/needs?name=${encodeURIComponent(n.name)}`}
                        className="need-tag"
                      >
                        {n.name}
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Topics */}
              {selectedMemory.topics && selectedMemory.topics.length > 0 && (
                <div className="modal-section">
                  <span className="modal-label">Topics</span>
                  <span className="modal-value">{selectedMemory.topics.map(t => t.title).join(', ')}</span>
                </div>
              )}
            </div>

            <div className="modal-actions">
              <Link href="/aimee" className="modal-btn-primary">
                Reflect on this
              </Link>
              <button className="modal-btn-secondary" onClick={() => setSelectedMemory(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .memories-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          padding: 0 clamp(1.5rem, 5vw, 2rem);
          max-width: 640px;
          margin: 0 auto;
          width: 100%;
        }

        /* Header */
        .page-header {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1.25rem 0;
          border-bottom: 1px solid var(--border-subtle);
        }

        .back-link {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          text-decoration: none;
          flex-shrink: 0;
        }

        .back-arrow {
          font-size: 1.25rem;
          color: var(--text-muted);
          font-weight: 300;
        }

        .header-logo {
          height: 26px;
          width: auto;
        }

        .header-title {
          flex: 1;
          min-width: 0;
        }

        .header-title h1 {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text);
          margin: 0;
        }

        .header-title p {
          font-size: 0.75rem;
          color: var(--text-muted);
          margin: 0.15rem 0 0;
        }

        .header-action {
          display: inline-flex;
          align-items: center;
          min-height: 36px;
          padding: 0.5rem 1rem;
          border-radius: 999px;
          background: var(--gradient-core);
          color: white;
          font-size: 0.85rem;
          font-weight: 600;
          text-decoration: none;
          box-shadow: 0 2px 10px rgba(51, 214, 200, 0.2);
          flex-shrink: 0;
        }

        /* Loading state */
        .loading-state {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 3rem;
          gap: 1rem;
        }

        .loading-spinner {
          width: 32px;
          height: 32px;
          border: 3px solid var(--border);
          border-top-color: var(--accent);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .loading-state p {
          color: var(--text-muted);
          font-size: 0.9rem;
        }

        /* Error state */
        .error-state {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          padding: 3rem 1.5rem;
          gap: 1rem;
        }

        .error-icon {
          font-size: 2.5rem;
          opacity: 0.7;
        }

        .error-message {
          color: var(--text-muted);
          font-size: 0.9rem;
        }

        .retry-btn {
          padding: 0.625rem 1.25rem;
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 999px;
          color: var(--text-soft);
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-soft);
        }

        .retry-btn:hover {
          background: var(--card-solid);
          border-color: var(--accent-border);
          color: var(--accent);
        }

        /* Empty state */
        .empty-state {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          padding: 3rem 1.5rem;
          animation: fadeIn 0.4s var(--ease-soft);
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .empty-icon {
          font-size: 3.5rem;
          margin-bottom: 1.25rem;
          opacity: 0.7;
        }

        .empty-title {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text);
          margin: 0 0 0.75rem;
        }

        .empty-description {
          font-size: 0.9rem;
          color: var(--text-muted);
          margin: 0 0 1.5rem;
          max-width: 280px;
          line-height: 1.6;
        }

        .empty-action {
          display: inline-flex;
          align-items: center;
          min-height: 48px;
          padding: 0 1.75rem;
          border-radius: 999px;
          background: var(--gradient-core);
          color: white;
          font-size: 0.9rem;
          font-weight: 600;
          text-decoration: none;
          box-shadow: 0 4px 16px rgba(51, 214, 200, 0.25);
        }

        /* Memory count */
        .memory-count {
          padding: 1.25rem 0 0.75rem;
        }

        .memory-count span {
          font-size: 0.8rem;
          color: var(--text-quiet);
          font-weight: 500;
        }

        /* Memory list */
        .memories-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          padding-bottom: 1.5rem;
        }

        .memory-card {
          display: flex;
          align-items: flex-start;
          gap: 1rem;
          padding: 1.25rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 20px;
          text-align: left;
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-soft);
          width: 100%;
        }

        .memory-card:hover {
          background: var(--card-solid);
          border-color: var(--border);
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
        }

        .memory-indicator {
          padding-top: 0.2rem;
        }

        .memory-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .memory-content {
          flex: 1;
          min-width: 0;
        }

        .memory-title {
          font-size: 0.95rem;
          font-weight: 600;
          color: var(--text);
          margin: 0 0 0.35rem;
          line-height: 1.3;
        }

        .memory-meta {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          margin-bottom: 0.5rem;
          flex-wrap: wrap;
        }

        .memory-entity {
          font-size: 0.8rem;
          color: var(--accent);
          font-weight: 500;
          text-decoration: none;
          transition: opacity var(--duration-fast) var(--ease-soft);
        }

        .memory-entity:hover {
          opacity: 0.8;
        }

        .memory-sep {
          color: var(--text-quiet);
          font-size: 0.75rem;
        }

        .memory-time {
          font-size: 0.75rem;
          color: var(--text-quiet);
        }

        .memory-feelings {
          display: flex;
          flex-wrap: wrap;
          gap: 0.35rem;
        }

        .feeling-tag {
          font-size: 0.7rem;
          color: var(--text-muted);
          padding: 0.2rem 0.5rem;
          background: var(--bg-soft);
          border-radius: 999px;
        }

        .memory-intensity {
          flex-shrink: 0;
        }

        .intensity-ring {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          border: 3px solid var(--ring-color);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--text-soft);
        }

        /* Navigation hints */
        .nav-hints {
          padding: 1.5rem 0;
          text-align: center;
        }

        .hints-text {
          font-size: 0.8rem;
          color: var(--text-quiet);
          margin: 0 0 1rem;
        }

        .hints-links {
          display: flex;
          justify-content: center;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .hint-link {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.5rem 1rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 500;
          color: var(--text-soft);
          text-decoration: none;
          transition: all var(--duration-fast) var(--ease-soft);
        }

        .hint-link:hover {
          background: var(--card-solid);
          border-color: var(--accent-border);
          color: var(--accent);
          transform: translateY(-2px);
        }

        /* Footer */
        .page-footer {
          padding: 1rem 0 2rem;
          display: flex;
          justify-content: center;
        }

        .trust-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 500;
          color: var(--text-soft);
        }

        /* Modal */
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.25);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: flex-end;
          justify-content: center;
          z-index: 100;
          padding: 1rem;
          animation: overlayIn 0.2s var(--ease-soft);
        }

        @keyframes overlayIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .modal {
          background: var(--card-solid);
          border-radius: 24px 24px 0 0;
          width: 100%;
          max-width: 500px;
          max-height: 85vh;
          overflow-y: auto;
          animation: modalSlideUp 0.3s var(--ease-spring);
        }

        @keyframes modalSlideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }

        .modal-header {
          position: relative;
          padding: 1.5rem;
          border-bottom: 1px solid var(--border-subtle);
        }

        .modal-emotion-bar {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          border-radius: 24px 24px 0 0;
        }

        .modal-header-content {
          padding-top: 0.5rem;
        }

        .modal-header-content h2 {
          font-size: 1.125rem;
          font-weight: 600;
          color: var(--text);
          margin: 0 0 0.25rem;
        }

        .modal-time {
          font-size: 0.8rem;
          color: var(--text-muted);
        }

        .modal-close {
          position: absolute;
          top: 1.25rem;
          right: 1.25rem;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          border: none;
          background: var(--bg-soft);
          color: var(--text-muted);
          font-size: 1.25rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .modal-body {
          padding: 1.25rem 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .modal-section {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .modal-label {
          font-size: 0.7rem;
          font-weight: 600;
          color: var(--text-quiet);
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        .modal-entity-link {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.9rem;
          color: var(--accent);
          font-weight: 500;
          text-decoration: none;
        }

        .modal-entity-link:hover {
          opacity: 0.8;
        }

        .modal-value {
          font-size: 0.9rem;
          color: var(--text-soft);
        }

        .modal-feeling {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.9rem;
          font-weight: 500;
          color: var(--text);
          text-transform: capitalize;
        }

        .feeling-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .feeling-intensity {
          font-size: 0.8rem;
          font-weight: 400;
          color: var(--text-muted);
        }

        .modal-feelings {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .modal-feeling-tag {
          font-size: 0.8rem;
          padding: 0.3rem 0.75rem;
          background: var(--bg-soft);
          border-radius: 999px;
          color: var(--text-soft);
          text-transform: capitalize;
        }

        .modal-needs {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .need-tag {
          font-size: 0.8rem;
          padding: 0.3rem 0.75rem;
          background: var(--accent-soft);
          border: 1px solid var(--accent-border);
          border-radius: 999px;
          color: var(--accent);
          font-weight: 500;
          text-decoration: none;
          transition: all var(--duration-fast) var(--ease-soft);
        }

        .need-tag:hover {
          background: var(--accent);
          color: white;
        }

        .modal-actions {
          display: flex;
          gap: 0.75rem;
          padding: 1.25rem 1.5rem;
          border-top: 1px solid var(--border-subtle);
        }

        .modal-btn-primary {
          flex: 2;
          min-height: 44px;
          border: none;
          border-radius: 999px;
          background: var(--gradient-core);
          color: white;
          font-size: 0.875rem;
          font-weight: 600;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 2px 12px rgba(51, 214, 200, 0.2);
        }

        .modal-btn-secondary {
          flex: 1;
          min-height: 44px;
          border: 1px solid var(--border);
          border-radius: 999px;
          background: var(--card);
          color: var(--text-soft);
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
        }
      `}</style>
    </main>
  )
}
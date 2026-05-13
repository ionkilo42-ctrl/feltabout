'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useAuthStore } from '@/store/sessionStore'

interface LibraryItem {
  type: 'reflection' | 'conversation'
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

  const filtered = filter === 'all' ? items : items.filter(i => i.type === filter)

  const statusLabel = (type: string, status: string) => {
    if (type === 'reflection') {
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
    <main className="app">
      <header className="app-header">
        <div className="header-left">
          <Link href="/" className="brand-lockup" aria-label="Feltabout home">
            <img className="brand-mark-sm" src="/logo.png" alt="Feltabout" />
          </Link>
          <div className="page-title-group">
            <Link href="/" className="back-link">← Back</Link>
            <h1>Library</h1>
          </div>
        </div>
        <div className="header-actions">
          <Link href="/session" className="btn-primary">
            New reflection
          </Link>
        </div>
      </header>

      <div className="library-container">
        {/* Filter tabs */}
        <div className="filter-bar">
          {(['all', 'reflection', 'conversation'] as Filter[]).map(f => (
            <button
              key={f}
              className={`filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f === 'reflection' ? 'Reflections' : 'Conversations'}
              {f !== 'all' && (
                <span className="filter-count">
                  {items.filter(i => i.type === f).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Patterns section */}
        {(patterns.length > 0 || patternsLoading) && (
          <div className="patterns-section">
            <div className="patterns-header">
              <h3>Patterns you may notice</h3>
              <span className="patterns-privacy">Only you can see these patterns.</span>
            </div>

            {patternsLoading ? (
              <div className="patterns-loading">
                <div className="spinner-small" />
              </div>
            ) : (
              <div className="patterns-list">
                {patterns.map((p, i) => (
                  <div key={i} className={`pattern-card pattern-${p.confidence}`}>
                    <div className="pattern-insight">{p.insight}</div>
                    {p.confidence === 'low' && (
                      <div className="pattern-tentative">This may be showing up…</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {patterns.length === 0 && !patternsLoading && (
          <div className="patterns-empty">
            <p>As you save more reflections, Feltabout can help surface recurring themes gently.</p>
            <span className="patterns-privacy-note">Only you can see these patterns.</span>
          </div>
        )}

        {/* Content */}
        {loading && (
          <div className="library-loading">
            <div className="spinner" />
            <p>Loading your library...</p>
          </div>
        )}

        {error && (
          <div className="library-empty">
            <p className="library-error">{error}</p>
            {error.includes('sign in') && (
              <Link href="/login" className="btn-primary">Sign in</Link>
            )}
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="library-empty">
            <div className="empty-icon">
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
          <div className="library-list">
            {filtered.map(item => (
              <Link
                key={item.id}
                href={item.type === 'reflection' ? `/reflections/${item.id}` : `/session`}
                className="library-card"
              >
                <div className="card-icon">
                  {item.type === 'reflection' ? '📝' : '💬'}
                </div>
                <div className="card-body">
                  <div className="card-name">{item.name}</div>
                  <div className="card-meta">
                    <span className="card-date">{formatDate(item.created_at)}</span>
                    {item.type === 'conversation' && (
                      <span className="card-participants">
                        {item.participant_count} {item.participant_count === 1 ? 'person' : 'people'}
                      </span>
                    )}
                  </div>
                </div>
                <div className="card-right">
                  <span className={`status-badge status-${item.status}`}>
                    {statusLabel(item.type, item.status)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .library-container {
          max-width: 640px;
          margin: 0 auto;
          padding: 24px 16px;
        }

        .filter-bar {
          display: flex;
          gap: 4px;
          margin-bottom: 24px;
          border-bottom: 1px solid var(--color-border);
          padding-bottom: 12px;
        }

        .filter-btn {
          padding: 6px 14px;
          border-radius: 20px;
          border: none;
          background: transparent;
          color: var(--color-text-secondary, #6b7280);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.15s ease;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .filter-btn:hover {
          background: var(--color-bg-secondary, #f9fafb);
        }

        .filter-btn.active {
          background: var(--color-primary, #e07a5f);
          color: white;
        }

        .filter-count {
          font-size: 12px;
          opacity: 0.8;
        }

        .library-loading {
          text-align: center;
          padding: 60px 0;
          color: var(--color-text-secondary, #6b7280);
        }

        .library-loading .spinner {
          width: 32px;
          height: 32px;
          border: 3px solid var(--color-border, #e5e7eb);
          border-top-color: var(--color-primary, #e07a5f);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
          margin: 0 auto 12px;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .library-empty {
          text-align: center;
          padding: 60px 0;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .library-empty h2 {
          font-size: 20px;
          font-weight: 600;
          color: var(--color-text-primary, #111827);
          margin: 0 0 8px;
        }

        .library-empty p {
          color: var(--color-text-secondary, #6b7280);
          margin: 0 0 24px;
          line-height: 1.5;
        }

        .library-error {
          color: #dc2626;
          margin-bottom: 16px;
        }

        .library-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .library-card {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 16px;
          background: white;
          border-radius: 12px;
          border: 1px solid var(--color-border, #e5e7eb);
          text-decoration: none;
          transition: all 0.15s ease;
          box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }

        .library-card:hover {
          border-color: var(--color-primary, #e07a5f);
          box-shadow: 0 4px 12px rgba(224, 122, 95, 0.1);
          transform: translateY(-1px);
        }

        .card-icon {
          font-size: 24px;
          flex-shrink: 0;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--color-bg-secondary, #f9fafb);
          border-radius: 10px;
        }

        .card-body {
          flex: 1;
          min-width: 0;
        }

        .card-name {
          font-size: 15px;
          font-weight: 500;
          color: var(--color-text-primary, #111827);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 4px;
        }

        .card-meta {
          display: flex;
          gap: 12px;
          font-size: 12px;
          color: var(--color-text-secondary, #6b7280);
        }

        .card-participants {
          opacity: 0.8;
        }

        .card-right {
          flex-shrink: 0;
        }

        .status-badge {
          font-size: 11px;
          font-weight: 500;
          padding: 3px 9px;
          border-radius: 12px;
          text-transform: capitalize;
        }

        .status-draft { background: #fef3c7; color: #92400e; }
        .status-completed { background: #d1fae5; color: #065f46; }
        .status-archived { background: #f3f4f6; color: #6b7280; }
        .status-pending { background: #e0e7ff; color: #3730a3; }
        .status-active { background: #d1fae5; color: #065f46; }
        .status-complete { background: #f3f4f6; color: #6b7280; }

        .app-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1.5rem;
          padding: 1.5rem 0;
          border-bottom: 1px solid var(--color-border, #e5e7eb);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 1.5rem;
        }

        .brand-lockup {
          display: inline-flex;
          align-items: center;
        }

        .page-title-group {
          display: flex;
          align-items: baseline;
          gap: 0.75rem;
        }

        .back-link {
          font-size: 0.9rem;
          color: var(--color-text-secondary, #6b7280);
          text-decoration: none;
          transition: color 0.15s ease;
        }

        .back-link:hover {
          color: var(--color-text-primary, #111827);
        }

        .app-header h1 {
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--color-text-primary, #111827);
          margin: 0;
        }

        .header-actions {
          display: flex;
          gap: 8px;
        }

        .btn-primary {
          display: inline-flex;
          align-items: center;
          padding: 8px 16px;
          background: var(--color-primary, #e07a5f);
          color: white;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          text-decoration: none;
          transition: background 0.15s;
          border: none;
          cursor: pointer;
        }

        .btn-primary:hover {
          background: var(--color-primary-dark, #c9603f);
        }

        .btn-secondary {
          display: inline-flex;
          align-items: center;
          padding: 8px 16px;
          background: white;
          color: var(--color-primary, #e07a5f);
          border: 1px solid var(--color-primary, #e07a5f);
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          text-decoration: none;
          transition: all 0.15s;
        }

        .btn-secondary:hover {
          background: var(--color-bg-secondary, #f9fafb);
        }

        /* ── Patterns section ───────────────────────────────────────────── */
        .patterns-section {
          background: white;
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 24px;
        }

        .patterns-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }

        .patterns-header h3 {
          font-size: 15px;
          font-weight: 600;
          color: var(--color-text-primary, #111827);
          margin: 0;
        }

        .patterns-privacy {
          font-size: 12px;
          color: var(--color-text-secondary, #6b7280);
          font-style: italic;
        }

        .patterns-loading {
          display: flex;
          justify-content: center;
          padding: 12px 0;
        }

        .spinner-small {
          width: 20px;
          height: 20px;
          border: 2px solid var(--color-border, #e5e7eb);
          border-top-color: var(--color-primary, #e07a5f);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        .patterns-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .pattern-card {
          padding: 12px 16px;
          border-radius: 8px;
          border-left: 3px solid transparent;
        }

        .pattern-high {
          background: #f0fdf4;
          border-left-color: #16a34a;
        }

        .pattern-medium {
          background: #fefce8;
          border-left-color: #ca8a04;
        }

        .pattern-low {
          background: #f9fafb;
          border-left-color: #d1d5db;
        }

        .pattern-insight {
          font-size: 14px;
          color: var(--color-text-primary, #111827);
          line-height: 1.5;
        }

        .pattern-tentative {
          font-size: 12px;
          color: var(--color-text-secondary, #6b7280);
          margin-top: 4px;
          font-style: italic;
        }

        .patterns-empty {
          background: white;
          border: 1px dashed var(--color-border, #e5e7eb);
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 24px;
          text-align: center;
        }

        .patterns-empty p {
          font-size: 13px;
          color: var(--color-text-secondary, #6b7280);
          margin: 0 0 8px;
          line-height: 1.5;
        }

        .patterns-privacy-note {
          font-size: 11px;
          color: var(--color-text-secondary, #6b7280);
          font-style: italic;
        }
      `}</style>
    </main>
  )
}
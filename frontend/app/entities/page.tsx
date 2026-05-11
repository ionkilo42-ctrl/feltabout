"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getV2Entities, Entity } from '../../lib/v2-api'

// Empty state component
function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">👤</div>
      <h3 className="empty-title">People and places will appear here</h3>
      <p className="empty-description">
        As you reflect with Aimee, the people and things that matter to your emotional life will appear here.
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
      <p>Loading entities...</p>
    </div>
  )
}

// Error state
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="error-state">
      <div className="error-icon">⚠️</div>
      <p className="error-message">{message}</p>
      <button className="retry-btn" onClick={onRetry}>Try again</button>
    </div>
  )
}

// Entity type icon
function getEntityIcon(type: string): string {
  const icons: Record<string, string> = {
    person: '👤',
    place: '📍',
    organization: '🏢',
    topic: '💬',
    default: '🏷️',
  }
  return icons[type] || icons.default
}

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const fetchEntities = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getV2Entities()
      setEntities(data)
    } catch (err) {
      console.error('Failed to fetch entities:', err)
      setError('Could not load entities. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    fetchEntities()
  }, [])
  
  // Group entities by type
  const groupedEntities = entities.reduce((acc, entity) => {
    const type = entity.entity_type || 'other'
    if (!acc[type]) acc[type] = []
    acc[type].push(entity)
    return acc
  }, {} as Record<string, Entity[]>)
  
  return (
    <main className="entities-page">
      {/* Header */}
      <header className="page-header">
        <Link href="/" className="back-link">
          <span className="back-arrow">←</span>
          <img src="/logo.png" alt="Feltabout" className="header-logo" />
        </Link>
        <div className="header-title">
          <h1>Entities</h1>
          <p>People and places in your emotional world</p>
        </div>
        <div className="header-spacer" />
      </header>

      {/* Content */}
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={fetchEntities} />}
      {!loading && !error && entities.length === 0 && <EmptyState />}
      {!loading && !error && entities.length > 0 && (
        <div className="entities-content">
          {Object.entries(groupedEntities).map(([type, typeEntities]) => (
            <div key={type} className="entity-group">
              <h2 className="group-title">
                <span className="group-icon">{getEntityIcon(type)}</span>
                <span className="group-name">{type}</span>
                <span className="group-count">{typeEntities.length}</span>
              </h2>
              <div className="entity-list">
                {typeEntities.map((entity) => (
                  <Link
                    key={entity.id}
                    href={`/memories?entity=${encodeURIComponent(entity.canonical_name)}`}
                    className="entity-card"
                  >
                    <div className="entity-info">
                      <span className="entity-icon">{getEntityIcon(entity.entity_type)}</span>
                      <span className="entity-name">{entity.canonical_name}</span>
                    </div>
                    <span className="entity-type">{entity.entity_type}</span>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Navigation hints */}
      <section className="nav-hints">
        <p className="hints-text">Continue exploring</p>
        <div className="hints-links">
          <Link href="/memories" className="hint-link">
            <span>💭</span> Memories
          </Link>
          <Link href="/needs" className="hint-link">
            <span>🎯</span> Needs
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

      <style>{`
        .entities-page {
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

        .header-spacer {
          width: 60px;
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

        /* Entities content */
        .entities-content {
          padding: 1rem 0;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .entity-group {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .group-title {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--text-muted);
          text-transform: capitalize;
        }

        .group-icon {
          font-size: 1rem;
        }

        .group-name {
          flex: 1;
        }

        .group-count {
          padding: 0.2rem 0.5rem;
          background: var(--bg-soft);
          border-radius: 999px;
          font-size: 0.7rem;
        }

        .entity-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .entity-card {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 16px;
          text-decoration: none;
          transition: all var(--duration-fast) var(--ease-soft);
        }

        .entity-card:hover {
          background: var(--card-solid);
          border-color: var(--border);
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
        }

        .entity-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .entity-icon {
          font-size: 1.25rem;
        }

        .entity-name {
          font-size: 0.95rem;
          font-weight: 600;
          color: var(--text);
        }

        .entity-type {
          font-size: 0.75rem;
          color: var(--text-muted);
          text-transform: capitalize;
          padding: 0.25rem 0.5rem;
          background: var(--bg-soft);
          border-radius: 999px;
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
      `}</style>
    </main>
  )
}
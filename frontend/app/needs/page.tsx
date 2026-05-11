"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getV2Needs, Need } from '../../lib/v2-api'

// Empty state component
function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">🎯</div>
      <h3 className="empty-title">Your needs will appear here</h3>
      <p className="empty-description">
        As you reflect with Aimee, the underlying needs that arise from your feelings will appear here.
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
      <p>Loading needs...</p>
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

// Need card component
function NeedCard({ need }: { need: Need }) {
  // Common need categories
  const categories: Record<string, { icon: string; color: string }> = {
    autonomy: { icon: '🎯', color: '#B794F4' },
    connection: { icon: '💜', color: '#FF6B6B' },
    security: { icon: '🛡️', color: '#6B9FFF' },
    growth: { icon: '🌱', color: '#6BCB77' },
    meaning: { icon: '✨', color: '#FFD93D' },
    peace: { icon: '☁️', color: '#A3A3A3' },
    fairness: { icon: '⚖️', color: '#FFB347' },
    recognition: { icon: '🌟', color: '#FFD93D' },
    default: { icon: '🎯', color: '#6BCB77' },
  }
  
  // Determine category based on need name
  const getCategory = (name: string) => {
    const lower = name.toLowerCase()
    if (lower.includes('autonomy') || lower.includes('choice') || lower.includes('control')) return 'autonomy'
    if (lower.includes('connection') || lower.includes('love') || lower.includes('belonging')) return 'connection'
    if (lower.includes('security') || lower.includes('safety') || lower.includes('stability')) return 'security'
    if (lower.includes('growth') || lower.includes('learning') || lower.includes('development')) return 'growth'
    if (lower.includes('meaning') || lower.includes('purpose') || lower.includes('fulfillment')) return 'meaning'
    if (lower.includes('peace') || lower.includes('rest') || lower.includes('calm')) return 'peace'
    if (lower.includes('fairness') || lower.includes('justice') || lower.includes('equity')) return 'fairness'
    if (lower.includes('recognition') || lower.includes('appreciation') || lower.includes('value')) return 'recognition'
    return 'default'
  }
  
  const category = getCategory(need.name)
  const { icon, color } = categories[category]
  
  return (
    <Link
      href={`/memories?need=${encodeURIComponent(need.name)}`}
      className="need-card"
      style={{ borderLeftColor: color }}
    >
      <div className="need-icon" style={{ background: `${color}20` }}>
        {icon}
      </div>
      <div className="need-info">
        <span className="need-name">{need.name}</span>
        <span className="need-category">{category}</span>
      </div>
    </Link>
  )
}

export default function NeedsPage() {
  const [needs, setNeeds] = useState<Need[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const fetchNeeds = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getV2Needs()
      setNeeds(data)
    } catch (err) {
      console.error('Failed to fetch needs:', err)
      setError('Could not load needs. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    fetchNeeds()
  }, [])
  
  return (
    <main className="needs-page">
      {/* Header */}
      <header className="page-header">
        <Link href="/" className="back-link">
          <span className="back-arrow">←</span>
          <img src="/logo.png" alt="Feltabout" className="header-logo" />
        </Link>
        <div className="header-title">
          <h1>Needs</h1>
          <p>What matters to you</p>
        </div>
        <div className="header-spacer" />
      </header>

      {/* Content */}
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={fetchNeeds} />}
      {!loading && !error && needs.length === 0 && <EmptyState />}
      {!loading && !error && needs.length > 0 && (
        <div className="needs-content">
          <div className="needs-count">
            <span>{needs.length} need{needs.length !== 1 ? 's' : ''} identified</span>
          </div>
          
          <div className="needs-grid">
            {needs.map((need) => (
              <NeedCard key={need.id} need={need} />
            ))}
          </div>
        </div>
      )}

      {/* Navigation hints */}
      <section className="nav-hints">
        <p className="hints-text">Continue exploring</p>
        <div className="hints-links">
          <Link href="/memories" className="hint-link">
            <span>💭</span> Memories
          </Link>
          <Link href="/entities" className="hint-link">
            <span>👤</span> Entities
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
        .needs-page {
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

        /* Needs content */
        .needs-content {
          padding: 1rem 0;
        }

        .needs-count {
          padding-bottom: 1rem;
        }

        .needs-count span {
          font-size: 0.8rem;
          color: var(--text-quiet);
          font-weight: 500;
        }

        .needs-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 0.75rem;
        }

        .need-card {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-left: 4px solid;
          border-radius: 16px;
          text-decoration: none;
          transition: all var(--duration-fast) var(--ease-soft);
        }

        .need-card:hover {
          background: var(--card-solid);
          border-color: var(--border);
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
        }

        .need-icon {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          flex-shrink: 0;
        }

        .need-info {
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
        }

        .need-name {
          font-size: 0.95rem;
          font-weight: 600;
          color: var(--text);
        }

        .need-category {
          font-size: 0.7rem;
          color: var(--text-muted);
          text-transform: capitalize;
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
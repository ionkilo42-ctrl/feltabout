"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getFeelMap, EMOTION_COLORS, FeelMapResponse, EmotionGroup } from '../../lib/v2-api'

// Empty state component
function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">🗺️</div>
      <h3 className="empty-title">Your emotional landscape will appear here</h3>
      <p className="empty-description">
        As you reflect with Aimee, your Feel Map will show the composition of your emotional world.
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
      <p>Loading your Feel Map...</p>
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

// Emotion group card
function EmotionGroupCard({ group }: { group: EmotionGroup }) {
  const totalWeight = group.total_weight || 1
  
  return (
    <div className="emotion-group-card" style={{ borderLeftColor: group.color }}>
      <div className="group-header">
        <div className="group-color" style={{ background: group.color }} />
        <span className="group-emotion">{group.emotion}</span>
        <span className="group-count">{group.feelings?.length || 0}</span>
      </div>
      
      <div className="feelings-grid">
        {group.feelings?.slice(0, 6).map((feeling, i) => (
          <div key={i} className="feeling-chip" title={feeling.label}>
            <span className="chip-label">{feeling.label}</span>
            <span className="chip-intensity">{feeling.intensity}</span>
          </div>
        ))}
        {group.feelings && group.feelings.length > 6 && (
          <div className="feeling-chip more">
            <span className="chip-label">+{group.feelings.length - 6}</span>
          </div>
        )}
      </div>
    </div>
  )
}

// Treemap visualization
function EmotionTreemap({ data }: { data: FeelMapResponse }) {
  if (!data.emotion_groups || data.emotion_groups.length === 0) return null
  
  const maxWeight = Math.max(...data.emotion_groups.map(g => g.total_weight)) || 1
  
  return (
    <div className="treemap-container">
      {data.emotion_groups.map((group) => {
        const widthPct = (group.total_weight / maxWeight) * 100
        return (
          <div
            key={group.emotion}
            className="treemap-cell"
            style={{
              width: `${widthPct}%`,
              backgroundColor: `${group.color}20`,
              borderColor: group.color,
            }}
          >
            <div className="cell-content">
              <span className="cell-emotion">{group.emotion}</span>
              <span className="cell-weight">{group.total_weight}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function FeelMapPage() {
  const [data, setData] = useState<FeelMapResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [daysFilter, setDaysFilter] = useState<number>(30)
  
  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getFeelMap({ days: daysFilter })
      setData(result)
    } catch (err) {
      console.error('Failed to fetch feel map:', err)
      setError('Could not load your emotional landscape. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    fetchData()
  }, [daysFilter])
  
  const hasData = data && data.emotion_groups && data.emotion_groups.length > 0
  
  return (
    <main className="feel-map-page">
      {/* Header */}
      <header className="page-header">
        <Link href="/" className="back-link">
          <span className="back-arrow">←</span>
          <img src="/logo.png" alt="Feltabout" className="header-logo" />
        </Link>
        <div className="header-title">
          <h1>Feel Map</h1>
          <p>Your emotional landscape</p>
        </div>
        <div className="header-spacer" />
      </header>

      {/* Time filter */}
      <div className="filter-bar">
        <button
          className={`filter-btn ${daysFilter === 7 ? 'active' : ''}`}
          onClick={() => setDaysFilter(7)}
        >
          7 days
        </button>
        <button
          className={`filter-btn ${daysFilter === 30 ? 'active' : ''}`}
          onClick={() => setDaysFilter(30)}
        >
          30 days
        </button>
        <button
          className={`filter-btn ${daysFilter === 90 ? 'active' : ''}`}
          onClick={() => setDaysFilter(90)}
        >
          90 days
        </button>
      </div>

      {/* Content */}
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={fetchData} />}
      {!loading && !error && !hasData && <EmptyState />}
      {!loading && !error && hasData && (
        <>
          {/* Summary stats */}
          <div className="map-summary">
            <div className="summary-stat">
              <span className="stat-value">{data.dominant_emotion}</span>
              <span className="stat-label">dominant emotion</span>
            </div>
            <div className="summary-stat">
              <span className="stat-value">{data.total_feelings}</span>
              <span className="stat-label">total feelings</span>
            </div>
            <div className="summary-stat">
              <span className="stat-value">{data.average_intensity?.toFixed(1)}</span>
              <span className="stat-label">avg intensity</span>
            </div>
          </div>

          {/* Treemap visualization */}
          <section className="treemap-section">
            <h2 className="section-title">Emotion composition</h2>
            <EmotionTreemap data={data} />
          </section>

          {/* Emotion groups */}
          <section className="groups-section">
            <h2 className="section-title">By emotion</h2>
            <div className="groups-list">
              {data.emotion_groups?.map((group) => (
                <EmotionGroupCard key={group.emotion} group={group} />
              ))}
            </div>
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
          <Link href="/memories" className="hint-link">
            <span>💭</span> Memories
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
        .feel-map-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          padding: 0 clamp(1.5rem, 5vw, 2rem);
          max-width: 720px;
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

        /* Filter bar */
        .filter-bar {
          display: flex;
          gap: 0.5rem;
          padding: 1rem 0;
          justify-content: center;
        }

        .filter-btn {
          padding: 0.5rem 1rem;
          border: 1px solid var(--border);
          border-radius: 999px;
          background: var(--card);
          color: var(--text-muted);
          font-size: 0.8rem;
          font-weight: 500;
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-soft);
        }

        .filter-btn:hover {
          background: var(--card-solid);
          border-color: var(--accent-border);
          color: var(--accent);
        }

        .filter-btn.active {
          background: var(--gradient-core);
          border-color: transparent;
          color: white;
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

        /* Map summary */
        .map-summary {
          display: flex;
          gap: 1rem;
          padding: 1rem 0;
        }

        .summary-stat {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 1rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 16px;
        }

        .summary-stat .stat-value {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text);
          text-transform: capitalize;
        }

        .summary-stat .stat-label {
          font-size: 0.7rem;
          color: var(--text-muted);
          margin-top: 0.25rem;
        }

        /* Treemap */
        .treemap-section {
          padding: 1rem 0;
        }

        .section-title {
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--text);
          margin: 0 0 1rem;
        }

        .treemap-container {
          display: flex;
          gap: 0.5rem;
          padding: 1rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 20px;
          overflow: hidden;
        }

        .treemap-cell {
          flex: 1;
          min-height: 60px;
          border: 2px solid;
          border-radius: 12px;
          padding: 0.75rem;
          transition: all var(--duration-fast) var(--ease-soft);
        }

        .treemap-cell:hover {
          transform: scale(1.02);
        }

        .cell-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          text-align: center;
        }

        .cell-emotion {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--text);
          text-transform: capitalize;
        }

        .cell-weight {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-soft);
        }

        /* Groups section */
        .groups-section {
          padding: 1rem 0;
        }

        .groups-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .emotion-group-card {
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-left: 4px solid;
          border-radius: 16px;
          padding: 1rem;
        }

        .group-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
        }

        .group-color {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }

        .group-emotion {
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--text);
          text-transform: capitalize;
          flex: 1;
        }

        .group-count {
          font-size: 0.75rem;
          color: var(--text-muted);
          padding: 0.2rem 0.5rem;
          background: var(--bg-soft);
          border-radius: 999px;
        }

        .feelings-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .feeling-chip {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          padding: 0.3rem 0.75rem;
          background: var(--bg-soft);
          border-radius: 999px;
          font-size: 0.75rem;
        }

        .feeling-chip.more {
          background: var(--accent-soft);
          color: var(--accent);
        }

        .chip-label {
          color: var(--text-soft);
          text-transform: capitalize;
        }

        .chip-intensity {
          color: var(--text-muted);
          font-weight: 600;
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
"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getFeelFlow, EMOTION_COLORS, FeelFlowResponse, FeelFlowPoint } from '../../lib/v2-api'

// Empty state component
function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">📊</div>
      <h3 className="empty-title">Your emotional patterns will appear here</h3>
      <p className="empty-description">
        As you reflect with Aimee, your Feel Flow will reveal the rhythm of your emotional life over time.
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
      <p>Loading your Feel Flow...</p>
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

// Bar chart component
function EmotionBarChart({ data }: { data: FeelFlowPoint[] }) {
  if (!data || data.length === 0) return null
  
  // Find max value for scaling
  const maxValue = Math.max(
    ...data.flatMap(d => [d.joy, d.sadness, d.anger, d.fear, d.disgust])
  ) || 10
  
  const emotions = ['joy', 'sadness', 'anger', 'fear', 'disgust'] as const
  
  return (
    <div className="chart-container">
      <div className="chart-bars">
        {data.map((point, i) => (
          <div key={i} className="chart-column">
            <div className="chart-label">{point.date.slice(5)}</div>
            <div className="bar-group">
              {emotions.map(emotion => (
                <div
                  key={emotion}
                  className={`chart-bar ${emotion}`}
                  style={{
                    height: `${(point[emotion] / maxValue) * 100}%`,
                    backgroundColor: EMOTION_COLORS[emotion],
                  }}
                  title={`${emotion}: ${point[emotion]}`}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="chart-legend">
        {emotions.map(emotion => (
          <div key={emotion} className="legend-item">
            <div className="legend-color" style={{ background: EMOTION_COLORS[emotion] }} />
            <span className="legend-label">{emotion}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Stats summary
function StatsSummary({ data }: { data: FeelFlowResponse }) {
  const emotions = ['joy', 'sadness', 'anger', 'fear', 'disgust'] as const
  
  return (
    <div className="stats-grid">
      {emotions.map(emotion => (
        <div key={emotion} className="stat-card">
          <div className="stat-color" style={{ background: EMOTION_COLORS[emotion] }} />
          <div className="stat-content">
            <span className="stat-value">{data.emotion_totals?.[emotion] || 0}</span>
            <span className="stat-label">{emotion}</span>
          </div>
        </div>
      ))}
      <div className="stat-card accent">
        <div className="stat-content">
          <span className="stat-value">{data.average_intensity?.toFixed(1) || '—'}</span>
          <span className="stat-label">avg intensity</span>
        </div>
      </div>
    </div>
  )
}

export default function FeelFlowPage() {
  const [data, setData] = useState<FeelFlowResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [daysFilter, setDaysFilter] = useState<number>(30)
  
  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getFeelFlow({ days: daysFilter })
      setData(result)
    } catch (err) {
      console.error('Failed to fetch feel flow:', err)
      setError('Could not load your emotional patterns. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    fetchData()
  }, [daysFilter])
  
  const hasData = data && data.data && data.data.length > 0
  
  return (
    <main className="feel-flow-page">
      {/* Header */}
      <header className="page-header">
        <Link href="/" className="back-link">
          <span className="back-arrow">←</span>
          <img src="/logo.png" alt="Feltabout" className="header-logo" />
        </Link>
        <div className="header-title">
          <h1>Feel Flow</h1>
          <p>Your emotional rhythm over time</p>
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
          {/* Stats summary */}
          <StatsSummary data={data} />
          
          {/* Chart */}
          <section className="chart-section">
            <h2 className="section-title">Emotional distribution</h2>
            <EmotionBarChart data={data.data} />
          </section>
        </>
      )}

      {/* Navigation hints */}
      <section className="nav-hints">
        <p className="hints-text">Continue exploring</p>
        <div className="hints-links">
          <Link href="/feel-map" className="hint-link">
            <span>🗺️</span> Feel Map
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
        .feel-flow-page {
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

        /* Stats grid */
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 0.75rem;
          padding: 1rem 0;
        }

        .stat-card {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 16px;
        }

        .stat-card.accent {
          grid-column: span 1;
        }

        .stat-color {
          width: 8px;
          height: 32px;
          border-radius: 4px;
          flex-shrink: 0;
        }

        .stat-content {
          display: flex;
          flex-direction: column;
          gap: 0.15rem;
        }

        .stat-value {
          font-size: 1.125rem;
          font-weight: 700;
          color: var(--text);
        }

        .stat-label {
          font-size: 0.7rem;
          color: var(--text-muted);
          text-transform: capitalize;
        }

        /* Chart section */
        .chart-section {
          padding: 1.5rem 0;
        }

        .section-title {
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--text);
          margin: 0 0 1rem;
        }

        .chart-container {
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 20px;
          padding: 1.5rem;
        }

        .chart-bars {
          display: flex;
          align-items: flex-end;
          gap: 0.5rem;
          height: 200px;
          padding-bottom: 1.5rem;
          border-bottom: 1px solid var(--border-subtle);
        }

        .chart-column {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          height: 100%;
        }

        .chart-label {
          font-size: 0.65rem;
          color: var(--text-muted);
        }

        .bar-group {
          flex: 1;
          display: flex;
          align-items: flex-end;
          gap: 2px;
          width: 100%;
        }

        .chart-bar {
          flex: 1;
          border-radius: 3px 3px 0 0;
          min-height: 4px;
          transition: height 0.3s var(--ease-soft);
        }

        .chart-legend {
          display: flex;
          justify-content: center;
          gap: 1rem;
          flex-wrap: wrap;
          padding-top: 1rem;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 0.4rem;
        }

        .legend-color {
          width: 10px;
          height: 10px;
          border-radius: 3px;
        }

        .legend-label {
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
"use client"

import Link from 'next/link'

// Primary emotion colors
const EMOTION_COLORS = {
  joy: '#FFD93D',
  sadness: '#6B9FFF',
  anger: '#FF6B6B',
  fear: '#B794F4',
  disgust: '#6BCB77',
}

// Orb data for the emotional warehouse preview
const MOCK_ORBS = [
  { label: 'joy', color: EMOTION_COLORS.joy, size: 48, top: '15%', left: '20%' },
  { label: 'sadness', color: EMOTION_COLORS.sadness, size: 36, top: '25%', left: '55%' },
  { label: 'anger', color: EMOTION_COLORS.anger, size: 42, top: '45%', left: '35%' },
  { label: 'fear', color: EMOTION_COLORS.fear, size: 38, top: '60%', left: '65%' },
  { label: 'disgust', color: EMOTION_COLORS.disgust, size: 30, top: '70%', left: '25%' },
  { label: 'joy', color: EMOTION_COLORS.joy, size: 34, top: '35%', left: '70%' },
  { label: 'sadness', color: EMOTION_COLORS.sadness, size: 44, top: '55%', left: '45%' },
  { label: 'anger', color: EMOTION_COLORS.anger, size: 28, top: '75%', left: '55%' },
  { label: 'fear', color: EMOTION_COLORS.fear, size: 40, top: '20%', left: '40%' },
  { label: 'joy', color: EMOTION_COLORS.joy, size: 32, top: '80%', left: '40%' },
]

// Mock stats
const MOCK_STATS = [
  { label: 'Feelings tracked', value: '247', unit: 'this month' },
  { label: 'Top emotion', value: 'joy', unit: '', color: EMOTION_COLORS.joy },
  { label: 'Needs identified', value: '38', unit: 'unique needs' },
  { label: 'About', value: '12', unit: 'entities tracked' },
]

// Mock recent feelings
const MOCK_RECENT = [
  { feeling: 'grateful', about: 'Crystal', time: '2h ago', color: EMOTION_COLORS.joy },
  { feeling: 'anxious', about: 'work', time: '5h ago', color: EMOTION_COLORS.fear },
  { feeling: 'hurt', about: 'Sarah', time: '1d ago', color: EMOTION_COLORS.sadness },
  { feeling: 'frustrated', about: 'Starbucks', time: '2d ago', color: EMOTION_COLORS.anger },
]

export default function HomePage() {
  return (
    <main className="home">
      {/* Header */}
      <header className="home-header">
        <div className="brand-lockup">
          <img className="brand-mark" src="/logo.png" alt="Feltabout" />
        </div>
        <nav className="home-nav">
          <Link href="/aimee" className="nav-link">Aimee</Link>
          <Link href="/feel-flow" className="nav-link">Feel Flow</Link>
          <Link href="/memories" className="nav-link">Memories</Link>
          <Link href="/entities" className="nav-link">Entities</Link>
          <Link href="/needs" className="nav-link">Needs</Link>
          <Link href="/reflections/new" className="nav-cta">Reflect</Link>
        </nav>
      </header>

      {/* Hero */}
      <section className="hero-section">
        <div className="hero-orb-field">
          {MOCK_ORBS.map((orb, i) => (
            <div
              key={i}
              className="hero-orb"
              style={{
                width: orb.size,
                height: orb.size,
                background: orb.color,
                top: orb.top,
                left: orb.left,
                opacity: 0.7 + (i % 3) * 0.1,
              }}
            />
          ))}
        </div>
        <div className="hero-content">
          <h1 className="hero-headline">A place to master your emotions.</h1>
          <p className="hero-subtitle">
            Understand what you feel, what it's about, and what your feelings need.
          </p>
          <div className="hero-ctas">
            <Link href="/aimee" className="btn-primary">
              Talk to Aimee
            </Link>
            <Link href="/feel-flow" className="btn-secondary">
              See your Feel Flow
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Stats */}
      <section className="stats-section">
        <div className="stats-grid">
          {MOCK_STATS.map((stat) => (
            <div key={stat.label} className="stat-card">
              <div className="stat-value" style={stat.color ? { color: stat.color } : {}}>
                {stat.value}
              </div>
              <div className="stat-label">{stat.label}</div>
              {stat.unit && <div className="stat-unit">{stat.unit}</div>}
            </div>
          ))}
        </div>
      </section>

      {/* Recent Feelings */}
      <section className="recent-section">
        <h2 className="section-title">Recent feelings</h2>
        <div className="recent-list">
          {MOCK_RECENT.map((item, i) => (
            <div key={i} className="recent-item">
              <div className="recent-dot" style={{ background: item.color }} />
              <div className="recent-info">
                <span className="recent-feeling">{item.feeling}</span>
                <span className="recent-about"> about {item.about}</span>
              </div>
              <span className="recent-time">{item.time}</span>
            </div>
          ))}
        </div>
        <Link href="/memories" className="see-all-link">See all memories →</Link>
      </section>

      {/* Emotion Color Legend */}
      <section className="emotion-legend">
        <h2 className="section-title">Primary emotions</h2>
        <div className="emotion-pills">
          {Object.entries(EMOTION_COLORS).map(([emotion, color]) => (
            <span key={emotion} className="emotion-pill" style={{ '--emotion-color': color } as React.CSSProperties}>
              <span className="emotion-dot" style={{ background: color }} />
              {emotion}
            </span>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="home-footer">
        <p className="footer-copy">Your feelings belong to you.</p>
        <p className="footer-secondary">feltabout never sells your emotional data.</p>
      </footer>

      <style>{`
        .home {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 0 clamp(1.5rem, 5vw, 3rem);
          position: relative;
          overflow: hidden;
        }

        /* Header */
        .home-header {
          width: 100%;
          max-width: 1100px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 2rem 0 1.5rem;
        }

        .brand-mark {
          display: block;
          height: clamp(28px, 4vw, 40px);
          width: auto;
        }

        .home-nav {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .nav-link {
          font-size: 0.85rem;
          font-weight: 500;
          color: var(--text-soft);
          text-decoration: none;
          padding: 0.5rem 0.75rem;
          border-radius: 12px;
          transition: all var(--duration-fast) var(--ease-soft);
        }

        .nav-link:hover {
          background: var(--hover-bg);
          color: var(--text);
        }

        .nav-cta {
          display: inline-flex;
          align-items: center;
          min-height: 36px;
          padding: 0.5rem 1.25rem;
          border-radius: 999px;
          background: var(--gradient-core);
          color: #FFFFFF;
          font-size: 0.85rem;
          font-weight: 600;
          text-decoration: none;
          margin-left: 0.5rem;
          box-shadow: 0 2px 12px rgba(51, 214, 200, 0.2);
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .nav-cta:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(51, 214, 200, 0.35);
        }

        /* Hero */
        .hero-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          width: 100%;
          max-width: 640px;
          position: relative;
          padding: 3rem 0;
        }

        .hero-orb-field {
          position: absolute;
          top: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 400px;
          height: 300px;
          pointer-events: none;
          z-index: 0;
        }

        .hero-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(12px);
          animation: orb-float 6s ease-in-out infinite;
        }

        .hero-orb:nth-child(odd) { animation-delay: 0.5s; }
        .hero-orb:nth-child(3n) { animation-delay: 1s; }

        @keyframes orb-float {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(6px, -8px); }
        }

        .hero-content {
          position: relative;
          z-index: 1;
        }

        .hero-headline {
          font-size: clamp(2rem, 5vw, 3.25rem);
          font-weight: 600;
          color: var(--text);
          letter-spacing: 0;
          line-height: 1.15;
          margin-bottom: 1rem;
        }

        .hero-subtitle {
          font-size: 1.125rem;
          color: var(--text-muted);
          max-width: 440px;
          margin: 0 auto 2.5rem;
          line-height: 1.5;
        }

        .hero-ctas {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.75rem;
          width: 100%;
          max-width: 320px;
          margin: 0 auto;
        }

        .btn-primary {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          min-height: 56px;
          padding: 1.1rem 2rem;
          border: none;
          border-radius: 999px;
          background: var(--gradient-core);
          color: #FFFFFF;
          font-size: 1rem;
          font-weight: 600;
          letter-spacing: 0.01em;
          text-decoration: none;
          box-shadow: 0 4px 20px rgba(51, 214, 200, 0.3), 0 2px 8px rgba(0, 0, 0, 0.06);
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .btn-primary:hover {
          transform: translateY(-3px);
          box-shadow: 0 8px 32px rgba(51, 214, 200, 0.4), 0 4px 12px rgba(0, 0, 0, 0.08);
        }

        .btn-secondary {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          min-height: 52px;
          padding: 0.9rem 1.75rem;
          border: 1px solid var(--border);
          border-radius: 999px;
          background: var(--card);
          backdrop-filter: blur(12px);
          color: var(--text-soft);
          font-size: 0.95rem;
          font-weight: 500;
          text-decoration: none;
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .btn-secondary:hover {
          background: var(--card-solid);
          border-color: var(--text-quiet);
          color: var(--text);
          transform: translateY(-2px);
          box-shadow: var(--shadow-sm);
        }

        /* Stats */
        .stats-section {
          width: 100%;
          max-width: 800px;
          padding: 2rem 0;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          gap: 1rem;
        }

        .stat-card {
          background: var(--card);
          backdrop-filter: blur(20px);
          border: 1px solid var(--border-subtle);
          border-radius: 20px;
          padding: 1.25rem;
          text-align: center;
          box-shadow: var(--shadow-card);
        }

        .stat-value {
          font-size: 1.75rem;
          font-weight: 700;
          color: var(--text);
          margin-bottom: 0.25rem;
        }

        .stat-label {
          font-size: 0.8rem;
          font-weight: 500;
          color: var(--text-soft);
        }

        .stat-unit {
          font-size: 0.7rem;
          color: var(--text-quiet);
          margin-top: 0.15rem;
        }

        /* Recent */
        .recent-section {
          width: 100%;
          max-width: 560px;
          padding: 1.5rem 0;
        }

        .section-title {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--text-quiet);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-bottom: 1rem;
        }

        .recent-list {
          background: var(--card);
          backdrop-filter: blur(20px);
          border: 1px solid var(--border-subtle);
          border-radius: 20px;
          overflow: hidden;
          box-shadow: var(--shadow-card);
        }

        .recent-item {
          display: flex;
          align-items: center;
          gap: 0.875rem;
          padding: 1rem 1.25rem;
          border-bottom: 1px solid var(--border-subtle);
          transition: background var(--duration-fast) var(--ease-soft);
        }

        .recent-item:last-child {
          border-bottom: none;
        }

        .recent-item:hover {
          background: var(--hover-bg);
        }

        .recent-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .recent-info {
          flex: 1;
          font-size: 0.9rem;
        }

        .recent-feeling {
          font-weight: 600;
          color: var(--text);
        }

        .recent-about {
          color: var(--text-muted);
        }

        .recent-time {
          font-size: 0.75rem;
          color: var(--text-quiet);
          flex-shrink: 0;
        }

        .see-all-link {
          display: inline-block;
          margin-top: 1rem;
          font-size: 0.85rem;
          color: var(--accent);
          text-decoration: none;
          font-weight: 500;
        }

        .see-all-link:hover {
          opacity: 0.8;
        }

        /* Emotion Legend */
        .emotion-legend {
          width: 100%;
          max-width: 560px;
          padding: 1.5rem 0;
        }

        .emotion-pills {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .emotion-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.4rem 0.875rem;
          border-radius: 999px;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          font-size: 0.8rem;
          font-weight: 500;
          color: var(--text-soft);
          text-transform: capitalize;
        }

        .emotion-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        /* Footer */
        .home-footer {
          width: 100%;
          max-width: 960px;
          padding: 3rem 0 2rem;
          text-align: center;
        }

        .footer-copy {
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--text-soft);
          margin-bottom: 0.35rem;
        }

        .footer-secondary {
          font-size: 0.75rem;
          color: var(--text-quiet);
        }

        /* Responsive */
        @media (min-width: 640px) {
          .hero-ctas {
            flex-direction: row;
            max-width: 400px;
          }

          .btn-primary, .btn-secondary {
            width: auto;
            flex: 1;
          }

          .home-nav {
            gap: 0.5rem;
          }
        }

        @media (max-width: 768px) {
          .home-nav {
            display: none;
          }
        }
      `}</style>
    </main>
  )
}
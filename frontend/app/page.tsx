"use client"

import Link from 'next/link'

export default function Home() {
  return (
    <main className="landing">
      {/* Header */}
      <header className="landing-header">
        <div className="brand-lockup">
          <img className="brand-mark" src="/logo.png" alt="Feltabout" />
        </div>
          <nav className="landing-nav">
            <Link href="/library" className="nav-link">Library</Link>
            <Link href="/session" className="nav-link-subtle">Start a conversation</Link>
          </nav>
      </header>

      {/* Hero */}
      <section className="hero-section">
        <div className="hero-orb" aria-hidden="true" />
        <div className="hero-content">
          <h1 className="hero-headline">Reflect before you react.</h1>
          <p className="hero-subtitle">
            A calm space to prepare for the conversations that matter.
          </p>
        </div>

        {/* Interactive prompt card */}
        <Link href="/reflections/new" className="prompt-card">
          <span className="prompt-caret" aria-hidden="true">|</span>
          <span className="prompt-text">What conversation has been weighing on you lately?</span>
          <span className="prompt-arrow" aria-hidden="true">→</span>
        </Link>

        {/* CTAs */}
        <div className="hero-ctas">
          <Link href="/reflections/new" className="btn-primary">
            Start a reflection
          </Link>
          <Link href="/library" className="btn-secondary">
            Open library
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p className="footer-copy">
          Not therapy. Not a crisis line. Just a calm space to prepare.
        </p>
        <p className="footer-secondary">
          AI-guided communication clarity before difficult conversations.
        </p>
      </footer>

      <style jsx>{`
        .landing {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: space-between;
          padding: 4rem clamp(1.5rem, 5vw, 3rem) 2rem;
        }

        /* Header */
        .landing-header {
          width: 100%;
          max-width: 960px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding-bottom: 3rem;
        }

        .brand-mark {
          display: block;
          height: clamp(32px, 5vw, 48px);
          width: auto;
        }

        .landing-nav {
          display: flex;
          align-items: center;
          gap: 1.5rem;
        }

        .nav-link {
          font-size: 0.9rem;
          font-weight: 500;
          color: var(--text-soft);
          text-decoration: none;
          transition: color var(--duration-fast) var(--ease-soft);
        }

        .nav-link:hover {
          color: var(--text);
        }

        .nav-link-subtle {
          display: inline-flex;
          align-items: center;
          min-height: 36px;
          padding: 0.5rem 1.25rem;
          border-radius: 999px;
          border: 1px solid var(--border);
          background: rgba(255, 255, 255, 0.55);
          backdrop-filter: blur(8px);
          font-size: 0.85rem;
          font-weight: 500;
          color: var(--text-soft);
          text-decoration: none;
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .nav-link-subtle:hover {
          background: rgba(255, 255, 255, 0.85);
          border-color: var(--accent-border);
          color: var(--accent);
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(51, 214, 200, 0.15);
        }

        .nav-link-subtle:active {
          transform: translateY(0);
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
        }

        .hero-orb {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: clamp(280px, 50vw, 400px);
          height: clamp(280px, 50vw, 400px);
          border-radius: 50%;
          background: var(--gradient-core);
          filter: blur(80px);
          opacity: 0.35;
          animation: orb-breathe 9s ease-in-out infinite;
          pointer-events: none;
          z-index: -1;
        }

        @keyframes orb-breathe {
          0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.3; }
          50% { transform: translate(-50%, -52%) scale(1.04); opacity: 0.4; }
        }

        .hero-content {
          margin-bottom: 2rem;
        }

        .hero-headline {
          font-size: clamp(2rem, 6vw, 3.5rem);
          font-weight: 600;
          color: var(--text);
          letter-spacing: -0.03em;
          line-height: 1.1;
          margin-bottom: 1rem;
        }

        .hero-subtitle {
          font-size: 1.125rem;
          color: var(--text-muted);
          max-width: 400px;
          margin: 0 auto;
          line-height: 1.5;
        }

        /* Prompt card */
        .prompt-card {
          display: flex;
          align-items: center;
          gap: 1rem;
          width: 100%;
          max-width: 480px;
          min-height: 72px;
          padding: 1.25rem 1.5rem;
          margin-bottom: 2rem;
          border-radius: 20px;
          background: var(--card);
          backdrop-filter: blur(20px);
          border: 1px solid var(--border-subtle);
          box-shadow: var(--shadow-card);
          text-decoration: none;
          transition: all var(--duration-normal) var(--ease-soft);
          cursor: pointer;
        }

        .prompt-card:hover {
          background: var(--card-solid);
          border-color: var(--accent-border);
          box-shadow: 0 0 0 4px var(--accent-soft), var(--shadow-md);
          transform: translateY(-3px);
        }

        .prompt-card:hover .prompt-arrow {
          transform: translateX(4px);
        }

        .prompt-caret {
          font-size: 1.5rem;
          font-weight: 300;
          color: var(--accent);
          flex-shrink: 0;
          animation: caret-blink 1.2s ease-in-out infinite;
        }

        @keyframes caret-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }

        .prompt-text {
          flex: 1;
          font-size: 1rem;
          font-weight: 500;
          color: var(--text-soft);
          text-align: left;
        }

        .prompt-arrow {
          font-size: 1.25rem;
          color: var(--text-quiet);
          transition: transform var(--duration-normal) var(--ease-soft);
          flex-shrink: 0;
        }

        /* CTAs */
        .hero-ctas {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          width: 100%;
          max-width: 320px;
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

        .btn-primary:active {
          transform: translateY(-1px);
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
          background: var(--bg-deep);
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

        /* Footer */
        .landing-footer {
          width: 100%;
          max-width: 960px;
          padding-top: 3rem;
          text-align: center;
        }

        .footer-copy {
          font-size: 1rem;
          font-weight: 500;
          color: var(--text-soft);
          margin-bottom: 0.5rem;
        }

        .footer-secondary {
          font-size: 0.85rem;
          color: var(--text-quiet);
        }

        /* Responsive */
        @media (min-width: 640px) {
          .hero-ctas {
            flex-direction: row;
            max-width: 400px;
          }

          .btn-primary,
          .btn-secondary {
            width: auto;
            flex: 1;
          }
        }
      `}</style>
    </main>
  )
}

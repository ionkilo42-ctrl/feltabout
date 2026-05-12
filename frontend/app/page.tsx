"use client"

import Link from 'next/link'

const EXAMPLE_LINES = [
  "I want to talk about this without making it a fight.",
  "I think I got quiet because I felt dismissed, not because I stopped caring.",
  "Can we reset this conversation and try to understand each other better?",
]

const STEPS = [
  {
    title: 'Say it messy',
    description: 'Write what happened in plain language. No perfect wording required.',
  },
  {
    title: 'Find the signal',
    description: 'Feltabout looks for the feeling, need, assumption, and desired outcome underneath it.',
  },
  {
    title: 'Choose calmer words',
    description: 'Get one grounded thing you could say before you react, text, or walk into the conversation.',
  },
]

export default function HomePage() {
  return (
    <main className="home">
      <header className="home-header">
        <Link href="/" className="brand-lockup" aria-label="Feltabout home">
          <img className="brand-mark" src="/logo.png" alt="Feltabout" />
        </Link>
        <nav className="home-nav">
          <Link href="/session" className="nav-link">Prepare</Link>
          <Link href="/library" className="nav-link">Library</Link>
          <Link href="/aimee" className="nav-link">Aimee</Link>
          <Link href="/login" className="nav-link">Sign in</Link>
          <Link href="/session" className="nav-cta">Start</Link>
        </nav>
      </header>

      <section className="hero-section">
        <div className="ambient ambient-one" />
        <div className="ambient ambient-two" />

        <div className="hero-content">
          <p className="eyebrow">Difficult conversation prep</p>
          <h1 className="hero-headline">Find the words before the moment gets away from you.</h1>
          <p className="hero-subtitle">
            Feltabout helps you turn emotional overload into one calmer, clearer thing you can actually say.
          </p>
          <div className="hero-ctas">
            <Link href="/session" className="btn-primary">
              Prepare a conversation
            </Link>
            <Link href="/library" className="btn-secondary">
              View your library
            </Link>
          </div>
        </div>

        <div className="example-card" aria-label="Example conversation openers">
          <div className="example-label">Examples Feltabout can help shape</div>
          {EXAMPLE_LINES.map((line) => (
            <p key={line} className="example-line">“{line}”</p>
          ))}
        </div>
      </section>

      <section className="steps-section">
        {STEPS.map((step, index) => (
          <div className="step-card" key={step.title}>
            <div className="step-number">0{index + 1}</div>
            <h2>{step.title}</h2>
            <p>{step.description}</p>
          </div>
        ))}
      </section>

      <section className="positioning-section">
        <p>
          Built for reflection and communication support — not diagnosis, treatment, or emergency care.
          Shared spaces and live voice mediation are later milestones; the current MVP focuses on helping
          one person prepare with more clarity.
        </p>
      </section>

      <footer className="home-footer">
        <p className="footer-copy">Reflect before you react.</p>
        <p className="footer-secondary">Your reflections stay yours.</p>
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

        .home-header {
          width: 100%;
          max-width: 1120px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 2rem 0 1.5rem;
          position: relative;
          z-index: 2;
        }

        .brand-lockup {
          display: inline-flex;
          align-items: center;
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

        .hero-section {
          flex: 1;
          width: 100%;
          max-width: 1120px;
          display: grid;
          grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.95fr);
          align-items: center;
          gap: clamp(2rem, 5vw, 5rem);
          padding: clamp(3rem, 8vw, 6rem) 0 3rem;
          position: relative;
        }

        .ambient {
          position: absolute;
          border-radius: 999px;
          filter: blur(36px);
          opacity: 0.28;
          pointer-events: none;
        }

        .ambient-one {
          width: 280px;
          height: 280px;
          background: var(--accent, #33d6c8);
          top: 10%;
          left: -12%;
        }

        .ambient-two {
          width: 220px;
          height: 220px;
          background: #f4a261;
          right: 4%;
          bottom: 10%;
        }

        .hero-content {
          position: relative;
          z-index: 1;
        }

        .eyebrow {
          color: var(--accent, #33d6c8);
          font-size: 0.8rem;
          font-weight: 700;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          margin-bottom: 1rem;
        }

        .hero-headline {
          font-size: clamp(2.35rem, 6vw, 4.75rem);
          font-weight: 650;
          color: var(--text);
          letter-spacing: -0.055em;
          line-height: 0.98;
          margin-bottom: 1.25rem;
          max-width: 760px;
        }

        .hero-subtitle {
          font-size: clamp(1.05rem, 2vw, 1.25rem);
          color: var(--text-muted);
          max-width: 570px;
          line-height: 1.6;
          margin-bottom: 2rem;
        }

        .hero-ctas {
          display: flex;
          flex-wrap: wrap;
          gap: 0.875rem;
        }

        .btn-primary,
        .btn-secondary {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 54px;
          padding: 0.95rem 1.45rem;
          border-radius: 999px;
          font-size: 0.98rem;
          font-weight: 650;
          text-decoration: none;
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .btn-primary {
          border: none;
          background: var(--gradient-core);
          color: #FFFFFF;
          box-shadow: 0 4px 20px rgba(51, 214, 200, 0.3), 0 2px 8px rgba(0, 0, 0, 0.06);
        }

        .btn-primary:hover {
          transform: translateY(-3px);
          box-shadow: 0 8px 32px rgba(51, 214, 200, 0.4), 0 4px 12px rgba(0, 0, 0, 0.08);
        }

        .btn-secondary {
          border: 1px solid var(--border);
          background: var(--card);
          color: var(--text-soft);
          backdrop-filter: blur(12px);
        }

        .btn-secondary:hover {
          background: var(--card-solid);
          border-color: var(--text-quiet);
          color: var(--text);
          transform: translateY(-2px);
          box-shadow: var(--shadow-sm);
        }

        .example-card {
          position: relative;
          z-index: 1;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 28px;
          padding: clamp(1.25rem, 3vw, 2rem);
          box-shadow: var(--shadow-card);
          backdrop-filter: blur(20px);
        }

        .example-label {
          color: var(--text-quiet);
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          margin-bottom: 1rem;
        }

        .example-line {
          color: var(--text);
          font-size: clamp(1rem, 2vw, 1.15rem);
          line-height: 1.55;
          padding: 1rem 0;
          border-top: 1px solid var(--border-subtle);
        }

        .example-line:first-of-type {
          border-top: none;
        }

        .steps-section {
          width: 100%;
          max-width: 1120px;
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 1rem;
          padding: 2rem 0;
        }

        .step-card {
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 22px;
          padding: 1.35rem;
          box-shadow: var(--shadow-card);
        }

        .step-number {
          color: var(--accent, #33d6c8);
          font-size: 0.75rem;
          font-weight: 800;
          letter-spacing: 0.14em;
          margin-bottom: 1rem;
        }

        .step-card h2 {
          color: var(--text);
          font-size: 1.1rem;
          margin-bottom: 0.5rem;
        }

        .step-card p {
          color: var(--text-muted);
          line-height: 1.55;
          font-size: 0.92rem;
        }

        .positioning-section {
          width: 100%;
          max-width: 760px;
          padding: 2rem 0;
          text-align: center;
        }

        .positioning-section p {
          color: var(--text-muted);
          line-height: 1.65;
          font-size: 0.95rem;
        }

        .home-footer {
          width: 100%;
          max-width: 960px;
          padding: 2rem 0 2.5rem;
          text-align: center;
        }

        .footer-copy {
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--text-soft);
          margin-bottom: 0.35rem;
        }

        .footer-secondary {
          font-size: 0.75rem;
          color: var(--text-quiet);
        }

        @media (max-width: 900px) {
          .hero-section {
            grid-template-columns: 1fr;
            text-align: center;
          }

          .hero-subtitle {
            margin-left: auto;
            margin-right: auto;
          }

          .hero-ctas {
            justify-content: center;
          }

          .steps-section {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 768px) {
          .home-nav {
            display: none;
          }

          .hero-ctas {
            flex-direction: column;
          }
        }
      `}</style>
    </main>
  )
}

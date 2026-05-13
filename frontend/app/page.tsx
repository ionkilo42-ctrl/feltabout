'use client'

import Link from 'next/link'
import styles from './HomePage.module.css'

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
    <main className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <Link href="/" className={styles.logoLink} aria-label="Feltabout home">
          <img className={styles.logo} src="/logo.png" alt="Feltabout" />
        </Link>
        <nav className={styles.nav}>
          <Link href="/session" className={styles.navLink}>Prepare</Link>
          <Link href="/library" className={styles.navLink}>Library</Link>
          <Link href="/aimee" className={styles.navLink}>Chat with Aimee</Link>
        </nav>
      </header>

      {/* Hero Section */}
      <section className={styles.hero}>
        <div className={styles.ambientGlow} />
        
        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>Difficult conversation prep</p>
          <h1 className={styles.headline}>Find the words before the moment gets away from you.</h1>
          <p className={styles.subtitle}>
            Feltabout helps you turn emotional overload into one calmer, clearer thing you can actually say.
          </p>
          <div className={styles.ctaGroup}>
            <Link href="/session" className={styles.primaryCta}>
              Prepare for a conversation
            </Link>
            <Link href="/start" className={styles.secondaryCta}>
              Start shared session
            </Link>
          </div>
        </div>

        <div className={styles.exampleCard}>
          <div className={styles.exampleLabel}>Examples Feltabout can help shape</div>
          {EXAMPLE_LINES.map((line) => (
            <p key={line} className={styles.exampleLine}>"{line}"</p>
          ))}
        </div>
      </section>

      {/* Steps Section */}
      <section className={styles.steps}>
        {STEPS.map((step, index) => (
          <div className={styles.stepCard} key={step.title}>
            <div className={styles.stepNumber}>0{index + 1}</div>
            <h2>{step.title}</h2>
            <p>{step.description}</p>
          </div>
        ))}
      </section>

      {/* Positioning Note */}
      <section className={styles.positioning}>
        <p>
          Built for reflection and communication support — not diagnosis, treatment, or emergency care.
          Shared spaces and live voice mediation are later milestones; the current MVP focuses on helping
          one person prepare with more clarity.
        </p>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <p className={styles.footerPrimary}>Reflect before you react.</p>
        <p className={styles.footerSecondary}>Your reflections stay yours.</p>
      </footer>
    </main>
  )
}
'use client'

import { useState, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useAuthStore } from '@/store/sessionStore'

type Step = 'input' | 'generating' | 'done' | 'error'

interface PlanOutput {
  simple_opener?: string
  emotional_summary?: string
  needs_summary?: string
  assumptions?: string
  reframe?: string
  avoid_saying?: string
  conversation_opener?: string
  followup_questions?: string
  repair_statement?: string
}

interface GenerateResponse {
  is_crisis: boolean
  severity: string
  message: string
  resources: string[]
  output?: PlanOutput | null
}

const DETAILS: { key: keyof PlanOutput; label: string }[] = [
  { key: 'emotional_summary', label: "What you're carrying" },
  { key: 'needs_summary', label: 'What you need' },
  { key: 'assumptions', label: 'Assumptions to check' },
  { key: 'reframe', label: 'A clearer frame' },
  { key: 'avoid_saying', label: 'What to avoid' },
  { key: 'conversation_opener', label: 'Another way to begin' },
  { key: 'followup_questions', label: 'Follow-up questions' },
  { key: 'repair_statement', label: 'Closing statement' },
]

function PageShell({ children }: { children: ReactNode }) {
  return (
    <div className="session-page">
      <header className="app-header">
        <div className="brand-lockup">
          <Link href="/">
            <img className="brand-mark" src="/logo.png" alt="Feltabout" />
          </Link>
        </div>
      </header>

      <div className="session-container">{children}</div>
      <style>{styles}</style>
    </div>
  )
}

export default function SessionPage() {
  const router = useRouter()
  const token = useAuthStore(s => s.token)
  const [step, setStep] = useState<Step>('input')
  const [situation, setSituation] = useState('')
  const [desiredOutcome, setDesiredOutcome] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [simpleOpener, setSimpleOpener] = useState<string | null>(null)
  const [showFullDetails, setShowFullDetails] = useState(false)
  const [fullOutput, setFullOutput] = useState<PlanOutput | null>(null)
  const [safetyResources, setSafetyResources] = useState<string[]>([])

  const handleSubmit = async () => {
    const trimmedSituation = situation.trim()
    if (!trimmedSituation) return

    if (!token) {
      router.push('/login')
      return
    }

    setStep('generating')
    setError(null)
    setSafetyResources([])

    try {
      const createRes = await fetch(apiUrl('/reflections'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: trimmedSituation.slice(0, 80),
          situation: trimmedSituation,
          desired_outcome: desiredOutcome.trim(),
          // Legacy fields kept empty for backward compat
          feelings: '',
          interpretation: '',
          needs: '',
          fears: '',
          message_draft: '',
        }),
      })

      if (!createRes.ok) {
        const err = await createRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to save reflection')
      }

      const reflection = await createRes.json()

      const genRes = await fetch(apiUrl(`/reflections/${reflection.id}/generate`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!genRes.ok) {
        const err = await genRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to generate plan')
      }

      const generated = await genRes.json() as GenerateResponse

      if (generated.is_crisis) {
        setSimpleOpener(generated.message || 'Take a moment before continuing.')
        setSafetyResources(generated.resources || [])
        setFullOutput(null)
      } else if (generated.output) {
        setSimpleOpener(generated.output.simple_opener || generated.output.conversation_opener || '')
        setFullOutput(generated.output)
      } else {
        throw new Error('No plan output returned')
      }

      setStep('done')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setStep('error')
    }
  }

  const handleRestart = () => {
    setStep('input')
    setSituation('')
    setDesiredOutcome('')
    setError(null)
    setSimpleOpener(null)
    setShowFullDetails(false)
    setFullOutput(null)
    setSafetyResources([])
  }

  const hasDetails = fullOutput && DETAILS.some(detail => Boolean(fullOutput[detail.key]))

  if (step === 'generating') {
    return (
      <PageShell>
        <div className="session-generating">
          <div className="generating-card">
            <div className="generating-animation">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
            <h2>Finding the right words</h2>
            <p>One moment...</p>
          </div>
        </div>
      </PageShell>
    )
  }

  if (step === 'error') {
    return (
      <PageShell>
        <div className="session-intro">
          <h2>Something went wrong</h2>
          <p className="error-text">{error}</p>
          <button className="btn-primary" onClick={handleRestart}>
            Try again
          </button>
        </div>
      </PageShell>
    )
  }

  if (step === 'done') {
    return (
      <PageShell>
        <div className="session-done">
          <div className="opener-card">
            <div className="opener-label">One thing you could say</div>
            <p className="opener-text">{simpleOpener}</p>
          </div>

          {safetyResources.length > 0 && (
            <div className="resources-list">
              {safetyResources.map(resource => (
                <p key={resource}>{resource}</p>
              ))}
            </div>
          )}

          {desiredOutcome && (
            <div className="outcome-note">
              You wanted: {desiredOutcome}
            </div>
          )}

          {hasDetails && (
            <div className="details-section">
              <button
                className="details-toggle"
                onClick={() => setShowFullDetails(!showFullDetails)}
              >
                {showFullDetails ? 'Hide details' : 'See full details'}
              </button>

              {showFullDetails && (
                <div className="details-content">
                  {DETAILS.map(detail => {
                    const value = fullOutput?.[detail.key]
                    if (!value) return null
                    return (
                      <div key={detail.key} className="detail-card">
                        <div className="detail-label">{detail.label}</div>
                        <p>{value}</p>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          <div className="done-actions">
            <Link href="/library" className="btn-primary">
              View in library
            </Link>
            <button className="btn-ghost" onClick={handleRestart}>
              Start another
            </button>
          </div>
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <div className="session-input">
        <div className="input-header">
          <h2>Tell me what's going on.</h2>
          <p className="input-subtitle">Say it messy. We'll find the clarity.</p>
        </div>

        <div className="input-fields">
          <textarea
            value={situation}
            onChange={e => setSituation(e.target.value)}
            placeholder="Something happened, or it's been building up. Just get it out..."
            rows={6}
            className="main-input"
            autoFocus
          />

          <div className="optional-field">
            <label>What do you want from this conversation? (optional)</label>
            <textarea
              value={desiredOutcome}
              onChange={e => setDesiredOutcome(e.target.value)}
              placeholder="e.g. I want us to understand each other better, not fix everything tonight"
              rows={2}
              className="secondary-input"
            />
          </div>
        </div>

        <div className="input-actions">
          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={!situation.trim()}
          >
            Find the words
          </button>
        </div>
      </div>
    </PageShell>
  )
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = `
.session-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.brand-lockup {
  flex: 1;
}

.brand-mark {
  height: 24px;
  width: auto;
}

.session-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 2rem 1.5rem;
  max-width: 560px;
  margin: 0 auto;
  width: 100%;
}

/* Input step */
.session-input {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.input-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary, #111827);
  margin: 0 0 0.5rem;
}

.input-subtitle {
  font-size: 1rem;
  color: var(--text-muted, #6b7280);
  margin: 0;
}

.input-fields {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.main-input {
  width: 100%;
  padding: 1rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  font-size: 1rem;
  line-height: 1.6;
  resize: vertical;
  min-height: 160px;
  background: white;
  color: var(--text-primary, #111827);
}

.main-input:focus {
  outline: none;
  border-color: var(--accent, #e07a5f);
  box-shadow: 0 0 0 3px rgba(224, 122, 95, 0.1);
}

.main-input::placeholder {
  color: var(--text-quiet, #9ca3af);
}

.optional-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.optional-field label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary, #6b7280);
}

.secondary-input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  font-size: 0.9375rem;
  line-height: 1.5;
  resize: vertical;
  background: white;
  color: var(--text-primary, #111827);
}

.secondary-input:focus {
  outline: none;
  border-color: var(--accent, #e07a5f);
}

.secondary-input::placeholder {
  color: var(--text-quiet, #9ca3af);
}

.input-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Generating step */
.session-generating {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.generating-card {
  text-align: center;
}

.generating-animation {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.dot {
  width: 10px;
  height: 10px;
  background: var(--accent, #e07a5f);
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-12px); }
}

.generating-card h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary, #111827);
  margin: 0 0 0.5rem;
}

.generating-card p {
  font-size: 0.9375rem;
  color: var(--text-muted, #6b7280);
  margin: 0;
}

/* Done step */
.session-done {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.opener-card {
  background: white;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.opener-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent, #e07a5f);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}

.opener-text {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--text-primary, #111827);
  line-height: 1.6;
  margin: 0;
}

.outcome-note {
  font-size: 0.875rem;
  color: var(--text-muted, #6b7280);
  font-style: italic;
}

.resources-list {
  background: white;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  padding: 1rem;
}

.resources-list p {
  color: var(--text-primary, #111827);
  font-size: 0.9375rem;
  line-height: 1.5;
  margin: 0 0 0.5rem;
}

.resources-list p:last-child {
  margin-bottom: 0;
}

.details-section {
  border-top: 1px solid var(--color-border, #e5e7eb);
  padding-top: 1rem;
}

.details-toggle {
  background: none;
  border: none;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-muted, #6b7280);
  cursor: pointer;
  padding: 0.5rem 0;
}

.details-toggle:hover {
  color: var(--text-primary, #111827);
}

.details-content {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  margin-top: 0.75rem;
}

.detail-card {
  background: var(--card, white);
  border: 1px solid var(--border-subtle, #f3f4f6);
  border-radius: 10px;
  padding: 1rem;
}

.detail-label {
  font-size: 0.6875rem;
  font-weight: 700;
  color: var(--text-quiet, #9ca3af);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.detail-card p {
  font-size: 0.9375rem;
  color: var(--text-primary, #111827);
  line-height: 1.6;
  margin: 0;
}

.done-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

/* Buttons */
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0.75rem 1.5rem;
  background: var(--accent, #e07a5f);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #c9603f;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ghost {
  background: none;
  border: none;
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--text-muted, #6b7280);
  cursor: pointer;
  padding: 0.75rem;
}

.btn-ghost:hover {
  color: var(--text-primary, #111827);
}

.session-intro {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  flex: 1;
  gap: 1rem;
}

.session-intro h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary, #111827);
  margin: 0;
}

.error-text {
  color: #dc2626;
  font-size: 0.9375rem;
  margin: 0;
}
`

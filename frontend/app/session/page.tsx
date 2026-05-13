"use client"

import { useState, type ReactNode, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'
import { useParticipantStore } from '@/store/sessionStore'
import styles from './SessionPage.module.css'

type Step = 'name-prompt' | 'input' | 'generating' | 'done' | 'error'

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

interface MemorySuggestion {
  title: string
  summary: string
  reason: string
  reflection_id: string
}

interface GenerateResponse {
  is_crisis: boolean
  severity: string
  message: string
  resources: string[]
  output?: PlanOutput | null
  memory_suggestion?: MemorySuggestion | null
  reflection_id?: string
}

type FeedbackStep = 'initial' | 'followup'

const REACTION_OPTIONS = [
  { value: 1, label: 'Better than expected', icon: '↑' },
  { value: 2, label: 'About the same', icon: '→' },
  { value: 3, label: 'Worse than expected', icon: '↓' },
  { value: 4, label: "Didn't have it", icon: '—' },
] as const

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
    <main className={styles.page}>
      <header className={styles.header}>
        <div className={styles.brandLockup}>
          <Link href="/">
            <img className={styles.brandMark} src="/logo.png" alt="Feltabout" />
          </Link>
        </div>
      </header>
      <div className={styles.container}>{children}</div>
    </main>
  )
}

export default function SessionPage() {
  const router = useRouter()
  const participant = useParticipantStore((s) => s.participant)
  const setParticipant = useParticipantStore((s) => s.setParticipant)

  const [step, setStep] = useState<Step>('name-prompt')
  const [promptName, setPromptName] = useState('')
  const [situation, setSituation] = useState('')
  const [desiredOutcome, setDesiredOutcome] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [simpleOpener, setSimpleOpener] = useState<string | null>(null)
  const [showFullDetails, setShowFullDetails] = useState(false)
  const [fullOutput, setFullOutput] = useState<PlanOutput | null>(null)
  const [safetyResources, setSafetyResources] = useState<string[]>([])

  const [memorySuggestion, setMemorySuggestion] = useState<MemorySuggestion | null>(null)
  const [reflectionId, setReflectionId] = useState<string | null>(null)
  const [memoryDismissed, setMemoryDismissed] = useState(false)

  const [feedbackStep, setFeedbackStep] = useState<FeedbackStep>('initial')
  const [preparedScore, setPreparedScore] = useState<number | null>(null)
  const [lessReactiveScore, setLessReactiveScore] = useState<number | null>(null)
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false)

  const [howDidItGo, setHowDidItGo] = useState<number | null>(null)
  const [whatHappened, setWhatHappened] = useState('')
  const [followupSubmitted, setFollowupSubmitted] = useState(false)

  useEffect(() => {
    if (participant) {
      setStep('input')
    }
  }, [participant])

  const handleNamePromptSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!promptName.trim()) return

    setParticipant({
      participantId: '',
      displayName: promptName.trim(),
      spaceId: '',
      isOwner: false,
      joinedAt: new Date().toISOString(),
    })
    setStep('input')
  }

  const handleSubmit = async () => {
    const trimmedSituation = situation.trim()
    if (!trimmedSituation) return

    setStep('generating')
    setError(null)
    setSafetyResources([])

    try {
      const createRes = await fetch(apiUrl('/reflections'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: trimmedSituation.slice(0, 80),
          situation: trimmedSituation,
          desired_outcome: desiredOutcome.trim(),
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
        headers: { 'Content-Type': 'application/json' },
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
        if (generated.memory_suggestion) {
          setMemorySuggestion(generated.memory_suggestion)
          setReflectionId(reflection.id)
        }
      } else {
        throw new Error('No plan output returned')
      }

      setStep('done')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setStep('error')
    }
  }

  const handleSaveMemory = async () => {
    if (!reflectionId) return
    try {
      await fetch(apiUrl('/memories'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reflection_id: reflectionId,
          memory_type: 'emotional_pattern',
          title: memorySuggestion?.title,
          content: memorySuggestion?.summary,
          is_private: true,
        }),
      })
      setMemorySuggestion(null)
    } catch (err) {
      console.error('Failed to save memory:', err)
    }
  }

  const handleSkipMemory = () => {
    setMemoryDismissed(true)
  }

  const handleSubmitFeedback = async () => {
    if (!reflectionId || preparedScore === null || lessReactiveScore === null) return
    setFeedbackSubmitting(true)
    try {
      await fetch(apiUrl(`/reflections/${reflectionId}/feedback`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prepared_score: preparedScore,
          less_reactive_score: lessReactiveScore,
          helpful_text: '',
        }),
      })
      setFeedbackStep('followup')
    } catch (err) {
      console.error('Failed to submit feedback:', err)
    } finally {
      setFeedbackSubmitting(false)
    }
  }

  const handleSubmitFollowup = async () => {
    if (!reflectionId) return
    try {
      await fetch(apiUrl(`/reflections/${reflectionId}/feedback`), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          how_did_it_go: howDidItGo,
          what_happened: whatHappened,
        }),
      })
      setFollowupSubmitted(true)
    } catch (err) {
      console.error('Failed to submit follow-up:', err)
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
    setMemorySuggestion(null)
    setReflectionId(null)
    setMemoryDismissed(false)
    setFeedbackStep('initial')
    setPreparedScore(null)
    setLessReactiveScore(null)
    setHowDidItGo(null)
    setWhatHappened('')
    setFollowupSubmitted(false)
  }

  const hasDetails = fullOutput && DETAILS.some(detail => Boolean(fullOutput[detail.key]))

  if (step === 'name-prompt') {
    return (
      <PageShell>
        <div className={styles.namePrompt}>
          <h1>What should we call you?</h1>
          <form onSubmit={handleNamePromptSubmit} className={styles.nameForm}>
            <input
              className={styles.nameInput}
              type="text"
              placeholder="Your name"
              value={promptName}
              onChange={(e) => setPromptName(e.target.value)}
              autoFocus
            />
            <button className="btn-primary" type="submit" disabled={!promptName.trim()}>
              Continue
            </button>
          </form>
          <p className={styles.nameNote}>No account needed.</p>
        </div>
      </PageShell>
    )
  }

  if (step === 'generating') {
    return (
      <PageShell>
        <div className={styles.generating}>
          <div className={styles.generatingCard}>
            <div className={styles.generatingDots}>
              <div className={styles.dot} />
              <div className={styles.dot} />
              <div className={styles.dot} />
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
        <div className={styles.errorIntro}>
          <h2>Something went wrong</h2>
          <p className={styles.errorText}>{error}</p>
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
        <div className={styles.done}>
          <div className={styles.openerCard}>
            <div className={styles.openerLabel}>One thing you could say</div>
            <p className={styles.openerText}>{simpleOpener}</p>
          </div>

          {safetyResources.length > 0 && (
            <div className={styles.resourcesList}>
              {safetyResources.map(resource => (
                <p key={resource}>{resource}</p>
              ))}
            </div>
          )}

          {desiredOutcome && (
            <p className={styles.outcomeNote}>
              You wanted: {desiredOutcome}
            </p>
          )}

          {hasDetails && (
            <div className={styles.detailsSection}>
              <button
                className={styles.detailsToggle}
                onClick={() => setShowFullDetails(!showFullDetails)}
              >
                {showFullDetails ? 'Hide details' : 'See full details'}
              </button>

              {showFullDetails && (
                <div className={styles.detailsContent}>
                  {DETAILS.map(detail => {
                    const value = fullOutput?.[detail.key]
                    if (!value) return null
                    return (
                      <div key={detail.key} className={styles.detailCard}>
                        <div className={styles.detailLabel}>{detail.label}</div>
                        <p>{value}</p>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {memorySuggestion && !memoryDismissed && (
            <div className={styles.memoryCard}>
              <div className={styles.memoryLabel}>Personal insight detected</div>
              <h3 className={styles.memoryTitle}>{memorySuggestion.title}</h3>
              <p className={styles.memorySummary}>{memorySuggestion.summary}</p>
              <p className={styles.memoryReason}>Why this matters: {memorySuggestion.reason}</p>
              <div className={styles.memoryActions}>
                <button className="btn-primary btn-sm" onClick={handleSaveMemory}>
                  Save to my insights
                </button>
                <button className="btn-ghost btn-sm" onClick={handleSkipMemory}>
                  Skip
                </button>
              </div>
            </div>
          )}

          {feedbackStep === 'initial' && !followupSubmitted && (
            <div className={styles.feedbackSection}>
              <h3 className={styles.feedbackTitle}>How did the plan feel?</h3>
              <div className={styles.feedbackRow}>
                <span className={styles.feedbackLabel}>Prepared for the conversation</span>
                <div className={styles.scoreButtons}>
                  {[1, 2, 3].map(score => (
                    <button
                      key={score}
                      className={`${styles.scoreBtn} ${preparedScore === score ? styles.selected : ''}`}
                      onClick={() => setPreparedScore(score)}
                    >
                      {score === 1 ? '↓' : score === 2 ? '→' : '↑'}{' '}
                      {score === 1 ? 'No' : score === 2 ? 'Somewhat' : 'Yes'}
                    </button>
                  ))}
                </div>
              </div>
              <div className={styles.feedbackRow}>
                <span className={styles.feedbackLabel}>Feeling less reactive</span>
                <div className={styles.scoreButtons}>
                  {[1, 2, 3].map(score => (
                    <button
                      key={score}
                      className={`${styles.scoreBtn} ${lessReactiveScore === score ? styles.selected : ''}`}
                      onClick={() => setLessReactiveScore(score)}
                    >
                      {score === 1 ? '↓' : score === 2 ? '→' : '↑'}{' '}
                      {score === 1 ? 'No' : score === 2 ? 'Somewhat' : 'Yes'}
                    </button>
                  ))}
                </div>
              </div>
              <button
                className="btn-primary"
                onClick={handleSubmitFeedback}
                disabled={preparedScore === null || lessReactiveScore === null || feedbackSubmitting}
              >
                {feedbackSubmitting ? 'Saving...' : 'Continue'}
              </button>
            </div>
          )}

          {feedbackStep === 'followup' && !followupSubmitted && (
            <div className={styles.feedbackSection}>
              <h3 className={styles.feedbackTitle}>How did it actually go?</h3>
              <div className={styles.reactionOptions}>
                {REACTION_OPTIONS.map(option => (
                  <button
                    key={option.value}
                    className={`${styles.reactionBtn} ${howDidItGo === option.value ? styles.selected : ''}`}
                    onClick={() => setHowDidItGo(option.value)}
                  >
                    <span className={styles.reactionIcon}>{option.icon}</span>
                    <span className={styles.reactionLabel}>{option.label}</span>
                  </button>
                ))}
              </div>
              <textarea
                className={styles.feedbackTextarea}
                placeholder="What happened? (optional)"
                value={whatHappened}
                onChange={e => setWhatHappened(e.target.value)}
                rows={3}
              />
              <button
                className="btn-primary"
                onClick={handleSubmitFollowup}
                disabled={howDidItGo === null}
              >
                Done
              </button>
            </div>
          )}

          {followupSubmitted && (
            <div className={styles.feedbackThanks}>
              <p>Thanks for sharing. Your experience helps improve future sessions.</p>
            </div>
          )}

          <div className={styles.doneActions}>
            <button className="btn-primary" onClick={handleRestart}>
              Start another
            </button>
            <Link href="/" className="btn-ghost">
              Go home
            </Link>
          </div>
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <div className={styles.inputStep}>
        <div className={styles.inputHeader}>
          <h2>Tell me what's going on.</h2>
          <p className={styles.inputSubtitle}>Say it messy. We'll find the clarity.</p>
        </div>

        <div className={styles.inputFields}>
          <textarea
            className={styles.mainInput}
            value={situation}
            onChange={e => setSituation(e.target.value)}
            placeholder="Something happened, or it's been building up. Just get it out..."
            rows={6}
            autoFocus
          />

          <div className={styles.optionalField}>
            <label className={styles.optionalLabel}>
              What do you want from this conversation? (optional)
            </label>
            <textarea
              className={styles.secondaryInput}
              value={desiredOutcome}
              onChange={e => setDesiredOutcome(e.target.value)}
              placeholder="e.g. I want us to understand each other better, not fix everything tonight"
              rows={2}
            />
          </div>
        </div>

        <div className={styles.inputActions}>
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
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiUrl } from '@/lib/api'

// ─── Steps ────────────────────────────────────────────────────────────────────

type Step = 'intro' | 1 | 2 | 3 | 4 | 5 | 'generating' | 'done' | 'error'

interface Answers {
  situation: string
  feelings: string
  interpretation: string
  needs: string
  desired_outcome: string
}

interface OutputPlan {
  emotional_summary: string
  needs_summary: string
  assumptions: string
  reframe: string
  avoid_saying: string
  conversation_opener: string
  followup_questions: string
  repair_statement: string
}

const QUESTIONS: Record<keyof Answers, { prompt: string; placeholder: string }> = {
  situation: {
    prompt: "What conversation are you preparing for?",
    placeholder: "e.g. Talking to my partner about feeling disconnected...",
  },
  feelings: {
    prompt: "What feels hardest about it?",
    placeholder: "e.g. I'm scared of making things worse, or of being dismissed...",
  },
  interpretation: {
    prompt: "What do I want them to understand?",
    placeholder: "e.g. I need them to see that I'm not attacking them — I'm just hurting...",
  },
  needs: {
    prompt: "What do I want to better understand about them?",
    placeholder: "e.g. What's going on on their side that I might be missing?",
  },
  desired_outcome: {
    prompt: "What outcome feels realistic and respectful?",
    placeholder: "e.g. I want us to agree to try a weekly check-in, not fix everything tonight...",
  },
}

const STEP_ORDER: (keyof Answers)[] = ['situation', 'feelings', 'interpretation', 'needs', 'desired_outcome']

// ─── Auth Helper ──────────────────────────────────────────────────────────────

function getAuth() {
  if (typeof window === 'undefined') return null
  const stored = localStorage.getItem('feltabout_session')
  if (!stored) return null
  try {
    return JSON.parse(stored)
  } catch {
    return null
  }
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function SessionPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('intro')
  const [answers, setAnswers] = useState<Answers>({
    situation: '',
    feelings: '',
    interpretation: '',
    needs: '',
    desired_outcome: '',
  })
  const [currentField, setCurrentField] = useState<keyof Answers>('situation')
  const [inputValue, setInputValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [reflectionId, setReflectionId] = useState<string | null>(null)
  const [output, setOutput] = useState<OutputPlan | null>(null)

  // ─── Navigation ─────────────────────────────────────────────────────────────

  const handleStart = () => {
    setStep(1)
    setCurrentField('situation')
    setInputValue('')
  }

  const handleNext = () => {
    const trimmed = inputValue.trim()
    if (!trimmed) return

    setAnswers(prev => ({ ...prev, [currentField]: trimmed }))

    const currentIndex = STEP_ORDER.indexOf(currentField)
    if (currentIndex < STEP_ORDER.length - 1) {
      const nextField = STEP_ORDER[currentIndex + 1]
      setCurrentField(nextField)
      setInputValue('')
    } else {
      // All questions answered — create reflection and generate
      handleCreateAndGenerate({
        situation: answers.situation,
        feelings: answers.feelings,
        interpretation: answers.interpretation,
        needs: answers.needs,
        desired_outcome: trimmed,
      })
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleNext()
    }
  }

  const handleRestart = () => {
    setStep('intro')
    setAnswers({ situation: '', feelings: '', interpretation: '', needs: '', desired_outcome: '' })
    setCurrentField('situation')
    setInputValue('')
    setError(null)
    setReflectionId(null)
    setOutput(null)
  }

  // ─── API Calls ──────────────────────────────────────────────────────────────

  const handleCreateAndGenerate = async (finalAnswers: Answers) => {
    setStep('generating')
    setError(null)

    const auth = getAuth()
    if (!auth?.token) {
      router.push('/login')
      return
    }

    try {
      // 1. Create reflection
      const createRes = await fetch(apiUrl('/reflections'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`,
        },
        body: JSON.stringify({
          title: finalAnswers.situation.slice(0, 80),
          situation: finalAnswers.situation,
          feelings: finalAnswers.feelings,
          interpretation: finalAnswers.interpretation,
          needs: finalAnswers.needs,
          desired_outcome: finalAnswers.desired_outcome,
        }),
      })

      if (!createRes.ok) {
        const err = await createRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to save reflection')
      }

      const reflection = await createRes.json()
      setReflectionId(reflection.id)

      // 2. Generate conversation plan
      const genRes = await fetch(apiUrl(`/reflections/${reflection.id}/generate`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`,
        },
      })

      if (!genRes.ok) {
        const err = await genRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to generate plan')
      }

      const generated = await genRes.json()

      if (generated.is_crisis) {
        // Safety response — show crisis resources but still show session
        setOutput({
          emotional_summary: generated.message || 'Take a moment before continuing.',
          needs_summary: '',
          assumptions: '',
          reframe: '',
          avoid_saying: '',
          conversation_opener: '',
          followup_questions: '',
          repair_statement: '',
        })
      } else if (generated.output) {
        setOutput(generated.output)
      } else {
        throw new Error('No plan output returned')
      }

      setStep('done')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setStep('error')
    }
  }

  // ─── Render ─────────────────────────────────────────────────────────────────

  if (step === 'intro') {
    return (
      <main className="app">
        <header className="app-header">
          <div className="brand-lockup">
            <Link href="/">
              <img className="brand-mark" src="/logo.png" alt="Feltabout" />
            </Link>
          </div>
        </header>

        <div className="session-intro">
          <h2>Guided conversation prep</h2>
          <p>
            Answer five questions to clarify what you feel, what you need to say,
            and how to open the conversation with care. Your session will be saved
            to your library when you&apos;re done.
          </p>
          <button className="btn-primary" onClick={handleStart}>
            Begin session
          </button>
        </div>
      </main>
    )
  }

  if (step === 'generating') {
    return (
      <main className="app">
        <header className="app-header">
          <div className="brand-lockup">
            <Link href="/">
              <img className="brand-mark" src="/logo.png" alt="Feltabout" />
            </Link>
          </div>
        </header>

        <div className="session-generating">
          <div className="generating-card">
            <div className="generating-icon">…</div>
            <h2>Preparing your conversation plan</h2>
            <p>This usually takes 10–30 seconds.</p>
          </div>
        </div>
      </main>
    )
  }

  if (step === 'error') {
    return (
      <main className="app">
        <header className="app-header">
          <div className="brand-lockup">
            <Link href="/">
              <img className="brand-mark" src="/logo.png" alt="Feltabout" />
            </Link>
          </div>
        </header>

        <div className="session-intro">
          <h2>Something went wrong</h2>
          <p className="error-text">{error}</p>
          <button className="btn-primary" onClick={handleRestart}>
            Try again
          </button>
        </div>
      </main>
    )
  }

  if (step === 'done') {
    const fields: { label: string; key: keyof Answers }[] = [
      { label: "What's on your mind", key: 'situation' },
      { label: "What felt hardest", key: 'feelings' },
      { label: "What you want them to understand", key: 'interpretation' },
      { label: "What you want to understand about them", key: 'needs' },
      { label: "Your hoped-for outcome", key: 'desired_outcome' },
    ]

    return (
      <main className="app">
        <header className="app-header">
          <div className="brand-lockup">
            <Link href="/">
              <img className="brand-mark" src="/logo.png" alt="Feltabout" />
            </Link>
          </div>
        </header>

        <div className="session-done">
          <div className="done-header">
            <div className="done-icon">✓</div>
            <h2>Your conversation prep is ready</h2>
            <p>This session has been saved to your library.</p>
          </div>

          {/* Summary Cards */}
          <div className="summary-cards">
            {output && output.emotional_summary && (
              <div className="summary-card">
                <h3>What you&apos;re feeling</h3>
                <p>{output.emotional_summary}</p>
              </div>
            )}
            {output && output.needs_summary && (
              <div className="summary-card">
                <h3>What you need</h3>
                <p>{output.needs_summary}</p>
              </div>
            )}
            {output && output.assumptions && (
              <div className="summary-card">
                <h3>Assumptions to check</h3>
                <p>{output.assumptions}</p>
              </div>
            )}
            {output && output.reframe && (
              <div className="summary-card">
                <h3>A calmer frame</h3>
                <p>{output.reframe}</p>
              </div>
            )}
            {output && output.conversation_opener && (
              <div className="summary-card opener">
                <h3>A way to open</h3>
                <p>{output.conversation_opener}</p>
              </div>
            )}
            {output && output.followup_questions && (
              <div className="summary-card">
                <h3>Questions to consider</h3>
                <p>{output.followup_questions}</p>
              </div>
            )}
          </div>

          {/* CTA Buttons */}
          <div className="done-actions">
            <Link href="/library" className="btn-primary">
              View in library
            </Link>
            <button className="btn-secondary" onClick={handleRestart}>
              Start another session
            </button>
          </div>
        </div>
      </main>
    )
  }

  // ─── Question Step ───────────────────────────────────────────────────────────

  const currentStepIndex = STEP_ORDER.indexOf(currentField) + 1
  const totalSteps = STEP_ORDER.length
  const question = QUESTIONS[currentField]

  return (
    <main className="app">
      <header className="app-header">
        <div className="brand-lockup">
          <Link href="/">
            <img className="brand-mark" src="/logo.png" alt="Feltabout" />
          </Link>
        </div>
      </header>

      <div className="session-step">
        {/* Progress */}
        <div className="step-progress">
          <div className="step-dots">
            {STEP_ORDER.map((_, i) => (
              <span
                key={i}
                className={`step-dot ${i < currentStepIndex ? 'done' : i === currentStepIndex - 1 ? 'current' : ''}`}
              />
            ))}
          </div>
          <span className="step-count">{currentStepIndex} of {totalSteps}</span>
        </div>

        {/* Prompt */}
        <div className="step-prompt">
          <h2>{question.prompt}</h2>
        </div>

        {/* Input */}
        <div className="step-input-area">
          <textarea
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={question.placeholder}
            rows={4}
            autoFocus
          />
        </div>

        {/* Continue button */}
        <div className="step-actions">
          <button
            className="btn-primary"
            onClick={handleNext}
            disabled={!inputValue.trim()}
          >
            {currentStepIndex < totalSteps ? 'Continue' : 'Generate plan'}
          </button>
          {currentStepIndex > 1 && (
            <button className="btn-ghost" onClick={handleRestart}>
              Start over
            </button>
          )}
        </div>
      </div>
    </main>
  )
}
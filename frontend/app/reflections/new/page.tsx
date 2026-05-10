"use client"

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { apiUrl } from '@/lib/api'
import { useAuthStore } from '@/store/sessionStore'

const STEPS = [
  {
    id: 'situation',
    question: 'What conversation is on your mind?',
    hint: 'Describe what happened or what you\'re anticipating.',
    placeholder: 'It started when...',
  },
  {
    id: 'feelings',
    question: 'What are you feeling right now?',
    hint: 'Name the emotions, even the messy ones.',
    placeholder: 'I feel...',
  },
  {
    id: 'needs',
    question: 'What do you wish felt different after this conversation?',
    hint: 'What\'s the emotional outcome you\'re hoping for?',
    placeholder: 'I wish we could...',
  },
  {
    id: 'worry',
    question: 'What are you worried might happen?',
    hint: 'What assumptions or fears are you carrying?',
    placeholder: 'I\'m worried that...',
  },
  {
    id: 'reframe',
    question: 'What might the other person be going through?',
    hint: 'Try to see it from their perspective.',
    placeholder: 'They might be...',
  },
]

// Step 6: Review before generation
const REVIEW_STEP = { id: 'review', index: STEPS.length }

// Mapping from wizard step ids to reflection field names
const FIELD_MAP: Record<string, string> = {
  situation: 'situation',
  feelings: 'feelings',
  needs: 'needs',
  worry: 'fears',
  reframe: 'interpretation',
}

export default function NewReflectionPage() {
  const router = useRouter()
  const token = useAuthStore(s => s.token)
  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const isReview = currentStep === STEPS.length
  const step = isReview ? REVIEW_STEP : STEPS[currentStep]
  const currentAnswer = answers[step.id] || ''
  const totalSteps = STEPS.length + 1 // +1 for review
  const progress = (currentStep + 1) / (totalSteps + 1)

  useEffect(() => {
    inputRef.current?.focus()
  }, [currentStep])

  const transitionTo = (nextStep: number) => {
    setIsTransitioning(true)
    setTimeout(() => {
      setCurrentStep(nextStep)
      setIsTransitioning(false)
    }, 300)
  }

  const handleNext = () => {
    if (!isReview && !currentAnswer.trim()) return

    if (!isReview) {
      setAnswers(prev => ({ ...prev, [step.id]: currentAnswer }))
    }

    if (currentStep < STEPS.length - 1) {
      transitionTo(currentStep + 1)
    } else if (currentStep === STEPS.length - 1) {
      // Go to review
      transitionTo(currentStep + 1)
    } else {
      // On review step → generate
      handleGenerate()
    }
  }

  const handleBack = () => {
    if (currentStep === 0 || isTransitioning) return
    transitionTo(currentStep - 1)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleNext()
    }
  }

  const handleGenerate = async () => {
    if (!token) {
      router.push('/login')
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      // 1. Create reflection with all answers
      const createRes = await fetch(apiUrl('/reflections'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          situation: answers.situation || '',
          feelings: answers.feelings || '',
          needs: answers.needs || '',
          fears: answers.worry || '',
          interpretation: answers.reframe || '',
        }),
      })

      if (!createRes.ok) {
        throw new Error('Failed to save reflection')
      }

      const { id: reflectionId } = await createRes.json()

      // 2. Generate AI output
      const genRes = await fetch(apiUrl(`/reflections/${reflectionId}/generate`), {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!genRes.ok) {
        throw new Error('Failed to generate reflection')
      }

      // 3. Navigate to the result page
      router.push(`/reflections/${reflectionId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setIsGenerating(false)
    }
  }

  // ─── Generating State ───────────────────────────────────────────────────

  if (isGenerating) {
    return (
      <div className="wizard-container">
        <div className="generating-card">
          <div className="generating-dots">
            <span></span><span></span><span></span>
          </div>
          <p className="generating-title">Preparing your reflection...</p>
          <p className="generating-sub">This takes just a moment.</p>
        </div>
        <style>{generateStyles}</style>
      </div>
    )
  }

  // ─── Review Step ────────────────────────────────────────────────────────

  if (isReview) {
    return (
      <div className="wizard-container">
        <div className={`review-card ${isTransitioning ? 'transitioning' : ''}`}>
          <div className="step-indicator">Last step</div>
          <h2 className="review-title">Ready to reflect?</h2>
          <p className="review-sub">Here's what you've shared. You can go back to edit any of it.</p>

          <div className="answers-summary">
            {STEPS.map(s => (
              <div key={s.id} className="answer-row">
                <span className="answer-label">{s.question}</span>
                <span className="answer-text">{answers[s.id] || '—'}</span>
              </div>
            ))}
          </div>

          {error && <p className="review-error">{error}</p>}

          <div className="nav-buttons">
            <button className="btn-back" onClick={handleBack}>← Go back</button>
            <button className="btn-primary" onClick={handleGenerate}>
              Generate reflection
            </button>
          </div>
        </div>
        <style>{generateStyles}</style>
      </div>
    )
  }

  // ─── Wizard Steps ───────────────────────────────────────────────────────

  return (
    <div className="wizard-container" ref={containerRef}>
      <Link href="/" style={{ position: 'absolute', top: '28px', left: '32px', zIndex: 10, opacity: 0.7 }}>
        <img src="/logo.png" alt="Feltabout" style={{ width: '132px', height: 'auto', display: 'block' }} />
      </Link>

      {/* Progress dots */}
      <div className="progress-dots">
        {STEPS.map((_, i) => (
          <span
            key={i}
            className={`dot ${i === currentStep ? 'active' : ''} ${i < currentStep ? 'done' : ''}`}
          />
        ))}
        <span className={`dot ${isReview ? 'active' : ''}`} />
      </div>

      {/* Question card */}
      <div className={`question-card ${isTransitioning ? 'transitioning' : ''}`}>
        <div className="step-indicator">
          {currentStep + 1} of {STEPS.length}
        </div>

        {!isReview && (
          <>
            <h2 className="question">{(step as typeof STEPS[0]).question}</h2>
            <p className="hint">{(step as typeof STEPS[0]).hint}</p>
          </>
        )}

        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            value={currentAnswer}
            onChange={e => setAnswers(prev => ({ ...prev, [step.id]: e.target.value }))}
            onKeyDown={handleKeyDown}
            placeholder={(step as typeof STEPS[0]).placeholder}
            rows={4}
          />
          <div className="char-hint">
            {currentAnswer.length > 0 && (
              <span className="meta-key">⌘ + Enter to continue</span>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="nav-buttons">
        <button
          className="btn-back"
          onClick={handleBack}
          disabled={currentStep === 0}
        >
          ← Back
        </button>

        <button
          className="btn-next"
          onClick={handleNext}
          disabled={!currentAnswer.trim()}
        >
          Continue
        </button>
      </div>

      <style>{generateStyles}</style>
    </div>
  )
}

// Shared styles (used by all render branches)
const generateStyles = `
  .wizard-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem clamp(1rem, 5vw, 2rem);
    position: relative;
  }

  .progress-dots {
    position: absolute;
    top: 2rem;
    display: flex;
    gap: 0.5rem;
    margin-top: 50px;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--border);
    transition: all var(--duration-normal) var(--ease-soft);
  }

  .dot.active {
    background: var(--accent);
    transform: scale(1.2);
  }

  .dot.done {
    background: var(--gradient-core);
  }

  .question-card {
    width: 100%;
    max-width: 520px;
    text-align: center;
    opacity: 1;
    transform: translateY(0);
    transition: all 300ms var(--ease-soft);
  }

  .question-card.transitioning {
    opacity: 0;
    transform: translateY(10px);
  }

  .step-indicator {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-quiet);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 1.5rem;
  }

  .question {
    font-size: clamp(1.5rem, 4vw, 2rem);
    font-weight: 600;
    color: var(--text);
    letter-spacing: 0;
    line-height: 1.3;
    margin-bottom: 0.75rem;
  }

  .hint {
    font-size: 1rem;
    color: var(--text-muted);
    margin-bottom: 2.5rem;
    line-height: 1.5;
  }

  .input-wrapper {
    position: relative;
  }

  textarea {
    width: 100%;
    min-height: 140px;
    padding: 1.25rem;
    border: 1px solid var(--border);
    border-radius: 20px;
    background: var(--card);
    backdrop-filter: blur(20px);
    font-family: inherit;
    font-size: 1rem;
    line-height: 1.6;
    color: var(--text);
    resize: none;
    outline: none;
    transition: all var(--duration-normal) var(--ease-soft);
  }

  textarea::placeholder { color: var(--text-quiet); }
  textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
    background: var(--card-solid);
  }

  .char-hint {
    margin-top: 1rem;
    min-height: 1.5rem;
  }

  .meta-key {
    font-size: 0.8rem;
    color: var(--text-quiet);
  }

  .nav-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
    width: 100%;
    max-width: 520px;
  }

  .btn-back {
    flex: 0 0 auto;
    min-height: 52px;
    padding: 0 1.5rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--duration-normal) var(--ease-soft);
  }

  .btn-back:hover:not(:disabled) {
    background: var(--bg-deep);
    color: var(--text);
  }

  .btn-back:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .btn-next {
    flex: 1;
    min-height: 52px;
    padding: 0 2rem;
    border: none;
    border-radius: 999px;
    background: var(--gradient-core);
    color: #FFFFFF;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--duration-normal) var(--ease-soft);
    box-shadow: 0 4px 16px rgba(51, 214, 200, 0.25);
  }

  .btn-next:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(51, 214, 200, 0.35);
  }

  .btn-next:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .btn-primary {
    flex: 1;
    min-height: 52px;
    padding: 0 2rem;
    border: none;
    border-radius: 999px;
    background: var(--gradient-core);
    color: #FFFFFF;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--duration-normal) var(--ease-soft);
    box-shadow: 0 4px 16px rgba(51, 214, 200, 0.25);
  }

  .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(51, 214, 200, 0.35);
  }

  /* Generating state */
  .generating-card {
    text-align: center;
  }

  .generating-dots {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    margin-bottom: 1.5rem;
  }

  .generating-dots span {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--gradient-core);
    animation: pulse 1.4s ease-in-out infinite;
  }

  .generating-dots span:nth-child(2) { animation-delay: 0.2s; }
  .generating-dots span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes pulse {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
    40% { transform: scale(1.2); opacity: 1; }
  }

  .generating-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.5rem;
  }

  .generating-sub {
    font-size: 0.9rem;
    color: var(--text-muted);
  }

  /* Review step */
  .review-card {
    width: 100%;
    max-width: 560px;
    text-align: center;
    opacity: 1;
    transform: translateY(0);
    transition: all 300ms var(--ease-soft);
  }

  .review-card.transitioning {
    opacity: 0;
    transform: translateY(10px);
  }

  .review-title {
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: 0;
    margin-bottom: 0.75rem;
  }

  .review-sub {
    font-size: 1rem;
    color: var(--text-muted);
    margin-bottom: 2rem;
    line-height: 1.5;
  }

  .answers-summary {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    text-align: left;
  }

  .answer-row {
    padding: 0.875rem 0;
    border-bottom: 1px solid var(--border-subtle);
  }

  .answer-row:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .answer-row:first-child {
    padding-top: 0;
  }

  .answer-label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-quiet);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.35rem;
  }

  .answer-text {
    display: block;
    font-size: 0.95rem;
    color: var(--text-soft);
    line-height: 1.5;
  }

  .review-error {
    color: #dc2626;
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }
`
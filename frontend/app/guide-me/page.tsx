'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  startGuideSession,
  sendGuideMessage,
  generateReflectionCard,
  updateReflectionCard,
  saveGuideSession,
  type GuideSessionResponse,
  type AimeeReplyResponse,
  type ReflectionCard,
  type ConversationMessage,
} from '@/lib/guide-api'
import styles from './GuideMePage.module.css'

// Stage to human-readable label
const STAGE_LABELS: Record<string, string> = {
  safe_opening: 'Opening',
  first_expression: 'Expression',
  feeling_identification: 'Feeling',
  intensity_capture: 'Intensity',
  validation: 'Validated',
  about_mapping: 'About',
  memory_discovery: 'Memory',
  meaning_discovery: 'Meaning',
  need_discovery: 'Need',
  purpose_of_feeling: 'Purpose',
  constructive_path: 'Path',
  reflection_review: 'Review',
  save_or_signup: 'Save',
}

const STAGE_ORDER = [
  'safe_opening',
  'first_expression',
  'feeling_identification',
  'intensity_capture',
  'validation',
  'about_mapping',
  'memory_discovery',
  'meaning_discovery',
  'need_discovery',
  'purpose_of_feeling',
  'constructive_path',
  'reflection_review',
  'save_or_signup',
]

function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link href="/" className={styles.backLink}>
          <span className={styles.backArrow}>←</span>
          <img src="/logo.png" alt="Feltabout" className={styles.headerLogo} />
        </Link>
        <div className={styles.titleGroup}>
          <span className={styles.guideName}>Guide Me</span>
          <span className={styles.guideStatus}>Structured reflection</span>
        </div>
        <div className={styles.headerSpacer} />
      </header>
      {children}
    </main>
  )
}

// ─── Reflection Card Component ─────────────────────────────────────────────────

function ReflectionCardView({
  card,
  onEdit,
  onSave,
  onSkip,
  saving,
}: {
  card: ReflectionCard
  onEdit: (card: ReflectionCard) => void
  onSave: () => void
  onSkip: () => void
  saving: boolean
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<ReflectionCard>(card)

  const handleSaveEdit = () => {
    onEdit(draft)
    setEditing(false)
  }

  if (editing) {
    return (
      <div className={styles.cardPanel}>
        <div className={styles.cardHeader}>
          <span className={styles.cardHeaderLabel}>Edit your reflection</span>
        </div>
        <div className={styles.cardBody}>
          <div className={styles.cardField}>
            <label className={styles.fieldLabel}>Title</label>
            <input
              className={styles.fieldInput}
              value={draft.title}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
          </div>
          <div className={styles.cardField}>
            <label className={styles.fieldLabel}>Feelings</label>
            {draft.feelings.map((f, i) => (
              <div key={i} className={styles.feelingRow}>
                <span>{f.name}</span>
                <span className={styles.intensityBadge}>{f.intensity}/10</span>
              </div>
            ))}
          </div>
          <div className={styles.cardField}>
            <label className={styles.fieldLabel}>What it&apos;s about</label>
            {draft.about_links.map((a, i) => (
              <div key={i} className={styles.aboutRow}>
                <span className={styles.aboutType}>{a.type}</span>
                <span>{a.label}</span>
              </div>
            ))}
          </div>
          <div className={styles.cardField}>
            <label className={styles.fieldLabel}>Needs</label>
            <div className={styles.needsTags}>
              {draft.needs.map((n, i) => (
                <span key={i} className={styles.needTag}>{n}</span>
              ))}
            </div>
          </div>
          <div className={styles.cardField}>
            <label className={styles.fieldLabel}>Memory summary</label>
            <textarea
              className={styles.fieldTextarea}
              value={draft.memory_summary}
              onChange={(e) => setDraft({ ...draft, memory_summary: e.target.value })}
              rows={3}
            />
          </div>
          <div className={styles.cardField}>
            <label className={styles.fieldLabel}>Purpose of this feeling</label>
            <textarea
              className={styles.fieldTextarea}
              value={draft.purpose_of_feeling}
              onChange={(e) => setDraft({ ...draft, purpose_of_feeling: e.target.value })}
              rows={2}
            />
          </div>
          <div className={styles.cardField}>
            <label className={styles.fieldLabel}>Constructive path</label>
            <textarea
              className={styles.fieldTextarea}
              value={draft.constructive_path}
              onChange={(e) => setDraft({ ...draft, constructive_path: e.target.value })}
              rows={2}
            />
          </div>
          <div className={styles.cardField}>
            <label className={styles.fieldLabel}>Suggested words</label>
            {draft.suggested_words.map((w, i) => (
              <div key={i} className={styles.suggestedWord}>"{w}"</div>
            ))}
          </div>
        </div>
        <div className={styles.cardActions}>
          <button className={styles.cancelBtn} onClick={() => setEditing(false)}>
            Cancel
          </button>
          <button className={styles.saveChangesBtn} onClick={handleSaveEdit}>
            Save changes
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.cardPanel}>
      <div className={styles.cardHeader}>
        <span className={styles.cardHeaderLabel}>Your Reflection Card</span>
        <button className={styles.editCardBtn} onClick={() => setEditing(true)}>
          Edit
        </button>
      </div>

      <div className={styles.cardBody}>
        <h2 className={styles.cardTitle}>{card.title}</h2>

        <div className={styles.cardSection}>
          <h3 className={styles.sectionLabel}>Feelings</h3>
          <div className={styles.feelingsList}>
            {card.feelings.map((f, i) => (
              <div key={i} className={styles.feelingItem}>
                <span className={styles.feelingName}>{f.name}</span>
                <div className={styles.intensityTrack}>
                  <div
                    className={styles.intensityFill}
                    style={{ width: `${f.intensity * 10}%` }}
                  />
                </div>
                <span className={styles.intensityNum}>{f.intensity}/10</span>
              </div>
            ))}
          </div>
        </div>

        {card.about_links.length > 0 && (
          <div className={styles.cardSection}>
            <h3 className={styles.sectionLabel}>About</h3>
            <div className={styles.aboutList}>
              {card.about_links.map((a, i) => (
                <div key={i} className={styles.aboutItem}>
                  <span className={styles.aboutType}>{a.type}</span>
                  <span>{a.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {card.needs.length > 0 && (
          <div className={styles.cardSection}>
            <h3 className={styles.sectionLabel}>Underlying needs</h3>
            <div className={styles.needsTags}>
              {card.needs.map((n, i) => (
                <span key={i} className={styles.needTag}>{n}</span>
              ))}
            </div>
          </div>
        )}

        {card.memory_summary && (
          <div className={styles.cardSection}>
            <h3 className={styles.sectionLabel}>What happened</h3>
            <p className={styles.cardText}>{card.memory_summary}</p>
          </div>
        )}

        {card.purpose_of_feeling && (
          <div className={styles.cardSection}>
            <h3 className={styles.sectionLabel}>Purpose of this feeling</h3>
            <p className={styles.cardText}>{card.purpose_of_feeling}</p>
          </div>
        )}

        {card.constructive_path && (
          <div className={styles.cardSection}>
            <h3 className={styles.sectionLabel}>Constructive path</h3>
            <p className={styles.cardText}>{card.constructive_path}</p>
          </div>
        )}

        {card.suggested_words.length > 0 && (
          <div className={styles.cardSection}>
            <h3 className={styles.sectionLabel}>Suggested words</h3>
            {card.suggested_words.map((w, i) => (
              <p key={i} className={styles.suggestedWord}>"{w}"</p>
            ))}
          </div>
        )}
      </div>

      <div className={styles.cardActions}>
        <button className={styles.skipBtn} onClick={onSkip} disabled={saving}>
          Do not save
        </button>
        <button className={styles.saveCardBtn} onClick={onSave} disabled={saving}>
          {saving ? 'Saving...' : 'Looks right — save'}
        </button>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function GuideMePage() {
  const router = useRouter()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  const requestIdRef = useRef(0)

  const [session, setSession] = useState<GuideSessionResponse | null>(null)
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [card, setCard] = useState<ReflectionCard | null>(null)
  const [showCard, setShowCard] = useState(false)
  const [saved, setSaved] = useState(false)
  const [msgId, setMsgId] = useState(0)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading, showCard])

  // Start session on mount
  useEffect(() => {
    startGuideSession()
      .then((s) => {
        setSession(s)
        setMessages(s.conversation_history)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to start session')
      })
  }, [])

  const addMessage = useCallback((speaker: 'aimee' | 'user', text: string) => {
    setMessages((prev) => [
      ...prev,
      { speaker, text, ts: new Date().toISOString() },
    ])
    setMsgId((prev) => prev + 1)
  }, [])

  const handleSubmit = async () => {
    if (!inputText.trim() || loading || !session) return

    const text = inputText.trim()
    const reqId = requestIdRef.current + 1
    requestIdRef.current = reqId
    setInputText('')
    setLoading(true)
    setError(null)

    addMessage('user', text)

    try {
      // If we're at the reflection_review stage and user has submitted, generate card
      if (session.current_stage === 'reflection_review' && !card) {
        // User submitted their final message, let's generate the card
        const replyRes = await sendGuideMessage(session.id, text)
        if (requestIdRef.current !== reqId) return

        if (replyRes.is_crisis) {
          addMessage('aimee', replyRes.reply)
          setLoading(false)
          return
        }

        // Add Aimee's response
        addMessage('aimee', replyRes.reply)
        setSession(replyRes.session)

        // Now generate the card
        const cardRes = await generateReflectionCard(session.id)
        if (requestIdRef.current !== reqId) return

        setCard(cardRes.card)
        setSession(cardRes.session)
        setShowCard(true)
      } else {
        const replyRes = await sendGuideMessage(session.id, text)
        if (requestIdRef.current !== reqId) return

        if (replyRes.is_crisis) {
          addMessage('aimee', replyRes.reply)
          setLoading(false)
          return
        }

        addMessage('aimee', replyRes.reply)
        setSession(replyRes.session)

        // Check if we've reached reflection_review
        if (replyRes.new_stage === 'reflection_review' || replyRes.session.current_stage === 'reflection_review') {
          // Generate the card
          const cardRes = await generateReflectionCard(session.id)
          if (requestIdRef.current !== reqId) return
          setCard(cardRes.card)
          setSession(cardRes.session)
          setShowCard(true)
        }
      }
    } catch (err) {
      if (requestIdRef.current !== reqId) return
      setError(err instanceof Error ? err.message : 'Something went wrong')
      addMessage('aimee', "I'm having trouble responding. Can you try again?")
    } finally {
      if (requestIdRef.current === reqId) {
        setLoading(false)
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleEditCard = async (updatedCard: ReflectionCard) => {
    if (!session) return
    try {
      const updated = await updateReflectionCard(session.id, {
        title: updatedCard.title,
        feelings: updatedCard.feelings,
        about_links: updatedCard.about_links,
        needs: updatedCard.needs,
        memory_summary: updatedCard.memory_summary,
        purpose_of_feeling: updatedCard.purpose_of_feeling,
        constructive_path: updatedCard.constructive_path,
        suggested_words: updatedCard.suggested_words,
      })
      setCard(updatedCard)
      setSession(updated)
    } catch (err) {
      console.error('Failed to update card:', err)
    }
  }

  const handleSaveCard = async () => {
    if (!session) return
    setSaving(true)
    try {
      await saveGuideSession(session.id, true)
      setSaved(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
      setSaving(false)
    }
  }

  const handleSkipCard = async () => {
    if (!session) return
    setSaving(true)
    try {
      await saveGuideSession(session.id, false)
      setSaved(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to skip')
      setSaving(false)
    }
  }

  const handleRestart = () => {
    setSession(null)
    setMessages([])
    setCard(null)
    setShowCard(false)
    setSaved(false)
    setError(null)
    setInputText('')
    startGuideSession()
      .then((s) => {
        setSession(s)
        setMessages(s.conversation_history)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to start')
      })
  }

  // Stage progress
  const currentStageIndex = session ? STAGE_ORDER.indexOf(session.current_stage) : 0

  // ─── Saved state ─────────────────────────────────────────────────────────────
  if (saved) {
    return (
      <PageShell>
        <div className={styles.savedContainer}>
          <div className={styles.savedCard}>
            <div className={styles.savedIcon}>✨</div>
            <h2>Reflection saved</h2>
            <p>Your reflection has been saved to your library.</p>
            <div className={styles.savedActions}>
              <Link href="/library" className={styles.primaryBtn}>
                View in library
              </Link>
              <button className={styles.ghostBtn} onClick={handleRestart}>
                Start another
              </button>
            </div>
          </div>
        </div>
      </PageShell>
    )
  }

  // ─── Loading state ────────────────────────────────────────────────────────────
  if (!session) {
    return (
      <PageShell>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingDots}>
            <span />
            <span />
            <span />
          </div>
          <p>Starting Guide Me...</p>
          {error && <p className={styles.errorText}>{error}</p>}
        </div>
      </PageShell>
    )
  }

  // ─── Reflection Card review ────────────────────────────────────────────────────
  if (showCard && card) {
    return (
      <PageShell>
        <div className={styles.cardContainer}>
          {/* Stage progress */}
          <div className={styles.stageProgress}>
            <span className={styles.stageLabel}>
              {STAGE_LABELS[session.current_stage] || session.current_stage}
            </span>
            <div className={styles.stageBar}>
              <div
                className={styles.stageFill}
                style={{ width: `${Math.min(100, ((currentStageIndex + 1) / STAGE_ORDER.length) * 100)}%` }}
              />
            </div>
          </div>

          {/* Previous messages */}
          <div className={styles.messagesContainer}>
            {messages.map((msg, i) => (
              <div key={i} className={`${styles.message} ${styles[msg.speaker]}`}>
                {msg.speaker === 'aimee' && (
                  <div className={styles.msgAvatar}>
                    <span>A</span>
                  </div>
                )}
                <div className={styles.msgBubble}>
                  <p className={styles.msgText}>{msg.text}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Reflection Card */}
          <ReflectionCardView
            card={card}
            onEdit={handleEditCard}
            onSave={handleSaveCard}
            onSkip={handleSkipCard}
            saving={saving}
          />

          {error && <p className={styles.errorBanner}>{error}</p>}
        </div>
      </PageShell>
    )
  }

  // ─── Active session ───────────────────────────────────────────────────────────
  return (
    <PageShell>
      <div className={styles.sessionContainer}>
        {/* Stage progress */}
        <div className={styles.stageProgress}>
          <span className={styles.stageLabel}>
            {STAGE_LABELS[session.current_stage] || session.current_stage}
          </span>
          <div className={styles.stageBar}>
            <div
              className={styles.stageFill}
              style={{ width: `${Math.min(100, ((currentStageIndex + 1) / STAGE_ORDER.length) * 100)}%` }}
            />
          </div>
        </div>

        {/* Messages */}
        <div className={styles.messagesContainer}>
          {messages.map((msg, i) => (
            <div key={i} className={`${styles.message} ${styles[msg.speaker]}`}>
              {msg.speaker === 'aimee' && (
                <div className={styles.msgAvatar}>
                  <span>A</span>
                </div>
              )}
              <div className={styles.msgBubble}>
                <p className={styles.msgText}>{msg.text}</p>
              </div>
            </div>
          ))}

          {loading && (
            <div className={`${styles.message} ${styles.aimee}`}>
              <div className={styles.msgAvatar}>
                <span>A</span>
              </div>
              <div className={styles.msgBubble}>
                <p className={`${styles.msgText} ${styles.loadingDots}`}>
                  <span>.</span>
                  <span>.</span>
                  <span>.</span>
                </p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Error */}
        {error && <div className={styles.errorBanner}>{error}</div>}

        {/* Input */}
        <div className={styles.inputSection}>
          <textarea
            ref={inputRef}
            className={styles.chatInput}
            placeholder="Your response..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={loading}
          />
          <button
            className={styles.sendBtn}
            onClick={handleSubmit}
            disabled={!inputText.trim() || loading}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>

        {/* Bottom actions */}
        <div className={styles.bottomActions}>
          <button className={styles.restartBtn} onClick={handleRestart}>
            Start over
          </button>
        </div>
      </div>
    </PageShell>
  )
}
"use client"

import { useState } from 'react'
import Link from 'next/link'

// Emotion colors
const EMOTION_COLORS: Record<string, string> = {
  joy: '#FFD93D',
  sadness: '#6B9FFF',
  anger: '#FF6B6B',
  fear: '#B794F4',
  disgust: '#6BCB77',
  neutral: '#A3A3A3',
}

// Extraction data type
export type ExtractionData = {
  feeling: string
  primary_emotion: string
  intensity: number
  entity: string
  topic: string
  needs: string[]
  confidence: number
  suggestedMemoryTitle: string
}

type ExtractionCardProps = {
  extraction: ExtractionData
  onConfirm?: (data: ExtractionData) => void
  onEdit?: (data: ExtractionData) => void
  onAddFeeling?: () => void
  onAddNeed?: () => void
  onSkipNeed?: () => void
  onSaveMemory?: () => void
  onClose?: () => void
  className?: string
  saving?: boolean
}

export default function ExtractionCard({
  extraction,
  onConfirm,
  onEdit,
  onAddFeeling,
  onAddNeed,
  onSkipNeed,
  onSaveMemory,
  onClose,
  className = '',
  saving = false,
}: ExtractionCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedData, setEditedData] = useState<ExtractionData>(extraction)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [saved, setSaved] = useState(false)

  const emotionColor = EMOTION_COLORS[extraction.primary_emotion] || EMOTION_COLORS.neutral

  const handleEdit = () => {
    setEditedData(extraction)
    setIsEditing(true)
  }

  const handleSaveEdit = () => {
    if (onEdit) onEdit(editedData)
    setIsEditing(false)
  }

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm(extraction)
      setShowConfirmation(true)
    }
  }

  const handleSaveMemory = () => {
    if (onSaveMemory) {
      onSaveMemory()
      setSaved(true)
    }
  }

  // If saved, show success state
  if (saved) {
    return (
      <div className={`extraction-card extraction-card-saved ${className}`}>
        <div className="saved-animation">
          <div className="saved-checkmark">✓</div>
        </div>
        <div className="saved-message">
          <h3>Memory saved</h3>
          <p>Your feeling has been added to your emotional history.</p>
        </div>
        <div className="saved-actions">
          <Link href="/memories" className="v2-btn-secondary">
            View memories
          </Link>
          <Link href="/aimee" className="v2-btn-primary">
            Continue reflecting
          </Link>
        </div>
        <style>{cardStyles}</style>
      </div>
    )
  }

  // Confirmation animation
  if (showConfirmation) {
    return (
      <div className={`extraction-card extraction-card-confirming ${className}`}>
        <div className="confirming-animation">
          <div className="confirming-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
        <div className="confirming-message">
          <p>Perfect. Aimee will remember this.</p>
        </div>
        <style>{cardStyles}</style>
      </div>
    )
  }

  return (
    <div className={`extraction-card ${className}`}>
      {/* Header */}
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-notice-badge">
            <span className="notice-avatar">A</span>
            <span className="notice-text">Aimee noticed:</span>
          </div>
        </div>
        <div className="card-header-right">
          {onClose && (
            <button className="card-collapse-btn" onClick={onClose} title="Minimize">
              −
            </button>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="card-body">
        {/* Trust indicator */}
        <div className="trust-indicator">
          <span className="trust-lock">🔒</span>
          <span className="trust-label">You control what gets saved</span>
        </div>

        {/* Feeling section */}
        <div className="extraction-section feeling-section">
          <label className="section-label">Feeling</label>
          {isEditing ? (
            <select
              className="field-input"
              value={editedData.feeling}
              onChange={(e) => setEditedData({ ...editedData, feeling: e.target.value })}
            >
              <option value="frustrated">frustrated</option>
              <option value="angry">angry</option>
              <option value="hurt">hurt</option>
              <option value="anxious">anxious</option>
              <option value="sad">sad</option>
              <option value="disappointed">disappointed</option>
              <option value="overwhelmed">overwhelmed</option>
              <option value="grateful">grateful</option>
              <option value="joyful">joyful</option>
            </select>
          ) : (
            <div className="feeling-display">
              <div className="emotion-dot" style={{ background: emotionColor }} />
              <span className="feeling-name">{extraction.feeling}</span>
              <span className="emotion-label">{extraction.primary_emotion}</span>
            </div>
          )}
        </div>

        {/* Intensity section */}
        <div className="extraction-section intensity-section">
          <label className="section-label">Intensity</label>
          <div className="intensity-display">
            <div className="intensity-track">
              <div
                className="intensity-fill"
                style={{
                  width: `${(extraction.intensity / 10) * 100}%`,
                  background: emotionColor,
                }}
              />
            </div>
            <span className="intensity-value">{extraction.intensity}/10</span>
          </div>
          {isEditing && (
            <input
              type="range"
              min="1"
              max="10"
              className="intensity-slider"
              value={editedData.intensity}
              onChange={(e) =>
                setEditedData({ ...editedData, intensity: parseInt(e.target.value) })
              }
            />
          )}
        </div>

        {/* About / Entity */}
        <div className="extraction-section">
          <label className="section-label">About</label>
          {isEditing ? (
            <input
              type="text"
              className="field-input"
              value={editedData.entity}
              onChange={(e) => setEditedData({ ...editedData, entity: e.target.value })}
              placeholder="Who or what is this about?"
            />
          ) : (
            <Link href={`/entities?name=${encodeURIComponent(extraction.entity)}`} className="entity-link">
              <span className="entity-icon">👤</span>
              <span>{extraction.entity}</span>
            </Link>
          )}
        </div>

        {/* Topic */}
        <div className="extraction-section">
          <label className="section-label">Topic</label>
          <div className="topic-display">{extraction.topic}</div>
        </div>

        {/* Needs */}
        <div className="extraction-section needs-section">
          <label className="section-label">
            Underlying need{extraction.needs.length > 1 ? 's' : ''}
          </label>
          <div className="needs-list">
            {extraction.needs.map((need, i) => (
              <Link
                key={i}
                href={`/needs?name=${encodeURIComponent(need)}`}
                className="need-tag"
              >
                {need}
              </Link>
            ))}
          </div>
        </div>

        {/* Confidence indicator */}
        <div className="confidence-row">
          <span className="confidence-label">Aimee's confidence:</span>
          <div className="confidence-bar">
            <div
              className="confidence-fill"
              style={{ width: `${extraction.confidence * 100}%` }}
            />
          </div>
          <span className="confidence-value">{Math.round(extraction.confidence * 100)}%</span>
        </div>
      </div>

      {/* Secondary actions */}
      {!isEditing && (
        <div className="card-secondary-actions">
          <button className="btn-action" onClick={onAddFeeling}>
            <span className="action-icon">+</span>
            Add feeling
          </button>
          <button className="btn-action" onClick={onAddNeed}>
            <span className="action-icon">+</span>
            Add need
          </button>
          <button className="btn-action btn-skip" onClick={onSkipNeed}>
            Skip need
          </button>
        </div>
      )}

      {/* Primary actions */}
      <div className="card-primary-actions">
        {isEditing ? (
          <>
            <button className="btn-edit-cancel" onClick={() => setIsEditing(false)}>
              Cancel
            </button>
            <button className="btn-save" onClick={handleSaveEdit}>
              Save changes
            </button>
          </>
        ) : (
          <>
            <button className="btn-edit" onClick={handleEdit}>
              Edit
            </button>
            <button className="btn-confirm" onClick={handleConfirm}>
              Confirm
            </button>
          </>
        )}
      </div>

      {/* Save memory */}
      {!isEditing && !showConfirmation && (
        <div className="card-memory-action">
          <button className="btn-save-memory" onClick={handleSaveMemory}>
            <span className="save-icon">💾</span>
            Save memory
          </button>
        </div>
      )}

      <style>{cardStyles}</style>
    </div>
  )
}

// Shared card styles (duplicated for self-contained component)
const cardStyles = `
  .extraction-card {
    background: var(--card-solid);
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    animation: cardIn 0.4s var(--ease-spring);
  }

  @keyframes cardIn {
    from { opacity: 0; transform: translateY(16px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }

  /* Header */
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border-subtle);
    background: linear-gradient(to bottom, var(--bg-soft), var(--card-solid));
  }

  .card-notice-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .notice-avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--gradient-core);
    color: white;
    font-size: 0.7rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .notice-text {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .card-collapse-btn {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--text-muted);
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--duration-fast) var(--ease-soft);
  }

  .card-collapse-btn:hover {
    background: var(--hover-bg);
    color: var(--text);
  }

  /* Trust indicator */
  .trust-indicator {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem 0;
    margin-bottom: 0.5rem;
  }

  .trust-lock {
    font-size: 0.8rem;
  }

  .trust-label {
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--text-muted);
  }

  /* Body */
  .card-body {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.125rem;
  }

  .extraction-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .section-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-quiet);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  /* Feeling display */
  .feeling-display {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.625rem 0;
  }

  .emotion-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 0 8px currentColor;
  }

  .feeling-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
    text-transform: capitalize;
  }

  .emotion-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: capitalize;
    padding: 0.2rem 0.5rem;
    background: var(--bg-soft);
    border-radius: 999px;
  }

  /* Entity link */
  .entity-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0;
    text-decoration: none;
    color: var(--accent);
    font-weight: 500;
    transition: opacity var(--duration-fast) var(--ease-soft);
  }

  .entity-link:hover {
    opacity: 0.8;
  }

  .entity-icon {
    font-size: 0.9rem;
  }

  /* Topic */
  .topic-display {
    font-size: 0.9rem;
    color: var(--text-soft);
    padding: 0.5rem 0;
    line-height: 1.45;
  }

  /* Intensity */
  .intensity-display {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .intensity-track {
    flex: 1;
    height: 8px;
    background: var(--bg-deep);
    border-radius: 4px;
    overflow: hidden;
    max-width: 200px;
  }

  .intensity-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s var(--ease-soft);
  }

  .intensity-value {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-soft);
    min-width: 36px;
  }

  .intensity-slider {
    width: 100%;
    max-width: 200px;
    margin-top: 0.5rem;
    accent-color: var(--accent);
  }

  /* Needs */
  .needs-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.5rem 0;
  }

  .need-tag {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.875rem;
    border-radius: 999px;
    background: var(--accent-soft);
    border: 1px solid var(--accent-border);
    color: var(--accent);
    font-size: 0.8rem;
    font-weight: 500;
    text-decoration: none;
    transition: all var(--duration-fast) var(--ease-soft);
  }

  .need-tag:hover {
    background: var(--accent);
    color: white;
    transform: translateY(-1px);
  }

  /* Confidence */
  .confidence-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-subtle);
  }

  .confidence-label {
    font-size: 0.7rem;
    color: var(--text-quiet);
    white-space: nowrap;
  }

  .confidence-bar {
    flex: 1;
    height: 4px;
    background: var(--bg-deep);
    border-radius: 2px;
    overflow: hidden;
    max-width: 80px;
  }

  .confidence-fill {
    height: 100%;
    background: var(--success);
    border-radius: 2px;
  }

  .confidence-value {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--success);
    min-width: 28px;
    text-align: right;
  }

  /* Field input */
  .field-input {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--card);
    font-size: 0.9rem;
    color: var(--text);
    outline: none;
    transition: border-color var(--duration-fast) var(--ease-soft);
  }

  .field-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }

  /* Secondary actions */
  .card-secondary-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    border-top: 1px solid var(--border-subtle);
    background: var(--bg-soft);
  }

  .btn-action {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    min-height: 34px;
    padding: 0.4rem 0.875rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--card);
    color: var(--text-soft);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--duration-fast) var(--ease-soft);
  }

  .btn-action:hover {
    background: var(--card-solid);
    border-color: var(--accent-border);
    color: var(--accent);
    transform: translateY(-1px);
  }

  .btn-action .action-icon {
    font-size: 1rem;
    line-height: 1;
  }

  .btn-skip {
    color: var(--text-muted);
  }

  .btn-skip:hover {
    border-color: var(--border);
    color: var(--text-muted);
    background: var(--bg-soft);
    transform: none;
  }

  /* Primary actions */
  .card-primary-actions {
    display: flex;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    border-top: 1px solid var(--border-subtle);
  }

  .btn-edit {
    flex: 1;
    min-height: 44px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--card);
    color: var(--text-soft);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--duration-fast) var(--ease-soft);
  }

  .btn-edit:hover {
    background: var(--card-solid);
    border-color: var(--border-strong);
  }

  .btn-edit-cancel {
    flex: 1;
    min-height: 44px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--card);
    color: var(--text-soft);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
  }

  .btn-confirm {
    flex: 2;
    min-height: 44px;
    border: none;
    border-radius: 999px;
    background: var(--gradient-core);
    color: white;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(51, 214, 200, 0.3);
    transition: all var(--duration-normal) var(--ease-soft);
  }

  .btn-confirm:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(51, 214, 200, 0.4);
  }

  .btn-save {
    flex: 2;
    min-height: 44px;
    border: none;
    border-radius: 999px;
    background: var(--gradient-core);
    color: white;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(51, 214, 200, 0.3);
  }

  /* Memory action */
  .card-memory-action {
    padding: 0.75rem 1.25rem 1.25rem;
  }

  .btn-save-memory {
    width: 100%;
    min-height: 44px;
    border: 1.5px dashed var(--border);
    border-radius: 16px;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all var(--duration-fast) var(--ease-soft);
  }

  .btn-save-memory:hover {
    border-color: var(--accent-border);
    color: var(--accent);
    background: var(--accent-soft);
  }

  .save-icon {
    font-size: 0.9rem;
  }

  /* Saved state */
  .extraction-card-saved {
    text-align: center;
    padding: 2rem 1.5rem;
  }

  .saved-animation {
    margin-bottom: 1.5rem;
  }

  .saved-checkmark {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: var(--success-soft);
    border: 3px solid var(--success);
    color: var(--success);
    font-size: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
    animation: checkIn 0.4s var(--ease-spring);
  }

  @keyframes checkIn {
    0% { transform: scale(0); }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); }
  }

  .saved-message h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text);
    margin: 0 0 0.5rem;
  }

  .saved-message p {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin: 0 0 1.5rem;
  }

  .saved-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: center;
  }

  /* Confirming state */
  .extraction-card-confirming {
    text-align: center;
    padding: 2rem 1.5rem;
  }

  .confirming-animation {
    margin-bottom: 1.5rem;
  }

  .confirming-dots {
    display: flex;
    justify-content: center;
    gap: 6px;
  }

  .confirming-dots span {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--accent);
    animation: dot-bounce 1.2s ease-in-out infinite;
  }

  .confirming-dots span:nth-child(2) { animation-delay: 0.15s; }
  .confirming-dots span:nth-child(3) { animation-delay: 0.3s; }

  @keyframes dot-bounce {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
    40% { transform: scale(1.2); opacity: 1; }
  }

  .confirming-message p {
    font-size: 0.95rem;
    color: var(--text-muted);
    font-style: italic;
    margin: 0;
  }
`
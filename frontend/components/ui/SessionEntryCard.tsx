'use client'

import React from 'react'
import styles from './SessionEntryCard.module.css'

interface SessionEntryCardProps {
  mode: 'start' | 'join'
  sessionName?: string
  onSubmit: (name: string) => void
  isLoading?: boolean
  error?: string | null
  submitLabel?: string
  footerText?: string
  children?: React.ReactNode
}

export function SessionEntryCard({
  mode,
  sessionName,
  onSubmit,
  isLoading = false,
  error = null,
  submitLabel,
  footerText,
  children,
}: SessionEntryCardProps) {
  const [name, setName] = React.useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (name.trim()) {
      onSubmit(name.trim())
    }
  }

  const icon = mode === 'start' ? '✨' : '🤝'
  const title = mode === 'start' ? 'Start a Shared Session' : 'Join Shared Session'
  const defaultSubmitLabel = mode === 'start' ? 'Create Session' : 'Join Session'
  const defaultFooterText = mode === 'start'
    ? 'After creating, you can share a link with someone to join.'
    : "You'll be able to chat with Aimee and the session host."

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.icon}>{icon}</span>
        <h1 className={styles.title}>{title}</h1>
        {sessionName && mode === 'join' && (
          <p className={styles.description}>
            <strong>{sessionName}</strong> has invited you to a shared session with Aimee.
          </p>
        )}
        {mode === 'start' && (
          <p className={styles.description}>
            Share this session with someone to communicate together with Aimee as your guide.
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label htmlFor="displayName" className={styles.label}>Your name</label>
          <input
            id="displayName"
            type="text"
            className={styles.input}
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isLoading}
            autoFocus
          />
        </div>

        {error && (
          <div className={styles.error}>{error}</div>
        )}

        <button
          type="submit"
          className={styles.submitBtn}
          disabled={!name.trim() || isLoading}
        >
          {isLoading ? (mode === 'start' ? 'Creating session...' : 'Joining...') : (submitLabel || defaultSubmitLabel)}
        </button>
      </form>

      <div className={styles.footer}>
        <p className={styles.footerText}>{footerText || defaultFooterText}</p>
      </div>

      {children}
    </div>
  )
}

export default SessionEntryCard
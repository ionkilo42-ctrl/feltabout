'use client'

import React, { useCallback, useEffect, useRef } from 'react'
import styles from './Textarea.module.css'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  hint?: string
  autoResize?: boolean
  maxHeight?: string
}

export function Textarea({
  label,
  error,
  hint,
  autoResize = true,
  maxHeight = '200px',
  className = '',
  id,
  onChange,
  value,
  rows = 3,
  ...props
}: TextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const inputId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current
    if (textarea && autoResize) {
      textarea.style.height = 'auto'
      const newHeight = Math.min(textarea.scrollHeight, parseInt(maxHeight) || 200)
      textarea.style.height = `${newHeight}px`
    }
  }, [autoResize, maxHeight])

  useEffect(() => {
    adjustHeight()
  }, [value, adjustHeight])

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange?.(e)
    adjustHeight()
  }

  return (
    <div className={`${styles.wrapper} ${className}`}>
      {label && (
        <label htmlFor={inputId} className={styles.label}>
          {label}
        </label>
      )}
      <textarea
        ref={textareaRef}
        id={inputId}
        className={`${styles.textarea} ${error ? styles.hasError : ''}`}
        rows={rows}
        onChange={handleChange}
        value={value}
        style={{ maxHeight }}
        {...props}
      />
      {error && <span className={styles.error}>{error}</span>}
      {hint && !error && <span className={styles.hint}>{hint}</span>}
    </div>
  )
}

export default Textarea
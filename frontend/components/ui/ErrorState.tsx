'use client'

import React from 'react'
import styles from './ErrorState.module.css'

interface ErrorStateProps {
  title?: string
  message: string
  action?: React.ReactNode
  icon?: string
  className?: string
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  action,
  icon = '⚠️',
  className = '',
}: ErrorStateProps) {
  return (
    <div className={`${styles.container} ${className}`}>
      {icon && <div className={styles.icon}>{icon}</div>}
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.message}>{message}</p>
      {action && <div className={styles.action}>{action}</div>}
    </div>
  )
}

export default ErrorState
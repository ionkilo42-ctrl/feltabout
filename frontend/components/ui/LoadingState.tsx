'use client'

import React from 'react'
import styles from './LoadingState.module.css'

interface LoadingStateProps {
  size?: 'sm' | 'md' | 'lg'
  label?: string
  className?: string
}

export function LoadingState({
  size = 'md',
  label = 'Loading...',
  className = '',
}: LoadingStateProps) {
  return (
    <div className={`${styles.container} ${className}`}>
      <div className={`${styles.spinner} ${styles[size]}`}>
        <span></span>
        <span></span>
        <span></span>
      </div>
      {label && <p className={styles.label}>{label}</p>}
    </div>
  )
}

export default LoadingState
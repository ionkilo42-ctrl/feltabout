'use client'

import React from 'react'
import styles from './ParticipantChip.module.css'

interface ParticipantChipProps {
  name: string
  isYou?: boolean
  isHost?: boolean
  isAimee?: boolean
  avatar?: string
  className?: string
}

export function ParticipantChip({
  name,
  isYou = false,
  isHost = false,
  isAimee = false,
  avatar,
  className = '',
}: ParticipantChipProps) {
  const initials = name.charAt(0).toUpperCase()
  const displayAvatar = avatar || (isAimee ? '✨' : initials)

  const classNames = [
    styles.chip,
    isYou ? styles.you : '',
    isAimee ? styles.aimee : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classNames}>
      <span className={styles.avatar}>
        {isAimee ? '✨' : initials}
      </span>
      <span className={styles.name}>
        {name}
        {isYou && ' (you)'}
        {isHost && ' (host)'}
        {isAimee && ' (facilitator)'}
      </span>
    </div>
  )
}

export default ParticipantChip
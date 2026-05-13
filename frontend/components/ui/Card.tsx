'use client'

import React from 'react'
import styles from './Card.module.css'

type CardVariant = 'default' | 'elevated' | 'solid' | 'glass'
type CardPadding = 'none' | 'sm' | 'md' | 'lg' | 'xl'

interface CardProps {
  children: React.ReactNode
  variant?: CardVariant
  padding?: CardPadding
  className?: string
  onClick?: () => void
  as?: 'div' | 'section' | 'article' | 'aside'
}

export function Card({
  children,
  variant = 'default',
  padding = 'md',
  className = '',
  onClick,
  as: Component = 'div',
}: CardProps) {
  const classNames = [
    styles.card,
    styles[variant],
    styles[`padding-${padding}`],
    onClick ? styles.interactive : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <Component className={classNames} onClick={onClick}>
      {children}
    </Component>
  )
}

export function CardHeader({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <div className={`${styles.header} ${className}`}>{children}</div>
}

export function CardContent({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <div className={`${styles.content} ${className}`}>{children}</div>
}

export function CardFooter({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <div className={`${styles.footer} ${className}`}>{children}</div>
}

export default Card
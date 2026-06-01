'use client'

import React from 'react'
import Link from 'next/link'
import styles from './PageHeader.module.css'

interface PageHeaderProps {
  title: string
  subtitle?: string
  backHref?: string
  actions?: React.ReactNode
  className?: string
}

export function PageHeader({
  title,
  subtitle,
  backHref,
  actions,
  className = '',
}: PageHeaderProps) {
  return (
    <header className={`${styles.header} ${className}`}>
      <div className={styles.left}>
        {backHref && (
          <Link href={backHref} className={styles.backLink}>
            <span className={styles.backArrow}>←</span>
          </Link>
        )}
        <div className={styles.titles}>
          <h1 className={styles.title}>{title}</h1>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </header>
  )
}

export default PageHeader
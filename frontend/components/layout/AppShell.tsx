'use client'

import React from 'react'
import Link from 'next/link'
import styles from './AppShell.module.css'

interface NavItem {
  href: string
  label: string
  icon?: string
}

const NAV_ITEMS: NavItem[] = [
  { href: '/session/[id]', label: 'Shared session', icon: '💬' },
  { href: '/', label: 'Home', icon: '🏠' },
  { href: '/library', label: 'Library', icon: '📚' },
  { href: '/aimee', label: 'Chat with Aimee', icon: '✨' },
]

interface AppShellProps {
  children: React.ReactNode
  showSidebar?: boolean
}

export function AppShell({ children, showSidebar = true }: AppShellProps) {
  return (
    <div className={`${styles.shell} ${showSidebar ? styles.withSidebar : ''}`}>
      {showSidebar && (
        <aside className={styles.sidebar}>
          <div className={styles.sidebarInner}>
            {/* Logo */}
            <Link href="/" className={styles.logoLink}>
              <img className={styles.logo} src="/logo.png" alt="Feltabout" />
              <span className={styles.logoText}>Feltabout</span>
            </Link>

            {/* Navigation */}
            <nav className={styles.nav}>
              {NAV_ITEMS.map((item) => (
                <Link key={item.href} href={item.href} className={styles.navItem}>
                  {item.icon && <span className={styles.navIcon}>{item.icon}</span>}
                  <span className={styles.navLabel}>{item.label}</span>
                </Link>
              ))}
            </nav>

            {/* Footer */}
            <div className={styles.sidebarFooter}>
              <p className={styles.footerNote}>Your reflections stay private.</p>
            </div>
          </div>
        </aside>
      )}

      <main className={styles.main}>
        {children}
      </main>
    </div>
  )
}

export default AppShell
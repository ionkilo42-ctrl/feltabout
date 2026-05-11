"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'

// Primary emotion colors
const EMOTION_COLORS = {
  joy: '#FFD93D',
  sadness: '#6B9FFF',
  anger: '#FF6B6B',
  fear: '#B794F4',
  disgust: '#6BCB77',
}

type V2LayoutProps = {
  children: React.ReactNode
  title: string
  subtitle?: string
  showBack?: boolean
  backHref?: string
  action?: React.ReactNode
}

export default function V2Layout({
  children,
  title,
  subtitle,
  showBack = true,
  backHref = '/',
  action,
}: V2LayoutProps) {
  const pathname = usePathname()
  const isHome = pathname === '/'

  return (
    <main className="v2-layout">
      {/* Header */}
      <header className="v2-header">
        <div className="v2-header-left">
          {showBack && !isHome ? (
            <Link href={backHref} className="back-link">
              <span className="back-arrow">←</span>
            </Link>
          ) : (
            <Link href="/" className="logo-link">
              <img src="/logo.png" alt="Feltabout" className="header-logo" />
            </Link>
          )}
          {isHome ? (
            <div className="header-brand">
              <img src="/logo.png" alt="Feltabout" className="header-logo-text" />
            </div>
          ) : (
            <div className="header-title-group">
              <h1 className="header-title">{title}</h1>
              {subtitle && <p className="header-subtitle">{subtitle}</p>}
            </div>
          )}
        </div>
        <div className="v2-header-right">
          {action || (
            !isHome && (
              <Link href="/aimee" className="header-action-btn">
                + New
              </Link>
            )
          )}
        </div>
      </header>

      {/* Content */}
      <div className="v2-content">
        {children}
      </div>

      {/* Trust footer */}
      {!isHome && (
        <footer className="v2-trust-footer">
          <div className="trust-pill">
            <span className="trust-icon">🔒</span>
            <span className="trust-text">Your feelings belong to you.</span>
          </div>
        </footer>
      )}

      <style>{`
        .v2-layout {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          background: var(--bg);
        }

        /* Header */
        .v2-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          padding: 1.25rem clamp(1.5rem, 5vw, 2rem);
          border-bottom: 1px solid var(--border-subtle);
          background: var(--card);
          backdrop-filter: blur(20px);
          position: sticky;
          top: 0;
          z-index: 10;
        }

        .v2-header-left {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          min-width: 0;
        }

        .v2-header-right {
          flex-shrink: 0;
        }

        .back-link {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          border-radius: 10px;
          text-decoration: none;
          transition: background var(--duration-fast) var(--ease-soft);
        }

        .back-link:hover {
          background: var(--hover-bg);
        }

        .back-arrow {
          font-size: 1.25rem;
          color: var(--text-muted);
          font-weight: 300;
        }

        .logo-link {
          display: flex;
          align-items: center;
          text-decoration: none;
        }

        .header-logo {
          height: 28px;
          width: auto;
        }

        .header-brand {
          display: flex;
          align-items: center;
        }

        .header-logo-text {
          height: 28px;
          width: auto;
        }

        .header-title-group {
          min-width: 0;
        }

        .header-title {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text);
          margin: 0;
          line-height: 1.2;
        }

        .header-subtitle {
          font-size: 0.75rem;
          color: var(--text-muted);
          margin: 0.15rem 0 0;
          line-height: 1.3;
        }

        .header-action-btn {
          display: inline-flex;
          align-items: center;
          min-height: 36px;
          padding: 0.5rem 1rem;
          border-radius: 999px;
          background: var(--gradient-core);
          color: white;
          font-size: 0.85rem;
          font-weight: 600;
          text-decoration: none;
          box-shadow: 0 2px 10px rgba(51, 214, 200, 0.2);
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .header-action-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 16px rgba(51, 214, 200, 0.3);
        }

        /* Content */
        .v2-content {
          flex: 1;
          width: 100%;
          max-width: 720px;
          margin: 0 auto;
          padding: 1.5rem clamp(1.5rem, 5vw, 2rem);
        }

        /* Trust footer */
        .v2-trust-footer {
          padding: 1.5rem clamp(1.5rem, 5vw, 2rem);
          display: flex;
          justify-content: center;
        }

        .trust-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: var(--card);
          border: 1px solid var(--border-subtle);
          border-radius: 999px;
        }

        .trust-icon {
          font-size: 0.875rem;
        }

        .trust-text {
          font-size: 0.8rem;
          font-weight: 500;
          color: var(--text-soft);
        }

        /* Shared card styles */
        .v2-card {
          background: var(--card);
          backdrop-filter: blur(20px);
          border: 1px solid var(--border-subtle);
          border-radius: 20px;
          box-shadow: var(--shadow-card);
        }

        .v2-card-solid {
          background: var(--card-solid);
          border: 1px solid var(--border-subtle);
          border-radius: 20px;
          box-shadow: var(--shadow-card);
        }

        /* Shared button styles */
        .v2-btn-primary {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 44px;
          padding: 0 1.5rem;
          border: none;
          border-radius: 999px;
          background: var(--gradient-core);
          color: white;
          font-size: 0.875rem;
          font-weight: 600;
          text-decoration: none;
          box-shadow: 0 2px 12px rgba(51, 214, 200, 0.2);
          cursor: pointer;
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .v2-btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(51, 214, 200, 0.35);
        }

        .v2-btn-secondary {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 44px;
          padding: 0 1.25rem;
          border: 1px solid var(--border);
          border-radius: 999px;
          background: var(--card);
          backdrop-filter: blur(12px);
          color: var(--text-soft);
          font-size: 0.875rem;
          font-weight: 500;
          text-decoration: none;
          cursor: pointer;
          transition: all var(--duration-normal) var(--ease-soft);
        }

        .v2-btn-secondary:hover {
          background: var(--card-solid);
          border-color: var(--border-strong);
          transform: translateY(-1px);
        }

        /* Empty state */
        .v2-empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          padding: 3rem 1.5rem;
          gap: 1rem;
        }

        .v2-empty-icon {
          font-size: 3rem;
          opacity: 0.6;
        }

        .v2-empty-title {
          font-size: 1rem;
          font-weight: 600;
          color: var(--text);
          margin: 0;
        }

        .v2-empty-description {
          font-size: 0.9rem;
          color: var(--text-muted);
          margin: 0;
          max-width: 280px;
          line-height: 1.5;
        }

        .v2-empty-action {
          margin-top: 0.5rem;
        }

        /* Section label */
        .v2-section-label {
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--text-quiet);
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin-bottom: 0.875rem;
        }

        /* Modal overlay */
        .v2-modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.25);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: flex-end;
          justify-content: center;
          z-index: 100;
          padding: 1rem;
          animation: overlayIn 0.2s var(--ease-soft);
        }

        @keyframes overlayIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .v2-modal {
          background: var(--card-solid);
          border-radius: 24px 24px 0 0;
          width: 100%;
          max-width: 500px;
          max-height: 85vh;
          overflow-y: auto;
          animation: modalSlideUp 0.3s var(--ease-spring);
        }

        @keyframes modalSlideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }

        .v2-modal-header {
          position: relative;
          padding: 1.5rem;
          border-bottom: 1px solid var(--border-subtle);
        }

        .v2-modal-header-content {
          padding-top: 0.5rem;
        }

        .v2-modal-header-content h2 {
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text);
          margin: 0 0 0.25rem;
        }

        .v2-modal-subtitle {
          font-size: 0.8rem;
          color: var(--text-muted);
        }

        .v2-modal-close {
          position: absolute;
          top: 1.25rem;
          right: 1.25rem;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          border: none;
          background: var(--bg-soft);
          color: var(--text-muted);
          font-size: 1.25rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background var(--duration-fast) var(--ease-soft);
        }

        .v2-modal-close:hover {
          background: var(--hover-bg);
        }

        .v2-modal-body {
          padding: 1.25rem 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .v2-modal-section {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .v2-modal-label {
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--text-quiet);
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        .v2-modal-value {
          font-size: 0.9rem;
          color: var(--text-soft);
        }

        .v2-modal-actions {
          display: flex;
          gap: 0.75rem;
          padding: 1.25rem 1.5rem;
          border-top: 1px solid var(--border-subtle);
        }

        /* Responsive */
        @media (max-width: 480px) {
          .v2-header {
            padding: 1rem 1rem;
          }

          .v2-content {
            padding: 1rem;
          }
        }
      `}</style>
    </main>
  )
}

// Export emotion colors for use in other components
export { EMOTION_COLORS }

// Empty state component
type EmptyStateProps = {
  icon?: string
  title: string
  description: string
  action?: React.ReactNode
}

export function V2EmptyState({ icon = '📝', title, description, action }: EmptyStateProps) {
  return (
    <div className="v2-empty-state">
      <div className="v2-empty-icon">{icon}</div>
      <h3 className="v2-empty-title">{title}</h3>
      <p className="v2-empty-description">{description}</p>
      {action && <div className="v2-empty-action">{action}</div>}
    </div>
  )
}

// Emotion dot component
type EmotionDotProps = {
  emotion: string
  size?: number
  showLabel?: boolean
}

export function EmotionDot({ emotion, size = 10, showLabel = false }: EmotionDotProps) {
  const color = EMOTION_COLORS[emotion as keyof typeof EMOTION_COLORS] || '#A3A3A3'
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
      <span
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          background: color,
          flexShrink: 0,
        }}
      />
      {showLabel && (
        <span style={{ fontSize: '0.85rem', color: 'var(--text)', textTransform: 'capitalize' }}>
          {emotion}
        </span>
      )}
    </span>
  )
}

// Linked object component - makes emotional objects clickable
type LinkedObjectProps = {
  type: 'entity' | 'need' | 'feeling' | 'emotion'
  value: string
  href?: string
  onClick?: () => void
}

export function LinkedObject({ type, value, href, onClick }: LinkedObjectProps) {
  const hrefMap = {
    entity: `/entities?name=${encodeURIComponent(value)}`,
    need: `/needs?name=${encodeURIComponent(value)}`,
    feeling: `/feel-flow?feeling=${encodeURIComponent(value)}`,
    emotion: `/feel-map?emotion=${encodeURIComponent(value)}`,
  }

  const iconMap = {
    entity: '👤',
    need: '💭',
    feeling: '💭',
    emotion: '🎭',
  }

  const content = (
    <span className="linked-object" data-type={type}>
      <span className="linked-object-icon">{iconMap[type]}</span>
      <span className="linked-object-value">{value}</span>
    </span>
  )

  if (onClick) {
    return (
      <button
        onClick={onClick}
        style={{
          background: 'none',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        {content}
      </button>
    )
  }

  return (
    <Link href={href || hrefMap[type]} className="linked-object-link">
      {content}
    </Link>
  )
}
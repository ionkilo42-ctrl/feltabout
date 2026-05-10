'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'

// Legacy entry point — direct /session/[id] URLs are no longer valid.
// Users should arrive via invite links, not raw session IDs.
export default function SessionByIdPage() {
  const params = useParams()
  const id = params.id as string

  return (
    <main style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      fontFamily: 'inherit',
    }}>
      <div style={{
        textAlign: 'center',
        maxWidth: '400px',
      }}>
        <div style={{ fontSize: '48px', marginBottom: '24px' }}>💬</div>
        <h1 style={{
          fontSize: '1.5rem',
          fontWeight: '600',
          color: 'var(--text, #111827)',
          marginBottom: '12px',
        }}>
          Conversation not found
        </h1>
        <p style={{
          fontSize: '1rem',
          color: 'var(--text-muted, #6b7280)',
          lineHeight: '1.6',
          marginBottom: '24px',
        }}>
          This link may have expired or been shared incorrectly. To start a conversation, use the main Feltabout app.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <Link href="/library" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '48px',
            padding: '0 1.5rem',
            border: 'none',
            borderRadius: '999px',
            background: 'var(--gradient-core, linear-gradient(135deg, #33d6c8, #e07a5f))',
            color: '#FFFFFF',
            fontSize: '15px',
            fontWeight: '600',
            textDecoration: 'none',
          }}>
            Go to Library
          </Link>
          <Link href="/session" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '44px',
            padding: '0 1.5rem',
            border: '1px solid var(--border, #e5e7eb)',
            borderRadius: '999px',
            background: 'transparent',
            color: 'var(--text-soft, #6b7280)',
            fontSize: '14px',
            fontWeight: '500',
            textDecoration: 'none',
          }}>
            Start a new conversation
          </Link>
        </div>
      </div>
    </main>
  )
}
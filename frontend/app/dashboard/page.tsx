'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '../../store/sessionStore'
import { apiUrl } from '../../lib/api'

export default function DashboardPage() {
  const [sessions, setSessions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const { token, userName, logout } = useAuthStore()

  useEffect(() => {
    if (!token) {
      router.push('/login')
      return
    }
    fetch(apiUrl('/my-sessions'), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => {
        setSessions(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(() => {
        setSessions([])
        setLoading(false)
      })
  }, [token, router])

  const createSession = async () => {
    const res = await fetch(apiUrl('/sessions'), {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
    const { session_id } = await res.json()
    router.push(`/session/${session_id}`)
  }

  const joinSession = () => {
    const sid = prompt('Enter session ID:')
    if (sid) router.push(`/session/${sid}`)
  }

  if (!token) return null

  return (
    <main className="dashboard-shell">
      <section className="dashboard-card">
      <div className="dashboard-topline">
        <div className="brand-lockup">
          <img className="brand-mark" src="/favicon.svg" alt="" />
          <div>
            <h1>My Sessions</h1>
            <p className="subtitle">Welcome, {userName}</p>
          </div>
        </div>
        <button className="ghost-btn" onClick={logout}>Log out</button>
      </div>
      <div className="dashboard-actions">
        <button onClick={createSession}>
          Create New Session
        </button>
        <button className="secondary" onClick={joinSession}>
          Join by ID
        </button>
      </div>
      {loading ? (
        <p className="history-empty">Loading...</p>
      ) : sessions.length === 0 ? (
        <p className="history-empty">No sessions yet. Create one to get started.</p>
      ) : (
        <ul className="history-list">
          {sessions.map(s => (
            <li key={s.session_id}>
              <button
                onClick={() => router.push(`/session/${s.session_id}`)}
                className="history-item"
              >
                <strong className="history-sid">{s.session_id}</strong>
                <br />
                <small className="history-meta">{s.mode} · {new Date(s.created_at).toLocaleDateString()} · {s.participant_count} participant(s)</small>
              </button>
            </li>
          ))}
        </ul>
      )}
      </section>
    </main>
  )
}

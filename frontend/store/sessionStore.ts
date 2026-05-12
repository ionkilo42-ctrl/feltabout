/**
 * Feltabout — Session state store (Zustand)
 * Replaces the fragile myIdRef / otherRef / nameRef pattern.
 * All cross-component session state lives here.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Participant {
  id: string
  name: string
  role: string
  emotion: string
}

export interface AuthUser {
  id: string
  email: string
  name: string
}

interface SessionStore {
  myId: string
  otherParticipant: Participant | null
  setMyId: (id: string) => void
  setOther: (p: Participant | null) => void
  clearSession: () => void
}

interface AuthStore {
  token: string
  userId: string
  userEmail: string
  userName: string
  setAuth: (token: string, userId: string, name: string, email?: string) => void
  logout: () => void
  isLoggedIn: () => boolean
}

export const useSessionStore = create<SessionStore>((set) => ({
  myId: '',
  otherParticipant: null,
  setMyId: (id) => set({ myId: id }),
  setOther: (p) => set({ otherParticipant: p }),
  clearSession: () => set({ myId: '', otherParticipant: null }),
}))

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      token: '',
      userId: '',
      userEmail: '',
      userName: '',
      setAuth: (token, userId, name, email = '') => set({ token, userId, userName: name, userEmail: email }),
      logout: () => set({ token: '', userId: '', userEmail: '', userName: '' }),
      isLoggedIn: () => !!get().token,
    }),
    {
      name: 'feltabout-auth',
      partialize: (state) => ({ token: state.token, userId: state.userId, userName: state.userName }),
    }
  )
)

// ─── Session Participant Store (localStorage-based for no-auth MVP) ────────────
// For MVP: Identity is just participant_id + display_name + space_id in localStorage.
// No account needed to join/create sessions.

export interface SessionParticipant {
  participantId: string
  displayName: string
  spaceId: string
  isOwner: boolean
  joinedAt: string
}

interface ParticipantStore {
  participant: SessionParticipant | null
  setParticipant: (p: SessionParticipant) => void
  clearParticipant: () => void
}

export const useParticipantStore = create<ParticipantStore>()(
  persist(
    (set) => ({
      participant: null,
      setParticipant: (p) => set({ participant: p }),
      clearParticipant: () => set({ participant: null }),
    }),
    {
      name: 'feltabout-participant',
    }
  )
)

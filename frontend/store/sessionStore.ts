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
  userName: string
  setAuth: (token: string, userId: string, name: string) => void
  logout: () => void
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
    (set) => ({
      token: '',
      userId: '',
      userName: '',
      setAuth: (token, userId, name) => set({ token, userId, userName: name }),
      logout: () => set({ token: '', userId: '', userName: '' }),
    }),
    {
      name: 'feltabout-auth',
      partialize: (state) => ({ token: state.token, userId: state.userId, userName: state.userName }),
    }
  )
)
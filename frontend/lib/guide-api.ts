/**
 * Guide Me API client for frontend.
 */

import { apiUrl } from './api'

export interface ConversationMessage {
  speaker: 'aimee' | 'user'
  text: string
  ts: string
}

export interface CollectedFeeling {
  name: string
  intensity: number
  validated: boolean
}

export interface CollectedAboutLink {
  type: 'entity' | 'topic' | 'event'
  label: string
}

export interface CollectedNeed {
  category: string
  text: string
}

export interface ReflectionCardFeelings {
  name: string
  intensity: number
}

export interface ReflectionCardAboutLinks {
  type: string
  label: string
}

export interface ReflectionCard {
  title: string
  feelings: ReflectionCardFeelings[]
  about_links: ReflectionCardAboutLinks[]
  needs: string[]
  memory_summary: string
  purpose_of_feeling: string
  constructive_path: string
  suggested_words: string[]
}

export interface GuideSessionResponse {
  id: string
  user_id: string
  status: string
  current_stage: string
  conversation_history: ConversationMessage[]
  collected_feelings: CollectedFeeling[]
  collected_about_links: CollectedAboutLink[]
  collected_needs: CollectedNeed[]
  collected_context: Record<string, unknown>
  reflection_card: ReflectionCard | null
  created_at: string
  updated_at: string
}

export interface AimeeReplyResponse {
  reply: string
  session: GuideSessionResponse
  stage_advanced: boolean
  new_stage: string | null
  is_crisis: boolean
  safety_resources: string[]
}

export interface GenerateCardResponse {
  card: ReflectionCard
  session: GuideSessionResponse
}

export interface UpdateCardRequest {
  title?: string
  feelings?: ReflectionCardFeelings[]
  about_links?: ReflectionCardAboutLinks[]
  needs?: string[]
  memory_summary?: string
  purpose_of_feeling?: string
  constructive_path?: string
  suggested_words?: string[]
}

// ─── API Functions ─────────────────────────────────────────────────────────────

export async function startGuideSession(): Promise<GuideSessionResponse> {
  const res = await fetch(apiUrl('/guide-sessions'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to start guide session')
  }
  return res.json()
}

export async function sendGuideMessage(
  sessionId: string,
  message: string,
): Promise<AimeeReplyResponse> {
  const res = await fetch(
    apiUrl(`/guide-sessions/${sessionId}/respond?user_message=${encodeURIComponent(message)}`),
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    },
  )
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to send message')
  }
  return res.json()
}

export async function generateReflectionCard(
  sessionId: string,
): Promise<GenerateCardResponse> {
  const res = await fetch(apiUrl(`/guide-sessions/${sessionId}/generate-card`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to generate reflection card')
  }
  return res.json()
}

export async function updateReflectionCard(
  sessionId: string,
  data: UpdateCardRequest,
): Promise<GuideSessionResponse> {
  const res = await fetch(apiUrl(`/guide-sessions/${sessionId}/card`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to update card')
  }
  return res.json()
}

export async function saveGuideSession(
  sessionId: string,
  save: boolean = true,
): Promise<{ status: string; message: string; reflection_id?: string }> {
  const res = await fetch(apiUrl(`/guide-sessions/${sessionId}/save`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ save }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to save')
  }
  return res.json()
}

export async function getGuideSession(
  sessionId: string,
): Promise<GuideSessionResponse> {
  const res = await fetch(apiUrl(`/guide-sessions/${sessionId}`))
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to get session')
  }
  return res.json()
}
/**
 * V2 API Client for Feltabout emotional graph.
 * 
 * Provides typed API calls to v2 backend endpoints.
 * All functions return typed responses and handle errors gracefully.
 */

import { apiUrl } from './api'

// ─── Types ──────────────────────────────────────────────────────────────────

export type PrimaryEmotion = 'joy' | 'sadness' | 'anger' | 'fear' | 'disgust'

export type NeedStatus = 'identified' | 'unknown' | 'skipped'

export interface ExtractedEntity {
  name: string
  entity_type: string
}

export interface ExtractedTopic {
  title: string
}

export interface ExtractedNeed {
  name: string
  status: NeedStatus
}

export interface ExtractedFeeling {
  primary_emotion: PrimaryEmotion
  label: string
  intensity: number
  confidence: number
  entities: ExtractedEntity[]
  topics: ExtractedTopic[]
  needs: ExtractedNeed[]
}

export interface ExtractionResponse {
  feelings: ExtractedFeeling[]
  suggested_memory_title: string
  suggested_response: string
  safety_status: 'safe' | 'flagged'
}

export interface ConfirmedFeeling {
  primary_emotion: PrimaryEmotion
  label: string
  intensity: number
  confidence: number
  source_text: string
  entity_names: string[]
  topic_titles: string[]
  need_names: string[]
}

export interface ConfirmRequest {
  source_text: string
  memory_title: string
  memory_narrative?: string
  occurred_at?: string
  feelings: ConfirmedFeeling[]
}

export interface ConfirmResponse {
  memory_id: string
  feelings_count: number
  status: string
}

export interface Memory {
  id: string
  title: string
  narrative?: string
  ai_summary?: string
  privacy_level: string
  occurred_at?: string
  created_at: string
  feelings: Feeling[]
  needs: Need[]
  entities: Entity[]
  topics: Topic[]
}

export interface Feeling {
  id: string
  primary_emotion: PrimaryEmotion
  label: string
  intensity: number
  confidence?: number
  source_text?: string
  occurred_at?: string
  created_at: string
}

export interface Entity {
  id: string
  canonical_name: string
  entity_type: string
  created_at: string
}

export interface Need {
  id: string
  name: string
  created_at: string
}

export interface Topic {
  id: string
  title: string
  created_at: string
}

export interface FeelFlowPoint {
  date: string
  joy: number
  sadness: number
  anger: number
  fear: number
  disgust: number
}

export interface FeelFlowResponse {
  data: FeelFlowPoint[]
  time_bucket: string
  emotion_totals: Record<PrimaryEmotion, number>
  average_intensity: number
}

export interface FeelMapItem {
  label: string
  weight: number
  about?: string
  intensity: number
}

export interface EmotionGroup {
  emotion: PrimaryEmotion
  color: string
  total_weight: number
  feelings: FeelMapItem[]
}

export interface FeelMapResponse {
  emotion_groups: EmotionGroup[]
  dominant_emotion: PrimaryEmotion
  total_feelings: number
  average_intensity: number
}

// ─── API Client ───────────────────────────────────────────────────────────────

class V2ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number
  ) {
    super(message)
    this.name = 'V2ApiError'
  }
}

async function apiRequest<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = apiUrl(path)
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new V2ApiError(
      error.detail || `API error: ${response.status}`,
      response.status
    )
  }
  
  return response.json()
}

// ─── Aimee Extraction API ──────────────────────────────────────────────────────

export async function extractWithAimee(text: string): Promise<ExtractionResponse> {
  return apiRequest<ExtractionResponse>('/v2/aimee/extract', {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export async function confirmAimeeExtraction(
  payload: ConfirmRequest
): Promise<ConfirmResponse> {
  return apiRequest<ConfirmResponse>('/v2/aimee/confirm', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// ─── Aimee Conversational Chat ──────────────────────────────────────────────────

export interface AimeeChatRequest {
  message: string
  context?: string
}

export interface AimeeChatResponse {
  reply: string
}

export async function chatWithAimee(
  message: string,
  context?: string
): Promise<AimeeChatResponse> {
  return apiRequest<AimeeChatResponse>('/aimee/chat', {
    method: 'POST',
    body: JSON.stringify({ message, context }),
  })
}

// ─── Memory API ───────────────────────────────────────────────────────────────

export async function getV2Memories(): Promise<Memory[]> {
  return apiRequest<Memory[]>('/v2/memories')
}

export async function getV2Memory(id: string): Promise<Memory> {
  return apiRequest<Memory>(`/v2/memories/${id}`)
}

// ─── Entity API ───────────────────────────────────────────────────────────────

export async function getV2Entities(): Promise<Entity[]> {
  return apiRequest<Entity[]>('/v2/entities')
}

export async function getV2Entity(id: string): Promise<Entity> {
  return apiRequest<Entity>(`/v2/entities/${id}`)
}

// ─── Need API ─────────────────────────────────────────────────────────────────

export async function getV2Needs(): Promise<Need[]> {
  return apiRequest<Need[]>('/v2/needs')
}

export async function getV2Need(id: string): Promise<Need> {
  return apiRequest<Need>(`/v2/needs/${id}`)
}

// ─── Feel Flow API ────────────────────────────────────────────────────────────

export async function getFeelFlow(params?: {
  days?: number
  time_bucket?: string
  entity_id?: string
}): Promise<FeelFlowResponse> {
  const searchParams = new URLSearchParams()
  if (params?.days) searchParams.set('days', String(params.days))
  if (params?.time_bucket) searchParams.set('time_bucket', params.time_bucket)
  if (params?.entity_id) searchParams.set('entity_id', params.entity_id)
  
  const query = searchParams.toString()
  return apiRequest<FeelFlowResponse>(
    `/v2/feelings/feel-flow${query ? `?${query}` : ''}`
  )
}

// ─── Feel Map API ─────────────────────────────────────────────────────────────

export async function getFeelMap(params?: {
  days?: number
}): Promise<FeelMapResponse> {
  const searchParams = new URLSearchParams()
  if (params?.days) searchParams.set('days', String(params.days))
  
  const query = searchParams.toString()
  return apiRequest<FeelMapResponse>(
    `/v2/feelings/feel-map${query ? `?${query}` : ''}`
  )
}

// ─── Emotion Colors (shared) ──────────────────────────────────────────────────

// Using string index for compatibility with frontend components
export const EMOTION_COLORS: Record<string, string> = {
  joy: '#FFD93D',
  sadness: '#6B9FFF',
  anger: '#FF6B6B',
  fear: '#B794F4',
  disgust: '#6BCB77',
  neutral: '#A3A3A3',
}

export const EMOTION_LABELS: Record<PrimaryEmotion, string> = {
  joy: 'Joy',
  sadness: 'Sadness',
  anger: 'Anger',
  fear: 'Fear',
  disgust: 'Disgust',
}

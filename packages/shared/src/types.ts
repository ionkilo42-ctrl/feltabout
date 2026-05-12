// Shared types for feltabout
// Used by both mobile app and API service

export type ReflectionStatus = "draft" | "completed" | "archived";

export interface User {
  id: string;
  email: string;
  name?: string;
  display_name?: string;
  created_at?: string;
}

export interface Reflection {
  id: string;
  user_id: string;
  title: string;
  situation: string;
  feelings: string;
  interpretation: string;
  needs: string;
  fears: string;
  desired_outcome: string;
  message_draft: string;
  status: ReflectionStatus;
  created_at: string;
  updated_at: string;
  output?: ReflectionOutput | null;
}

export interface ReflectionOutput {
  id: string;
  reflection_id: string;
  simple_opener?: string;
  emotional_summary: string;
  needs_summary: string;
  assumptions: string;
  reframe: string;
  avoid_saying: string;
  conversation_opener: string;
  followup_questions: string;
  repair_statement: string;
  created_at: string;
}

export interface SafetyEvent {
  id: string;
  user_id: string;
  reflection_id: string;
  event_type: string;
  severity: "low" | "medium" | "high" | "critical";
  model_response: string;
  created_at: string;
}

export interface CreateReflectionRequest {
  title: string;
  situation: string;
  feelings: string;
  interpretation: string;
  needs: string;
  fears: string;
  desired_outcome: string;
  message_draft: string;
}

export interface UpdateReflectionRequest {
  title?: string;
  situation?: string;
  feelings?: string;
  interpretation?: string;
  needs?: string;
  fears?: string;
  desired_outcome?: string;
  message_draft?: string;
  status?: ReflectionStatus;
}

export interface GeneratePlanRequest {
  reflection_id: string;
}

export interface CrisisResponse {
  is_crisis: boolean;
  severity: "none" | "low" | "medium" | "high" | "critical";
  message: string;
  resources: string[];
}

export interface GenerateResponse extends CrisisResponse {
  output: ReflectionOutput | null;
}

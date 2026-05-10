import Constants from "expo-constants";
import type {
  Reflection,
  CreateReflectionRequest,
  UpdateReflectionRequest,
  GenerateResponse,
  ReflectionFeedback,
  CreateFeedbackRequest,
} from "../types";

const API_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  Constants.expoConfig?.extra?.apiUrl ??
  (Constants.manifest?.extra as Record<string, string>)?.apiUrl ??
  "http://localhost:8000";

// ─── Reflections ──────────────────────────────────────────────────────────────

export async function listReflections(): Promise<Reflection[]> {
  const resp = await fetch(`${API_URL}/reflections`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!resp.ok) throw new Error(`List failed: ${resp.status}`);
  return resp.json();
}

export async function getReflection(id: string): Promise<Reflection> {
  const resp = await fetch(`${API_URL}/reflections/${id}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!resp.ok) throw new Error(`Get failed: ${resp.status}`);
  return resp.json();
}

export async function createReflection(
  data: CreateReflectionRequest
): Promise<Reflection> {
  const resp = await fetch(`${API_URL}/reflections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`Create failed: ${resp.status}`);
  return resp.json();
}

export async function updateReflection(
  id: string,
  data: UpdateReflectionRequest
): Promise<Reflection> {
  const resp = await fetch(`${API_URL}/reflections/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`Update failed: ${resp.status}`);
  return resp.json();
}

export async function deleteReflection(id: string): Promise<void> {
  const resp = await fetch(`${API_URL}/reflections/${id}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  });
  if (!resp.ok) throw new Error(`Delete failed: ${resp.status}`);
}

export async function generatePlan(
  reflectionId: string
): Promise<GenerateResponse> {
  const resp = await fetch(`${API_URL}/reflections/${reflectionId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!resp.ok) throw new Error(`Generate failed: ${resp.status}`);
  return resp.json();
}

export async function archiveReflection(id: string): Promise<Reflection> {
  return updateReflection(id, { status: "archived" });
}

// ─── Feedback ─────────────────────────────────────────────────────────────────

export async function submitFeedback(
  reflectionId: string,
  data: CreateFeedbackRequest
): Promise<ReflectionFeedback> {
  const resp = await fetch(`${API_URL}/reflections/${reflectionId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`Submit feedback failed: ${resp.status}`);
  return resp.json();
}

export async function getFeedback(
  reflectionId: string
): Promise<ReflectionFeedback> {
  const resp = await fetch(`${API_URL}/reflections/${reflectionId}/feedback`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!resp.ok) throw new Error(`Get feedback failed: ${resp.status}`);
  return resp.json();
}

export async function updateFeedback(
  reflectionId: string,
  data: { conversation_went_better?: number }
): Promise<ReflectionFeedback> {
  const resp = await fetch(`${API_URL}/reflections/${reflectionId}/feedback`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`Update feedback failed: ${resp.status}`);
  return resp.json();
}

import type {
  Reflection,
  CreateReflectionRequest,
  UpdateReflectionRequest,
  GenerateResponse,
  ReflectionFeedback,
  CreateFeedbackRequest,
  UpdateFeedbackRequest,
} from "../types";
import { API_URL, apiHeaders, readError } from "./client";

// ─── Reflections ──────────────────────────────────────────────────────────────

export async function listReflections(): Promise<Reflection[]> {
  const resp = await fetch(`${API_URL}/reflections`, {
    method: "GET",
    headers: await apiHeaders(),
  });
  if (!resp.ok) throw await readError(resp, `List failed: ${resp.status}`);
  return resp.json();
}

export async function getReflection(id: string): Promise<Reflection> {
  const resp = await fetch(`${API_URL}/reflections/${id}`, {
    method: "GET",
    headers: await apiHeaders(),
  });
  if (!resp.ok) throw await readError(resp, `Get failed: ${resp.status}`);
  return resp.json();
}

export async function createReflection(
  data: CreateReflectionRequest
): Promise<Reflection> {
  const resp = await fetch(`${API_URL}/reflections`, {
    method: "POST",
    headers: await apiHeaders(),
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw await readError(resp, `Create failed: ${resp.status}`);
  return resp.json();
}

export async function updateReflection(
  id: string,
  data: UpdateReflectionRequest
): Promise<Reflection> {
  const resp = await fetch(`${API_URL}/reflections/${id}`, {
    method: "PUT",
    headers: await apiHeaders(),
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw await readError(resp, `Update failed: ${resp.status}`);
  return resp.json();
}

export async function deleteReflection(id: string): Promise<void> {
  const resp = await fetch(`${API_URL}/reflections/${id}`, {
    method: "DELETE",
    headers: await apiHeaders(),
  });
  if (!resp.ok) throw await readError(resp, `Delete failed: ${resp.status}`);
}

export async function generatePlan(
  reflectionId: string
): Promise<GenerateResponse> {
  const resp = await fetch(`${API_URL}/reflections/${reflectionId}/generate`, {
    method: "POST",
    headers: await apiHeaders(),
  });
  if (!resp.ok) throw await readError(resp, `Generate failed: ${resp.status}`);
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
    headers: await apiHeaders(),
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw await readError(resp, `Submit feedback failed: ${resp.status}`);
  return resp.json();
}

export async function getFeedback(
  reflectionId: string
): Promise<ReflectionFeedback> {
  const resp = await fetch(`${API_URL}/reflections/${reflectionId}/feedback`, {
    method: "GET",
    headers: await apiHeaders(),
  });
  if (!resp.ok) throw await readError(resp, `Get feedback failed: ${resp.status}`);
  return resp.json();
}

export async function updateFeedback(
  reflectionId: string,
  data: UpdateFeedbackRequest
): Promise<ReflectionFeedback> {
  const resp = await fetch(`${API_URL}/reflections/${reflectionId}/feedback`, {
    method: "PATCH",
    headers: await apiHeaders(),
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw await readError(resp, `Update feedback failed: ${resp.status}`);
  return resp.json();
}

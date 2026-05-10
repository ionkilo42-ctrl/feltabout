import AsyncStorage from "@react-native-async-storage/async-storage";
import type { AuthSession, LoginRequest, RegisterRequest } from "../types";
import { API_URL, AUTH_STORAGE_KEY, apiHeaders, readError } from "./client";

export async function login(data: LoginRequest): Promise<AuthSession> {
  const resp = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw await readError(resp, "Could not sign in.");
  return resp.json();
}

export async function register(data: RegisterRequest): Promise<AuthSession> {
  const resp = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw await readError(resp, "Could not create account.");
  return resp.json();
}

export async function getMe(): Promise<AuthSession["user"]> {
  const resp = await fetch(`${API_URL}/auth/me`, {
    method: "GET",
    headers: await apiHeaders(),
  });
  if (!resp.ok) throw await readError(resp, "Could not load your account.");
  return resp.json();
}

export async function persistSession(session: AuthSession): Promise<void> {
  await AsyncStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export async function loadPersistedSession(): Promise<AuthSession | null> {
  const raw = await AsyncStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as AuthSession;
    if (!parsed.token || !parsed.user?.id) return null;
    return parsed;
  } catch {
    await AsyncStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export async function clearSession(): Promise<void> {
  await AsyncStorage.removeItem(AUTH_STORAGE_KEY);
}

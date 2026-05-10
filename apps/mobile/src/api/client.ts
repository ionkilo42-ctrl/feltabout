import Constants from "expo-constants";
import AsyncStorage from "@react-native-async-storage/async-storage";

export const API_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  Constants.expoConfig?.extra?.apiUrl ??
  (Constants.manifest?.extra as Record<string, string>)?.apiUrl ??
  "http://localhost:8000";

export const AUTH_STORAGE_KEY = "feltabout.mobile.auth";

export async function getStoredToken(): Promise<string> {
  try {
    const raw = await AsyncStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return "";
    const parsed = JSON.parse(raw) as { token?: string };
    return parsed.token ?? "";
  } catch {
    return "";
  }
}

export async function apiHeaders(): Promise<Record<string, string>> {
  const token = await getStoredToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function readError(resp: Response, fallback: string): Promise<Error> {
  try {
    const data = await resp.json();
    return new Error(data.detail || fallback);
  } catch {
    return new Error(fallback);
  }
}

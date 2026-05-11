import { getToken } from "./auth";
import type { CreateTripRequest, Trip, User } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  try {
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers, signal: controller.signal });

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out. Please check your connection and try again.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  auth: {
    me: () => request<User>("/api/auth/me"),
    googleLoginUrl: () => `${API_BASE}/api/auth/google`,
  },
  trips: {
    create: (data: CreateTripRequest) =>
      request<Trip>("/api/trips/", { method: "POST", body: JSON.stringify(data) }),
    list: () => request<Trip[]>("/api/trips/"),
    get: (id: string) => request<Trip>(`/api/trips/${id}`),
    delete: (id: string) => request<void>(`/api/trips/${id}`, { method: "DELETE" }),
  },
};

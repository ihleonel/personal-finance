import type { AuthSession, AuthTokens, ProfileInput } from "@/lib/schemas"
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/auth/storage"

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(status: number, data: unknown, message?: string) {
    super(message ?? `Request failed with status ${status}`)
    this.name = "ApiError"
    this.status = status
    this.data = data
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: unknown
  headers?: Record<string, string>
  skipAuth?: boolean
}

const AUTH_FREE_PATHS = new Set(["/auth/login/", "/auth/register/", "/auth/refresh/"])

let onUnauthorized: (() => void) | null = null

export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler
}

async function refreshTokens(): Promise<AuthTokens | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null
  try {
    const res = await fetch("/api/auth/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { access: string; refresh?: string }
    const next: AuthTokens = {
      access: data.access,
      refresh: data.refresh ?? refresh,
    }
    setTokens(next)
    return next
  } catch {
    return null
  }
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(opts.body !== undefined ? { "Content-Type": "application/json" } : {}),
    ...opts.headers,
  }

  if (!opts.skipAuth && !AUTH_FREE_PATHS.has(path)) {
    const token = getAccessToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const init: RequestInit = {
    method: opts.method ?? "GET",
    headers,
  }
  if (opts.body !== undefined) {
    init.body = JSON.stringify(opts.body)
  }

  const res = await fetch(`/api${path}`, init)

  if (
    res.status === 401 &&
    !opts.skipAuth &&
    !AUTH_FREE_PATHS.has(path) &&
    getRefreshToken()
  ) {
    const refreshed = await refreshTokens()
    if (refreshed) {
      return request<T>(path, opts)
    }
    clearTokens()
    onUnauthorized?.()
  }

  if (!res.ok) {
    const data: unknown = await res.json().catch(() => null)
    throw new ApiError(res.status, data)
  }

  if (res.status === 204) {
    return undefined as T
  }
  return (await res.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
}

export async function loginRequest(email: string, password: string): Promise<AuthSession> {
  return api.post<AuthSession>("/auth/login/", { email, password })
}

export async function registerRequest(input: {
  email: string
  password: string
  first_name: string
  last_name: string
}): Promise<AuthSession> {
  return api.post<AuthSession>("/auth/register/", input)
}

export async function logoutRequest(refresh: string): Promise<void> {
  await api.post<void>("/auth/logout/", { refresh })
}

export async function fetchCurrentUser(): Promise<AuthSession["user"]> {
  return api.get<AuthSession["user"]>("/auth/me/")
}

export async function fetchProfile(): Promise<AuthSession["user"]> {
  return api.get<AuthSession["user"]>("/auth/profile/")
}

export async function updateProfile(
  input: ProfileInput,
): Promise<AuthSession["user"]> {
  return api.patch<AuthSession["user"]>("/auth/profile/", input)
}

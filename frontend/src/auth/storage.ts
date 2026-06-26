import type { AuthTokens } from "@/lib/schemas"

const ACCESS_KEY = "pf.access"
const REFRESH_KEY = "pf.refresh"

export function setTokens(tokens: AuthTokens): void {
  localStorage.setItem(ACCESS_KEY, tokens.access)
  localStorage.setItem(REFRESH_KEY, tokens.refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function hasTokens(): boolean {
  return Boolean(getAccessToken() && getRefreshToken())
}

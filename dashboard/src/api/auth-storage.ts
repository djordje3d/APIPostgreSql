export const ACCESS_TOKEN_KEY = 'access_token'
export const TOKEN_EXPIRES_AT_KEY = 'token_expires_at'

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  } catch {
    return null
  }
}

/** Expiration timestamp (ms since epoch) if stored; null otherwise. */
export function getStoredTokenExpiresAt(): number | null {
  try {
    const v = localStorage.getItem(TOKEN_EXPIRES_AT_KEY)
    if (v == null) return null
    const n = parseInt(v, 10)
    return Number.isFinite(n) ? n : null
  } catch {
    return null
  }
}

/**
 * Store token and optional expiry.
 * @param token - JWT access token
 * @param expiresInSeconds - from API (expires_in); if provided, we store expires_at for proactive logout
 */
export function setStoredToken(token: string, expiresInSeconds?: number): void {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, token)
    if (expiresInSeconds != null && expiresInSeconds > 0) {
      const expiresAt = Date.now() + expiresInSeconds * 1000
      localStorage.setItem(TOKEN_EXPIRES_AT_KEY, String(expiresAt))
    } else {
      localStorage.removeItem(TOKEN_EXPIRES_AT_KEY)
    }
  } catch {
    // ignore
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(TOKEN_EXPIRES_AT_KEY)
  } catch {
    // ignore
  }
}

export function isAuthenticated(): boolean {
  return !!getStoredToken()
}

/**
 * Milliseconds until token expires; 0 if already expired; null if no expiry stored.
 * Use this to schedule proactive logout (setTimeout(clearAndRedirect, ms)).
 */
export function getMsUntilTokenExpiry(): number | null {
  const expiresAt = getStoredTokenExpiresAt()
  if (expiresAt == null) return null
  const ms = expiresAt - Date.now()
  return ms <= 0 ? 0 : ms
}

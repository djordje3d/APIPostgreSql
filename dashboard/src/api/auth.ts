import { api } from './client'
import { setStoredToken } from './auth-storage'

export { getStoredToken, setStoredToken, clearStoredToken, isAuthenticated, ACCESS_TOKEN_KEY } from './auth-storage'

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

/**
 * POST /auth/login with username and password. Returns token response.
 * On success, stores the token via setStoredToken.
 */
export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login', { username, password })
  setStoredToken(data.access_token, data.expires_in)
  return data
}

/**
 * POST /auth/refresh: get a new access token while the current one is still valid.
 * On success, stores the new token and returns it. Use after user activity to extend the session.
 */
export async function refresh(): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/refresh')
  setStoredToken(data.access_token, data.expires_in)
  return data
}

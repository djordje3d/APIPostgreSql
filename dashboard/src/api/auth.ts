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

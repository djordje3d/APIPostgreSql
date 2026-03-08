import axios from 'axios'
import { getStoredToken } from './auth-storage'

// Default to backend dev URL so dashboard works without .env; override with VITE_API_URL.
export const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const apiKey = import.meta.env.VITE_API_KEY || ''

/** Optional request config for cancel/abort (e.g. dashboard refresh). */
export interface ApiRequestConfig {
  signal?: AbortSignal
}

export const api = axios.create({
  baseURL,
  timeout: 5000, // 5 seconds - added to fix the issue of the dashboard not refreshing when the backend is not responding
  // timeout can be adjusted as needed for "3G" testing
  headers: {
    'Content-Type': 'application/json',
    ...(apiKey ? { 'X-API-Key': apiKey } : {}),
  },
})

// Prefer Bearer token when present; set on every request.
api.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    // Remove X-API-Key when using token so backend uses JWT
    delete config.headers['X-API-Key']
  }
  return config
})

// Notify app when API is unreachable (e.g. backend not running) or request timed out.
// On 401: clear token and redirect to login.
// Do not show connection banner for aborted requests (intentional cancel).
api.interceptors.response.use(
  (response) => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('api-connection-ok'))
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      const path = window.location.pathname
      if (path !== '/login') {
        // Let App.vue show "session expired" modal and then redirect
        window.dispatchEvent(new CustomEvent('session-expired'))
      }
    }
    if (error.code === 'ERR_CANCELED' && typeof window !== 'undefined') {
      return Promise.reject(error)
    }
    const isTimeout =
      error.code === 'ECONNABORTED' || error.message?.toLowerCase().includes('timeout')
    const isNetworkError =
      error.code === 'ERR_NETWORK' ||
      error.message?.includes('Network Error') ||
      error.message?.includes('connection refused')
    if (typeof window !== 'undefined') {
      if (isTimeout) {
        window.dispatchEvent(new CustomEvent('api-connection-timeout', { detail: { baseURL } }))
      } else if (isNetworkError) {
        window.dispatchEvent(new CustomEvent('api-connection-error', { detail: { baseURL } }))
      }
    }
    return Promise.reject(error)
  }
)

export default api

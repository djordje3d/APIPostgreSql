import axios from 'axios'
import { clearStoredToken, getStoredToken } from './auth-storage'

// Default to backend dev URL so dashboard works without .env; override with VITE_API_URL.
export const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const apiKey = import.meta.env.VITE_API_KEY || ''

export const api = axios.create({
  baseURL,
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

// Notify app when API is unreachable (e.g. backend not running) so we can show a message.
// On 401: clear token and redirect to login.
api.interceptors.response.use(
  (response) => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('api-connection-ok'))
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      clearStoredToken()
      const path = window.location.pathname
      if (path !== '/login') {
        window.location.href = '/login'
      }
    }
    const isNetworkError =
      error.code === 'ERR_NETWORK' ||
      error.message?.includes('Network Error') ||
      error.message?.includes('connection refused')
    if (isNetworkError && typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('api-connection-error', { detail: { baseURL } }))
    }
    return Promise.reject(error)
  }
)

export default api

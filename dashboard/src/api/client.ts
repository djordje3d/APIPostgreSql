import axios from 'axios'

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

// Notify app when API is unreachable (e.g. backend not running) so we can show a message.
api.interceptors.response.use(
  (response) => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('api-connection-ok'))
    }
    return response
  },
  (error) => {
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

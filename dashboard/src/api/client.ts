import axios from 'axios'

// Default to backend dev URL so dashboard works without .env; override with VITE_API_URL.
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const apiKey = import.meta.env.VITE_API_KEY || ''

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
    ...(apiKey ? { 'X-API-Key': apiKey } : {}),
  },
})

export default api

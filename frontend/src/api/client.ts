import axios from 'axios'

// In development: Vite proxy sends /api → localhost:8000
// In production (Render): VITE_API_BASE_URL points to the deployed backend
//   e.g. https://bioarbitrage-backend.onrender.com
const baseURL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : '/api'

const client = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT from localStorage on every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect to login on 401 ONLY if the user had a stored token
// (i.e. their session expired). Do NOT redirect if there was no token
// — that would break public pages like the Landing Page that make
// optional API calls and handle errors silently with .catch(() => {}).
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const hadToken = !!localStorage.getItem('access_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      if (hadToken) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default client

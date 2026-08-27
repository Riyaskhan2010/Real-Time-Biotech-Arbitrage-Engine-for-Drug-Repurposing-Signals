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

// Redirect to login on 401 when the user has an active authenticated session
// (i.e. their token expired while using the app).
//
// IMPORTANT: Do NOT redirect during:
//   - initAuth startup validation (handled by authStore.initAuth)
//   - login attempts (401 means wrong credentials, not expired session)
//
// We detect "active session" by checking the flag set by the auth store.
// Using window.location.href would cause a full page reload and break
// the React state machine. Instead we dispatch a custom event that
// authStore listens for and handles via React Router.
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Only force-logout if we had a valid authenticated session.
      // Skip during initAuth (isInitializing) and during login attempts.
      const token = localStorage.getItem('access_token')
      if (token) {
        // Token exists but was rejected — session expired mid-use.
        // Clear credentials and reload to login page cleanly.
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        // Use location.replace (not href assignment) to avoid
        // adding a broken dashboard entry to browser history.
        window.location.replace('/login')
      }
    }
    return Promise.reject(err)
  }
)

export default client

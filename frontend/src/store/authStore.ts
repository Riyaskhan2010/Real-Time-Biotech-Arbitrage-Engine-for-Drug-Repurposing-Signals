import { create } from 'zustand'
import type { User } from '../types'
import { authApi } from '../api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  isInitializing: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  clearError: () => void
  initAuth: () => Promise<void>
}

const storedToken = localStorage.getItem('access_token')
const storedUser  = localStorage.getItem('user')

export const useAuthStore = create<AuthState>((set) => ({
  user:             storedUser ? JSON.parse(storedUser) : null,
  token:            storedToken,
  isAuthenticated:  !!storedToken,
  isLoading:        false,
  isInitializing:   !!storedToken,  // true on start if a token exists — we'll validate it
  error:            null,

  /**
   * Validate the stored token against /api/auth/me on app startup.
   *
   * Uses a raw fetch (not the axios client) so the response interceptor
   * does NOT fire during this check. If the token is expired, we clean up
   * here without triggering a page reload — the Layout/Router then redirects
   * to /login cleanly via React state, not a full browser navigation.
   */
  initAuth: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isInitializing: false })
      return
    }
    try {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const user: User = await res.json()
        set({ user, isAuthenticated: true, isInitializing: false })
        localStorage.setItem('user', JSON.stringify(user))
      } else {
        // Token invalid or expired — clear state, React Router will redirect
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        set({ user: null, token: null, isAuthenticated: false, isInitializing: false })
      }
    } catch {
      // Network error — assume token still valid to avoid false logout
      // (e.g. backend temporarily down shouldn't log the user out)
      set({ isInitializing: false })
    }
  },

  login: async (username, password) => {
    set({ isLoading: true, error: null })
    try {
      const data = await authApi.login(username, password)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      set({ user: data.user, token: data.access_token, isAuthenticated: true, isLoading: false })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Login failed. Please check your credentials.'
      set({ error: msg, isLoading: false })
      throw err
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    set({ user: null, token: null, isAuthenticated: false })
  },

  clearError: () => set({ error: null }),
}))

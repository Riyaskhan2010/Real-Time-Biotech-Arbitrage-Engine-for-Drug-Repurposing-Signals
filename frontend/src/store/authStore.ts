import { create } from 'zustand'
import type { User } from '../types'
import { authApi } from '../api'
import client from '../api/client'

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
   * If the token is expired or invalid, clear it so the user is sent to login
   * BEFORE the dashboard attempts to load protected data.
   * This prevents the "Failed to load dashboard data" flash.
   */
  initAuth: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isInitializing: false })
      return
    }
    try {
      const { data } = await client.get<User>('/auth/me')
      set({ user: data, isAuthenticated: true, isInitializing: false })
      localStorage.setItem('user', JSON.stringify(data))
    } catch {
      // Token invalid or expired — clean up silently
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      set({ user: null, token: null, isAuthenticated: false, isInitializing: false })
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

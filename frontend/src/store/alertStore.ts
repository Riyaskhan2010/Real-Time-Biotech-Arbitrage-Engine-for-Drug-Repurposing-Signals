import { create } from 'zustand'
import { alertsApi } from '../api'

/**
 * Centralised alert state so the Header badge doesn't make
 * a separate API call on every page mount.
 */
interface AlertState {
  unreadCount: number
  lastFetchedAt: number | null
  fetchUnreadCount: () => Promise<void>
  decrement: () => void
  reset: () => void
}

const CACHE_MS = 30_000 // re-fetch at most once per 30 s

export const useAlertStore = create<AlertState>((set, get) => ({
  unreadCount: 0,
  lastFetchedAt: null,

  fetchUnreadCount: async () => {
    const { lastFetchedAt } = get()
    if (lastFetchedAt && Date.now() - lastFetchedAt < CACHE_MS) return
    try {
      const count = await alertsApi.unreadCount()
      set({ unreadCount: count, lastFetchedAt: Date.now() })
    } catch {
      // silently ignore — badge will show 0
    }
  },

  decrement: () =>
    set((s) => ({ unreadCount: Math.max(0, s.unreadCount - 1) })),

  reset: () => set({ unreadCount: 0, lastFetchedAt: null }),
}))

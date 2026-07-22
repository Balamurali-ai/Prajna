/**
 * ====================================================
 * Auth Store (Zustand)
 * ====================================================
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import { authApi } from '@api/index'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  expiresAt: number | null
  isAuthenticated: boolean
  isGuest: boolean
  isLoading: boolean
  error: string | null

  // Actions
  setSession: (token: string, user: User, expiresIn: number) => void
  setUser: (user: User) => void
  loginAsGuest: () => void
  logout: () => void
  fetchMe: () => Promise<void>
  clearError: () => void
}

const GUEST_USER: User = {
  id: 'guest',
  email: 'guest@prajna.local',
  full_name: 'Guest',
  role: 'guest',
  created_at: new Date().toISOString(),
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      expiresAt: null,
      isAuthenticated: false,
      isGuest: false,
      isLoading: false,
      error: null,

      setSession: (token, user, expiresIn) => {
        set({
          token,
          user,
          expiresAt: Date.now() + expiresIn * 1000,
          isAuthenticated: true,
          isGuest: false,
          error: null,
        })
      },

      setUser: (user) => set({ user }),

      loginAsGuest: () => {
        set({
          user: GUEST_USER,
          token: null,
          expiresAt: null,
          isAuthenticated: true,
          isGuest: true,
          error: null,
        })
      },

      logout: () => {
        set({
          user: null,
          token: null,
          expiresAt: null,
          isAuthenticated: false,
          isGuest: false,
        })
      },

      fetchMe: async () => {
        if (!get().token) return
        set({ isLoading: true, error: null })
        try {
          const user = await authApi.me()
          set({ user, isLoading: false })
        } catch {
          set({ isLoading: false })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'crime-intel-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        expiresAt: state.expiresAt,
        isAuthenticated: state.isAuthenticated,
        isGuest: state.isGuest,
      }),
    }
  )
)

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
  isLoading: boolean
  error: string | null

  // Actions
  setSession: (token: string, user: User, expiresIn: number) => void
  setUser: (user: User) => void
  logout: () => void
  fetchMe: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      expiresAt: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setSession: (token, user, expiresIn) => {
        localStorage.setItem('access_token', token)
        set({
          token,
          user,
          expiresAt: Date.now() + expiresIn * 1000,
          isAuthenticated: true,
          error: null,
        })
      },

      setUser: (user) => set({ user }),

      logout: () => {
        localStorage.removeItem('access_token')
        set({
          user: null,
          token: null,
          expiresAt: null,
          isAuthenticated: false,
        })
      },

      fetchMe: async () => {
        if (!get().token) return
        set({ isLoading: true, error: null })
        try {
          const user = await authApi.me()
          set({ user, isLoading: false })
        } catch (err) {
          set({ isLoading: false, error: (err as Error).message })
          get().logout()
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
      }),
    }
  )
)

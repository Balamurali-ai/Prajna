/**
 * ====================================================
 * UI Store (Zustand)
 * ====================================================
 * Theme, sidebar, modals, filters, etc.
 * ====================================================
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { RiskFilters, HotspotFilters } from '@/types'

interface UIState {
  // Sidebar
  sidebarOpen: boolean
  toggleSidebar: () => void
  setSidebar: (open: boolean) => void

  // Filters
  riskFilters: RiskFilters
  setRiskFilters: (filters: RiskFilters) => void
  resetRiskFilters: () => void

  hotspotFilters: HotspotFilters
  setHotspotFilters: (filters: HotspotFilters) => void
  resetHotspotFilters: () => void

  // Map
  mapView: {
    center: [number, number]
    zoom: number
  }
  setMapView: (view: { center: [number, number]; zoom: number }) => void

  // Selected district (for district details page)
  selectedDistrict: string | null
  setSelectedDistrict: (district: string | null) => void

  // Notifications (toasts)
  notifications: Array<{
    id: string
    type: 'success' | 'error' | 'info' | 'warning'
    message: string
    duration?: number
  }>
  addNotification: (
    n: Omit<UIState['notifications'][0], 'id'>
  ) => void
  removeNotification: (id: string) => void
}

const defaultRiskFilters: RiskFilters = {}
const defaultHotspotFilters: HotspotFilters = {}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      toggleSidebar: () =>
        set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setSidebar: (open) => set({ sidebarOpen: open }),

      riskFilters: defaultRiskFilters,
      setRiskFilters: (filters) => set({ riskFilters: filters }),
      resetRiskFilters: () => set({ riskFilters: defaultRiskFilters }),

      hotspotFilters: defaultHotspotFilters,
      setHotspotFilters: (filters) => set({ hotspotFilters: filters }),
      resetHotspotFilters: () => set({ hotspotFilters: defaultHotspotFilters }),

      mapView: { center: [78.9629, 20.5937], zoom: 4 },
      setMapView: (view) => set({ mapView: view }),

      selectedDistrict: null,
      setSelectedDistrict: (district) => set({ selectedDistrict: district }),

      notifications: [],
      addNotification: (n) => {
        const id = `n-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
        set((s) => ({ notifications: [...s.notifications, { ...n, id }] }))
        if (n.duration !== 0) {
          setTimeout(() => {
            set((s) => ({
              notifications: s.notifications.filter((x) => x.id !== id),
            }))
          }, n.duration ?? 5000)
        }
      },
      removeNotification: (id) =>
        set((s) => ({
          notifications: s.notifications.filter((x) => x.id !== id),
        })),
    }),
    {
      name: 'crime-intel-ui',
      partialize: (s) => ({
        sidebarOpen: s.sidebarOpen,
        mapView: s.mapView,
      }),
    }
  )
)

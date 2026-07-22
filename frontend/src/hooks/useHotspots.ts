/**
 * ====================================================
 * React Query Hooks — Hotspots
 * ====================================================
 */
import { useQuery, type UseQueryOptions } from '@tanstack/react-query'

import { hotspotApi } from '@api/index'
import type { HotspotGeoJSON, HotspotRanking } from '@/types'

export const hotspotKeys = {
  all: ['hotspots'] as const,
  list: () => [...hotspotKeys.all, 'list'] as const,
  top: (n?: number) => [...hotspotKeys.all, 'top', n] as const,
  geojson: () => [...hotspotKeys.all, 'geojson'] as const,
}

export function useHotspots(
  options?: Omit<UseQueryOptions<HotspotRanking[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<HotspotRanking[]>({
    queryKey: hotspotKeys.list(),
    queryFn: () => hotspotApi.getAll(),
    staleTime: 5 * 60_000,
    ...options,
  })
}

export function useTopHotspots(
  n?: number,
  options?: Omit<UseQueryOptions<HotspotRanking[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<HotspotRanking[]>({
    queryKey: hotspotKeys.top(n),
    queryFn: () => hotspotApi.getTop(n),
    staleTime: 5 * 60_000,
    ...options,
  })
}

export function useHotspotGeoJSON(
  options?: Omit<UseQueryOptions<HotspotGeoJSON>, 'queryKey' | 'queryFn'>
) {
  return useQuery<HotspotGeoJSON>({
    queryKey: hotspotKeys.geojson(),
    queryFn: () => hotspotApi.getGeoJSON(),
    staleTime: 10 * 60_000,
    ...options,
  })
}

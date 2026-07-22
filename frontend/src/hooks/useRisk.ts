/**
 * ====================================================
 * React Query Hooks — Dashboard & Risk
 * ====================================================
 */
import { useQuery, type UseQueryOptions } from '@tanstack/react-query'

import { dashboardApi, riskApi } from '@api/index'
import type {
  DashboardData,
  DistrictPrediction,
  RiskFilters,
  RiskRanking,
} from '@/types'

// Query keys
export const queryKeys = {
  dashboard: {
    all: ['dashboard'] as const,
    full: () => [...queryKeys.dashboard.all, 'full'] as const,
    metrics: () => [...queryKeys.dashboard.all, 'metrics'] as const,
  },
  risk: {
    all: ['risk'] as const,
    list: (filters?: RiskFilters) => [...queryKeys.risk.all, 'list', filters] as const,
    top: (n: number) => [...queryKeys.risk.all, 'top', n] as const,
    district: (name: string) => [...queryKeys.risk.all, 'district', name] as const,
  },
} as const

// ====================================================
// Dashboard
// ====================================================
export function useDashboard(
  options?: Omit<UseQueryOptions<DashboardData>, 'queryKey' | 'queryFn'>
) {
  return useQuery<DashboardData>({
    queryKey: queryKeys.dashboard.full(),
    queryFn: () => dashboardApi.getFull(),
    staleTime: 60_000,
    refetchInterval: 5 * 60_000,
    ...options,
  })
}

// ====================================================
// Risk
// ====================================================
export function useRiskRankings(
  filters?: RiskFilters,
  options?: Omit<UseQueryOptions<RiskRanking[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<RiskRanking[]>({
    queryKey: queryKeys.risk.list(filters),
    queryFn: () => riskApi.getAll(filters),
    staleTime: 5 * 60_000,
    ...options,
  })
}

export function useTopDistricts(
  n = 10,
  options?: Omit<
    UseQueryOptions<{ top_n: number; districts: RiskRanking[] }>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<{ top_n: number; districts: RiskRanking[] }>({
    queryKey: queryKeys.risk.top(n),
    queryFn: () => riskApi.getTopN(n),
    staleTime: 5 * 60_000,
    ...options,
  })
}

export function useDistrict(
  name: string | null,
  options?: Omit<UseQueryOptions<DistrictPrediction>, 'queryKey' | 'queryFn' | 'enabled'>
) {
  return useQuery<DistrictPrediction>({
    queryKey: queryKeys.risk.district(name ?? ''),
    queryFn: () => riskApi.getDistrict(name!),
    enabled: !!name,
    staleTime: 5 * 60_000,
    ...options,
  })
}

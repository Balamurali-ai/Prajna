/**
 * ====================================================
 * React Query Hooks — Analytics, Explainability, Reports
 * ====================================================
 */
import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from '@tanstack/react-query'

import { analyticsApi, explainabilityApi, reportsApi } from '@api/index'
import type {
  AnalyticsReport,
  CategoryDistribution,
  DistrictExplanation,
  GlobalExplanation,
  NeighborInfluence,
  Report,
  ReportFormat,
  ReportType,
  Seasonality,
  TrendsData,
} from '@/types'

// ====================================================
// Analytics
// ====================================================
export const analyticsKeys = {
  all: ['analytics'] as const,
  full: () => [...analyticsKeys.all, 'full'] as const,
  trends: () => [...analyticsKeys.all, 'trends'] as const,
  seasonality: () => [...analyticsKeys.all, 'seasonality'] as const,
  categories: () => [...analyticsKeys.all, 'categories'] as const,
  neighbor: () => [...analyticsKeys.all, 'neighbor'] as const,
}

export function useAnalytics(
  options?: Omit<UseQueryOptions<AnalyticsReport>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AnalyticsReport>({
    queryKey: analyticsKeys.full(),
    queryFn: () => analyticsApi.getFull(),
    staleTime: 10 * 60_000,
    ...options,
  })
}

export function useTrends(
  options?: Omit<UseQueryOptions<TrendsData>, 'queryKey' | 'queryFn'>
) {
  return useQuery<TrendsData>({
    queryKey: analyticsKeys.trends(),
    queryFn: () => analyticsApi.getTrends(),
    staleTime: 10 * 60_000,
    ...options,
  })
}

export function useSeasonality(
  options?: Omit<UseQueryOptions<Seasonality>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Seasonality>({
    queryKey: analyticsKeys.seasonality(),
    queryFn: () => analyticsApi.getSeasonality(),
    staleTime: 10 * 60_000,
    ...options,
  })
}

export function useCategoryDistribution(
  options?: Omit<UseQueryOptions<CategoryDistribution>, 'queryKey' | 'queryFn'>
) {
  return useQuery<CategoryDistribution>({
    queryKey: analyticsKeys.categories(),
    queryFn: () => analyticsApi.getCategories(),
    staleTime: 10 * 60_000,
    ...options,
  })
}

export function useNeighborInfluence(
  options?: Omit<UseQueryOptions<NeighborInfluence>, 'queryKey' | 'queryFn'>
) {
  return useQuery<NeighborInfluence>({
    queryKey: analyticsKeys.neighbor(),
    queryFn: () => analyticsApi.getNeighborInfluence(),
    staleTime: 10 * 60_000,
    ...options,
  })
}

// ====================================================
// Explainability
// ====================================================
export const explainabilityKeys = {
  all: ['explainability'] as const,
  global: () => [...explainabilityKeys.all, 'global'] as const,
  district: (name: string) => [...explainabilityKeys.all, 'district', name] as const,
}

export function useGlobalExplanation(
  options?: Omit<UseQueryOptions<GlobalExplanation>, 'queryKey' | 'queryFn'>
) {
  return useQuery<GlobalExplanation>({
    queryKey: explainabilityKeys.global(),
    queryFn: () => explainabilityApi.getGlobal(),
    staleTime: 30 * 60_000,
    ...options,
  })
}

export function useDistrictExplanation(
  district: string | null,
  options?: Omit<UseQueryOptions<DistrictExplanation>, 'queryKey' | 'queryFn' | 'enabled'>
) {
  return useQuery<DistrictExplanation>({
    queryKey: explainabilityKeys.district(district ?? ''),
    queryFn: () => explainabilityApi.getDistrict(district!),
    enabled: !!district,
    staleTime: 5 * 60_000,
    ...options,
  })
}

// ====================================================
// Reports
// ====================================================
export const reportKeys = {
  all: ['reports'] as const,
  list: () => [...reportKeys.all, 'list'] as const,
  detail: (id: string) => [...reportKeys.all, 'detail', id] as const,
}

export function useReports(
  options?: Omit<UseQueryOptions<Report[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Report[]>({
    queryKey: reportKeys.list(),
    queryFn: () => reportsApi.list(),
    staleTime: 30_000,
    ...options,
  })
}

export function useReport(
  id: string,
  options?: Omit<UseQueryOptions<Report>, 'queryKey' | 'queryFn' | 'enabled'>
) {
  return useQuery<Report>({
    queryKey: reportKeys.detail(id),
    queryFn: () => reportsApi.get(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data && (data.status === 'pending' || data.status === 'processing')) {
        return 3000
      }
      return false
    },
    ...options,
  })
}

export function useGenerateReport() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: {
      title: string
      description?: string
      report_type: ReportType
      format: ReportFormat
      filters?: Record<string, unknown>
    }) => reportsApi.generate(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: reportKeys.list() })
    },
  })
}

export function useDeleteReport() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => reportsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: reportKeys.list() })
    },
  })
}

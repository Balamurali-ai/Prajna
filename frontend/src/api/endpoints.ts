/**
 * ====================================================
 * API Endpoint Modules
 * ====================================================
 * One file per resource. Each exports typed
 * functions for React Query hooks.
 * ====================================================
 */
import { del, get, patch, post } from './client'
import { config } from '@config/index'
import type {
  AnalyticsReport,
  CategoryDistribution,
  DashboardData,
  DistrictExplanation,
  DistrictPrediction,
  GlobalExplanation,
  HotspotGeoJSON,
  HotspotRanking,
  NeighborInfluence,
  Report,
  ReportFormat,
  ReportType,
  RiskFilters,
  RiskRanking,
  Seasonality,
  TrendsData,
  User,
} from '@/types'

// ====================================================
// Dashboard
// ====================================================
export const dashboardApi = {
  getFull: () => get<DashboardData>('/dashboard'),
  getMetrics: () => get<DashboardData['metrics']>('/dashboard/metrics'),
}

// ====================================================
// Risk
// ====================================================
export const riskApi = {
  getAll: (filters?: RiskFilters) =>
    get<RiskRanking[]>('/risk/rankings', { params: filters }),
  getTopN: (n = 10) => get<{ top_n: number; districts: RiskRanking[] }>(`/risk/top?n=${n}`),
  getTop10: () => get<{ top_n: number; districts: RiskRanking[] }>('/risk/top10'),
  getDistrict: (district: string) =>
    get<DistrictPrediction>(`/risk/district/${encodeURIComponent(district)}`),
}

// ====================================================
// Hotspots
// ====================================================
export const hotspotApi = {
  getAll: () => get<HotspotRanking[]>('/hotspots'),
  getTop: (n?: number) =>
    get<HotspotRanking[]>(`/hotspots/top${n ? `?n=${n}` : ''}`),
  getGeoJSON: () => get<HotspotGeoJSON>('/hotspots/geojson'),
}

// ====================================================
// Analytics
// ====================================================
export const analyticsApi = {
  getFull: () => get<AnalyticsReport>('/analytics'),
  getTrends: () => get<TrendsData>('/analytics/trends'),
  getSeasonality: () => get<Seasonality>('/analytics/seasonality'),
  getCategories: () => get<CategoryDistribution>('/analytics/categories'),
  getNeighborInfluence: () => get<NeighborInfluence>('/analytics/neighbor-influence'),
}

// ====================================================
// Explainability
// ====================================================
export const explainabilityApi = {
  getGlobal: () => get<GlobalExplanation>('/explainability/global'),
  getDistrict: (district: string) =>
    get<DistrictExplanation>(`/explainability/district/${encodeURIComponent(district)}`),
}

// ====================================================
// Reports
// ====================================================
export const reportsApi = {
  list: () => get<Report[]>('/reports'),
  get: (id: string) => get<Report>(`/reports/${id}`),
  generate: (payload: {
    title: string
    description?: string
    report_type: ReportType
    format: ReportFormat
    filters?: Record<string, unknown>
  }) => post<Report>('/reports/generate', payload),
  downloadUrl: (id: string) =>
    `${config.api.baseUrl}/reports/download/${id}`,
  delete: (id: string) => del<void>(`/reports/${id}`),
}

// ====================================================
// Auth
// ====================================================
export const authApi = {
  me: (token?: string) =>
    get<User>(
      '/auth/me',
      token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
    ),
  login: (email: string, password: string) =>
    post<{ access_token: string; user: User; expires_in: number }>('/auth/login', {
      email,
      password,
    }),
  register: (payload: {
    email: string
    password: string
    full_name?: string
    role?: User['role']
  }) => post<{ access_token: string; user: User }>('/auth/register', payload),
}

// ====================================================
// Admin
// ====================================================
export const adminApi = {
  listUsers: (skip = 0, limit = 50) =>
    get<User[]>(`/admin/users?skip=${skip}&limit=${limit}`),
  getUser: (id: string) => get<User>(`/admin/users/${id}`),
  updateUser: (id: string, payload: Partial<Pick<User, 'role' | 'full_name' | 'department' | 'badge_number'>>) =>
    patch<User>(`/admin/users/${id}`, payload),
  deleteUser: (id: string) => del<void>(`/admin/users/${id}`),
}

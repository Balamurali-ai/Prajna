/**
 * ====================================================
 * Domain Types
 * ====================================================
 * Mirrors backend Pydantic schemas.
 * ====================================================
 */

// ============================
// Common
// ============================
export interface ApiSuccess<T> {
  success: true
  data: T
  message?: string
  request_id?: string
  timestamp: number
}

export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details?: unknown
  }
  request_id?: string
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError

// ============================
// User & Auth
// ============================
export type UserRole = 'admin' | 'officer' | 'analyst' | 'guest'

export interface User {
  id: string
  email: string
  full_name?: string
  role: UserRole
  department?: string
  badge_number?: string
  jurisdiction?: string
  avatar_url?: string
  last_login_at?: string
  created_at: string
}

export interface AuthSession {
  user: User
  access_token: string
  expires_at: number
}

// ============================
// Risk
// ============================
export interface RiskRanking {
  district: string
  state?: string
  risk_score: number
  risk_rank: number
  confidence: number
  predicted_crime_count?: number
}

export interface DistrictPrediction extends RiskRanking {
  additional_metrics?: Record<string, unknown>
}

// ============================
// Hotspot
// ============================
export interface HotspotRanking {
  h3_cell: string
  hotspot_score: number
  rank: number
}

export interface HotspotFeature {
  type: 'Feature'
  geometry: {
    type: string
    coordinates: unknown
  }
  properties: Record<string, unknown>
}

export interface HotspotGeoJSON {
  type: 'FeatureCollection'
  features: HotspotFeature[]
}

// ============================
// Dashboard
// ============================
export interface DashboardMetrics {
  total_crimes: number
  hotspot_count: number
  average_risk_score: number
  high_risk_districts: number
  trend_direction: 'up' | 'down' | 'stable'
}

export interface DashboardAlert {
  type: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  district?: string
  h3_cell?: string
  score?: number
}

export interface DashboardData {
  metrics: DashboardMetrics
  top_districts: RiskRanking[]
  top_hotspots: HotspotRanking[]
  alerts: DashboardAlert[]
  generated_at: number
}

// ============================
// Analytics
// ============================
export interface TrendsData {
  direction: string
  percentage_change?: number
  monthly?: Array<{ month: number | string; value: number }>
  yearly?: Array<{ year: number; value: number }>
  summary?: string
}

export interface Seasonality {
  monthly_pattern?: Array<{ month: string; value: number }>
  weekly_pattern?: Array<{ day: string; value: number }>
  peak_month?: string
  peak_day_of_week?: string
}

export interface CategoryDistribution {
  categories?: Array<{ name: string; count: number; percentage: number }>
  total_crimes?: number
}

export interface NeighborInfluence {
  spatial_lag?: number
  moran_i?: number
  hotspots_clusters?: Array<{ district: string; score: number }>
  summary?: string
}

export interface AnalyticsReport {
  trends?: TrendsData
  seasonality?: Seasonality
  category_distribution?: CategoryDistribution
  neighbor_influence?: NeighborInfluence
  generated_at?: number
}

// ============================
// Explainability
// ============================
export interface FeatureImportance {
  feature: string
  importance: number
  rank?: number
  direction?: 'positive' | 'negative'
}

export interface GlobalExplanation {
  features: FeatureImportance[]
  base_value?: number
  model_type?: string
  summary?: string
}

export interface DistrictExplanation {
  district: string
  base_value: number
  predicted_value: number
  top_features: FeatureImportance[]
  full_features?: Record<string, number>
}

// ============================
// Reports
// ============================
export type ReportType =
  | 'dashboard_summary'
  | 'risk_ranking'
  | 'hotspot_analysis'
  | 'district_deep_dive'
  | 'analytics_report'
  | 'explainability'
  | 'custom'

export type ReportFormat = 'csv' | 'pdf' | 'geojson' | 'json'

export type ReportStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'expired'

export interface Report {
  id: string
  title: string
  description?: string
  report_type: ReportType
  format: ReportFormat
  status: ReportStatus
  file_size?: number
  download_count: number
  error_message?: string
  created_at: string
  generation_completed_at?: string
  expires_at?: string
}

// ============================
// Filters
// ============================
export interface RiskFilters {
  state?: string
  district?: string
  min_risk?: number
  max_risk?: number
  year?: number
}

export interface HotspotFilters {
  min_score?: number
  bbox?: [number, number, number, number]
}

// ============================
// WebSocket
// ============================
export type WSMessageType =
  | 'connected'
  | 'pong'
  | 'heartbeat'
  | 'subscribed'
  | 'unsubscribed'
  | 'risk_update'
  | 'hotspot_update'
  | 'report_complete'
  | 'error'

export interface WSMessage {
  type: WSMessageType
  timestamp?: number
  data?: unknown
  message?: string
  channel?: string
}

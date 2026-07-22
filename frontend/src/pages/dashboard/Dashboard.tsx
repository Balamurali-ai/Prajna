/**
 * ====================================================
 * Dashboard Page
 * ====================================================
 */
import {
  AlertTriangle,
  Flame,
  MapPin,
  ShieldAlert,
  TrendingUp,
} from 'lucide-react'

import { AlertsPanel, HotspotTable, KPICard, RiskRankingTable } from '@components/dashboard'
import { useDashboard } from '@hooks/useRisk'
import { formatScore } from '@utils/index'

export function DashboardPage() {
  const { data, isLoading } = useDashboard()

  const metrics = data?.metrics
  const topDistricts = data?.top_districts ?? []
  const topHotspots = data?.top_hotspots ?? []
  const alerts = data?.alerts ?? []

  return (
    <div className="space-y-6 p-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Command Center</h1>
        <p className="text-sm text-muted-foreground">
          Real-time crime intelligence overview
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KPICard
          title="Total Crimes"
          value={metrics?.total_crimes ?? 0}
          icon={ShieldAlert}
          accent="blue"
          loading={isLoading}
        />
        <KPICard
          title="Active Hotspots"
          value={metrics?.hotspot_count ?? 0}
          icon={Flame}
          accent="orange"
          loading={isLoading}
        />
        <KPICard
          title="Average Risk"
          value={formatScore(metrics?.average_risk_score)}
          unit="/100"
          icon={TrendingUp}
          accent="purple"
          loading={isLoading}
        />
        <KPICard
          title="High Risk Districts"
          value={metrics?.high_risk_districts ?? 0}
          icon={AlertTriangle}
          accent="red"
          loading={isLoading}
        />
        <KPICard
          title="Trend"
          value={metrics?.trend_direction?.toUpperCase() ?? '—'}
          icon={MapPin}
          accent="green"
          loading={isLoading}
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Top districts (2 cols) */}
        <div className="space-y-4 xl:col-span-2">
          <div>
            <h2 className="text-lg font-semibold">Top Risk Districts</h2>
            <p className="text-xs text-muted-foreground">
              Ranked by predicted risk score
            </p>
          </div>
          <RiskRankingTable data={topDistricts} loading={isLoading} />
        </div>

        {/* Side panels */}
        <div className="space-y-6">
          <AlertsPanel alerts={alerts} loading={isLoading} />
          <HotspotTable data={topHotspots} loading={isLoading} limit={8} />
        </div>
      </div>
    </div>
  )
}

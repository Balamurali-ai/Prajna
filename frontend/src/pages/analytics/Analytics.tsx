/**
 * ====================================================
 * Analytics Page
 * ====================================================
 */
import { TrendingUp, Calendar, BarChart3, Activity } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@components/ui'
import { CategoryChart, TrendChart } from '@components/charts'
import {
  useAnalytics,
  useCategoryDistribution,
  useNeighborInfluence,
  useSeasonality,
  useTrends,
} from '@hooks/index'
import { formatScore } from '@utils/index'

export function AnalyticsPage() {
  const { data: analytics, isLoading } = useAnalytics()
  const { data: trends } = useTrends()
  const { data: seasonality } = useSeasonality()
  const { data: categories } = useCategoryDistribution()
  const { data: neighbor } = useNeighborInfluence()

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Trend analysis, seasonality, and spatial patterns
        </p>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Trend Direction"
          value={analytics?.trends?.direction?.toUpperCase() ?? '—'}
          icon={TrendingUp}
          loading={isLoading}
        />
        <SummaryCard
          title="Monthly Change"
          value={
            analytics?.trends?.percentage_change
              ? `${analytics.trends.percentage_change.toFixed(1)}%`
              : '—'
          }
          icon={Activity}
          loading={isLoading}
        />
        <SummaryCard
          title="Peak Month"
          value={analytics?.seasonality?.peak_month ?? '—'}
          icon={Calendar}
          loading={isLoading}
        />
        <SummaryCard
          title="Moran's I"
          value={formatScore(analytics?.neighbor_influence?.moran_i)}
          icon={BarChart3}
          loading={isLoading}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <TrendChart
          title="Crime Trend (Monthly)"
          data={trends?.monthly ?? []}
          loading={isLoading}
          color="#3b82f6"
        />
        <CategoryChart
          title="Crime Category Distribution"
          data={categories?.categories ?? []}
          loading={isLoading}
        />
        <TrendChart
          title="Seasonal Pattern"
          data={seasonality?.monthly_pattern ?? []}
          loading={isLoading}
          color="#10b981"
        />
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Spatial Neighbor Influence</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Stat
              label="Moran's I"
              value={formatScore(neighbor?.moran_i)}
            />
            <Stat
              label="Spatial Lag"
              value={formatScore(neighbor?.spatial_lag)}
            />
            <p className="text-xs text-muted-foreground">
              {neighbor?.summary ?? 'No summary available'}
            </p>
            {neighbor?.hotspots_clusters && neighbor.hotspots_clusters.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Top Clusters
                </p>
                {neighbor.hotspots_clusters.slice(0, 5).map((c, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded border border-border/40 bg-background/50 p-2"
                  >
                    <span className="text-sm">{c.district}</span>
                    <span className="font-mono text-xs">{c.score?.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function SummaryCard({
  title,
  value,
  icon: Icon,
  loading,
}: {
  title: string
  value: string
  icon: React.ComponentType<{ className?: string }>
  loading?: boolean
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className="rounded-md bg-primary/10 p-2 text-primary">
          <Icon className="h-4 w-4" />
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
            {title}
          </p>
          <p className="text-lg font-bold">{loading ? '—' : value}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border/40 pb-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="font-mono text-sm font-semibold">{value}</span>
    </div>
  )
}

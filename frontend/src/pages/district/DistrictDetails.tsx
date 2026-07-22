/**
 * ====================================================
 * District Details Page
 * ====================================================
 */
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, MapPin, TrendingUp, ShieldAlert, Brain } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Skeleton } from '@components/ui'
import { SHAPChart, TrendChart } from '@components/charts'
import { useDistrict, useDistrictExplanation, useTrends } from '@hooks/index'
import { formatNumber, formatScore, getRiskBadgeClass, getRiskColor, getRiskLevel } from '@utils/index'

export function DistrictDetailsPage() {
  const { name } = useParams<{ name: string }>()
  const districtName = name ? decodeURIComponent(name) : null

  const { data: district, isLoading } = useDistrict(districtName)
  const { data: explanation, isLoading: explainLoading } =
    useDistrictExplanation(districtName)
  const { data: trends } = useTrends()

  if (isLoading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-12 w-1/3" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (!district) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">District not found</p>
            <Link to="/dashboard">
              <Button variant="outline" className="mt-4">
                Back to Dashboard
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  const level = getRiskLevel(district.risk_score)
  const color = getRiskColor(district.risk_score)

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <Link to="/dashboard" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Back to dashboard
        </Link>
        <div className="mt-2 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold">{district.district}</h1>
              <Badge className={getRiskBadgeClass(district.risk_score)}>
                {level} risk
              </Badge>
            </div>
            {district.state && (
              <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
                <MapPin className="h-3.5 w-3.5" />
                {district.state}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KPIBox label="Risk Score" value={formatScore(district.risk_score)} color={color} />
        <KPIBox label="Rank" value={`#${district.risk_rank}`} />
        <KPIBox label="Confidence" value={`${(district.confidence * 100).toFixed(0)}%`} />
        <KPIBox
          label="Predicted Crimes"
          value={formatNumber(district.predicted_crime_count ?? 0)}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SHAPChart
          title="Top SHAP Drivers"
          features={explanation?.top_features ?? []}
          loading={explainLoading}
        />
        <TrendChart
          title="Historical Trend"
          data={trends?.monthly ?? []}
          color={color}
        />
      </div>

      {/* Additional metrics */}
      {district.additional_metrics &&
        Object.keys(district.additional_metrics).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Brain className="h-4 w-4" />
                Additional Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
                {Object.entries(district.additional_metrics).map(([k, v]) => (
                  <div
                    key={k}
                    className="rounded-md border border-border/60 bg-background/50 p-3"
                  >
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                      {k.replace(/_/g, ' ')}
                    </p>
                    <p className="mt-1 font-mono text-sm font-semibold">
                      {typeof v === 'number' ? v.toFixed(3) : String(v)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
    </div>
  )
}

function KPIBox({
  label,
  value,
  color,
}: {
  label: string
  value: string
  color?: string
}) {
  return (
    <Card className="border-border/60">
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
        <p
          className="mt-1 text-2xl font-bold"
          style={color ? { color } : undefined}
        >
          {value}
        </p>
      </CardContent>
    </Card>
  )
}

// Suppress unused imports
void TrendingUp
void ShieldAlert

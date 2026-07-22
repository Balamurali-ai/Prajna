/**
 * ====================================================
 * SHAP Feature Importance Chart
 * ====================================================
 */
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card, CardContent, CardHeader, CardTitle } from '@components/ui'
import type { FeatureImportance } from '@/types'

interface SHAPChartProps {
  title?: string
  features: FeatureImportance[]
  loading?: boolean
  limit?: number
  height?: number
}

export function SHAPChart({
  title = 'Top SHAP Drivers',
  features,
  loading,
  limit = 10,
  height = 400,
}: SHAPChartProps) {
  const data = features
    ?.slice(0, limit)
    .map((f) => ({
      name: f.feature,
      importance: f.importance,
      direction: f.direction ?? 'positive',
    }))

  return (
    <Card className="border-border/60">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading || !data || data.length === 0 ? (
          <div
            className="flex items-center justify-center rounded bg-muted/30"
            style={{ height }}
          >
            <span className="text-sm text-muted-foreground">No SHAP data</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} layout="vertical" margin={{ left: 80, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis
                type="number"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(148,163,184,0.2)' }}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(148,163,184,0.2)' }}
                tickLine={false}
                width={70}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15,23,42,0.95)',
                  border: '1px solid rgba(148,163,184,0.2)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value: number) => value.toFixed(4)}
              />
              <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                {data.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.direction === 'negative' ? '#f97316' : '#3b82f6'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

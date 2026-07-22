/**
 * ====================================================
 * Trend Chart (Recharts Line)
 * ====================================================
 */
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card, CardContent, CardHeader, CardTitle } from '@components/ui'
import { formatCompact } from '@utils/index'

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

interface TrendChartProps {
  title: string
  data: Array<{ month: number | string; value: number }> | Array<{ year: number; value: number }>
  dataKey?: string
  color?: string
  loading?: boolean
  height?: number
}

export function TrendChart({
  title,
  data,
  dataKey = 'value',
  color = '#3b82f6',
  loading,
  height = 280,
}: TrendChartProps) {
  const xKey = 'month' in (data?.[0] ?? {}) ? 'month' : 'year'
  const displayData = data?.map((d) => {
    const raw = d[xKey as keyof typeof d]
    const label = typeof raw === 'number' && xKey === 'month'
      ? MONTH_NAMES[(raw - 1) % 12]
      : String(raw ?? '')
    return { label, [dataKey]: d.value }
  })

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
            <span className="text-sm text-muted-foreground">No data</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={displayData}>
              <defs>
                <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.4} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis
                dataKey="label"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(148,163,184,0.2)' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(148,163,184,0.2)' }}
                tickLine={false}
                tickFormatter={(v) => formatCompact(v)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15,23,42,0.95)',
                  border: '1px solid rgba(148,163,184,0.2)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Area
                type="monotone"
                dataKey={dataKey}
                stroke={color}
                strokeWidth={2}
                fill={`url(#gradient-${dataKey})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

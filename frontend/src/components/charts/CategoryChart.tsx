/**
 * ====================================================
 * Category Distribution (Donut Chart)
 * ====================================================
 */
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

import { Card, CardContent, CardHeader, CardTitle } from '@components/ui'
import { formatCompact } from '@utils/index'

const COLORS = ['#3b82f6', '#10b981', '#eab308', '#f97316', '#ef4444', '#8b5cf6', '#06b6d4']

interface CategoryChartProps {
  title: string
  data: Array<{ name: string; value: number; percentage: number }>
  loading?: boolean
  height?: number
}

export function CategoryChart({
  title,
  data,
  loading,
  height = 300,
}: CategoryChartProps) {
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
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15,23,42,0.95)',
                  border: '1px solid rgba(148,163,184,0.2)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value: number) => formatCompact(value)}
              />
              <Legend
                verticalAlign="bottom"
                iconType="circle"
                wrapperStyle={{ fontSize: 11, color: '#94a3b8' }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

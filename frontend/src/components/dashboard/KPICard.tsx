/**
 * ====================================================
 * KPI Card
 * ====================================================
 */
import { type LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'

import { Card, CardContent } from '@components/ui'
import { cn, formatCompact, getTrendIcon } from '@utils/index'

export interface KPICardProps {
  title: string
  value: number | string
  unit?: string
  icon?: LucideIcon
  trend?: 'up' | 'down' | 'stable'
  trendValue?: string
  accent?: 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'yellow'
  loading?: boolean
  className?: string
}

const accentClasses: Record<NonNullable<KPICardProps['accent']>, string> = {
  blue: 'from-blue-500/20 to-blue-500/0 text-blue-400 ring-blue-500/30',
  green: 'from-emerald-500/20 to-emerald-500/0 text-emerald-400 ring-emerald-500/30',
  orange: 'from-orange-500/20 to-orange-500/0 text-orange-400 ring-orange-500/30',
  red: 'from-red-500/20 to-red-500/0 text-red-400 ring-red-500/30',
  purple: 'from-purple-500/20 to-purple-500/0 text-purple-400 ring-purple-500/30',
  yellow: 'from-yellow-500/20 to-yellow-500/0 text-yellow-400 ring-yellow-500/30',
}

const trendIcons = {
  up: TrendingUp,
  down: TrendingDown,
  stable: Minus,
}

export function KPICard({
  title,
  value,
  unit,
  icon: Icon,
  trend,
  trendValue,
  accent = 'blue',
  loading,
  className,
}: KPICardProps) {
  const TrendIcon = trend ? trendIcons[trend] : null

  return (
    <Card
      className={cn(
        'relative overflow-hidden border-border/60 bg-gradient-to-br ring-1 ring-inset',
        accentClasses[accent],
        className
      )}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {title}
            </p>
            {loading ? (
              <div className="h-8 w-24 animate-pulse rounded bg-muted/50" />
            ) : (
              <div className="flex items-baseline gap-1">
                <h3 className="text-2xl font-bold tracking-tight text-foreground">
                  {typeof value === 'number' ? formatCompact(value) : value}
                </h3>
                {unit && (
                  <span className="text-sm text-muted-foreground">{unit}</span>
                )}
              </div>
            )}
            {trend && TrendIcon && !loading && (
              <div className="mt-2 flex items-center gap-1 text-xs">
                <TrendIcon className="h-3 w-3" />
                <span>{trendValue ?? getTrendIcon(trend)}</span>
                <span className="text-muted-foreground">vs last period</span>
              </div>
            )}
          </div>
          {Icon && (
            <div className={cn('rounded-lg p-2 ring-1 ring-inset', accentClasses[accent])}>
              <Icon className="h-5 w-5" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

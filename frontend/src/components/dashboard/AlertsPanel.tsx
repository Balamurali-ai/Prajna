/**
 * ====================================================
 * Alerts Panel
 * ====================================================
 */
import { AlertTriangle, AlertOctagon, Info, CheckCircle2 } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@components/ui'
import { cn, formatRelativeTime } from '@utils/index'
import type { DashboardAlert } from '@/types'

const severityConfig = {
  critical: { icon: AlertOctagon, color: 'text-red-400', bg: 'bg-red-500/10' },
  high: { icon: AlertTriangle, color: 'text-orange-400', bg: 'bg-orange-500/10' },
  medium: { icon: Info, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  low: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
} as const

interface AlertsPanelProps {
  alerts: DashboardAlert[]
  loading?: boolean
}

export function AlertsPanel({ alerts, loading }: AlertsPanelProps) {
  return (
    <Card className="border-border/60">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
          Active Alerts
        </CardTitle>
        <span className="text-xs text-muted-foreground">
          {alerts?.length ?? 0}
        </span>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border/40">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="p-4">
                <div className="h-4 w-1/2 animate-pulse rounded bg-muted/40" />
                <div className="mt-2 h-3 w-3/4 animate-pulse rounded bg-muted/40" />
              </div>
            ))
          ) : alerts && alerts.length > 0 ? (
            alerts.map((alert, idx) => {
              const cfg = severityConfig[alert.severity]
              const Icon = cfg.icon
              return (
                <div
                  key={idx}
                  className={cn('flex items-start gap-3 p-4 transition-colors hover:bg-muted/30')}
                >
                  <div className={cn('rounded-md p-2', cfg.bg)}>
                    <Icon className={cn('h-4 w-4', cfg.color)} />
                  </div>
                  <div className="flex-1 space-y-0.5">
                    <p className="text-sm font-medium">{alert.title}</p>
                    <p className="text-xs text-muted-foreground">{alert.description}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {formatRelativeTime(Date.now() - 60_000)}
                  </span>
                </div>
              )
            })
          ) : (
            <div className="p-6 text-center text-sm text-muted-foreground">
              No active alerts
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * ====================================================
 * Hotspot Table
 * ====================================================
 */
import { Flame } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@components/ui'
import { getRiskColor, getRiskLevel } from '@utils/index'
import type { HotspotRanking } from '@/types'

interface HotspotTableProps {
  data: HotspotRanking[]
  loading?: boolean
  limit?: number
}

export function HotspotTable({ data, loading, limit = 20 }: HotspotTableProps) {
  const display = data?.slice(0, limit) ?? []

  return (
    <Card className="border-border/60">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Flame className="h-4 w-4 text-orange-500" />
          Top Hotspots
        </CardTitle>
        <span className="text-xs text-muted-foreground">
          {data?.length ?? 0} total
        </span>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border/40">
          {loading
            ? Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 p-4">
                  <div className="h-8 w-8 animate-pulse rounded bg-muted/40" />
                  <div className="flex-1 space-y-1.5">
                    <div className="h-3 w-1/3 animate-pulse rounded bg-muted/40" />
                    <div className="h-2 w-1/2 animate-pulse rounded bg-muted/40" />
                  </div>
                </div>
              ))
            : display.map((h) => {
                const level = getRiskLevel(h.hotspot_score)
                const color = getRiskColor(h.hotspot_score)
                return (
                  <div
                    key={h.h3_cell}
                    className="flex items-center gap-3 p-4 transition-colors hover:bg-muted/30"
                  >
                    <div
                      className="flex h-9 w-9 items-center justify-center rounded-md ring-1 ring-inset"
                      style={{
                        backgroundColor: `${color}15`,
                        color,
                        borderColor: `${color}40`,
                      }}
                    >
                      <span className="font-mono text-xs font-bold">
                        #{h.rank}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="font-mono text-sm font-medium">
                        {h.h3_cell}
                      </div>
                      <div className="mt-1 h-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full"
                          style={{
                            width: `${Math.min(100, h.hotspot_score)}%`,
                            backgroundColor: color,
                          }}
                        />
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-sm font-bold">
                        {h.hotspot_score.toFixed(1)}
                      </div>
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        {level}
                      </div>
                    </div>
                  </div>
                )
              })}
        </div>
      </CardContent>
    </Card>
  )
}

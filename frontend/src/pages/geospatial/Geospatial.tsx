/**
 * ====================================================
 * Geospatial Intelligence Page
 * ====================================================
 */
import { useState } from 'react'
import { Filter, Layers } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle, Button, Input, Badge } from '@components/ui'
import { MapLegend, MapView } from '@components/map'
import { useHotspots, useRiskRankings } from '@hooks/index'
import { getRiskBadgeClass, getRiskLevel } from '@utils/index'

export function GeospatialPage() {
  const { data: hotspots } = useHotspots()
  const { data: riskData } = useRiskRankings()
  const [showHotspots, setShowHotspots] = useState(true)
  const [showChoropleth, setShowChoropleth] = useState(true)
  const [search, setSearch] = useState('')

  const filteredRisk = riskData?.filter((r) =>
    r.district.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0 overflow-y-auto border-r border-border bg-card p-4">
        <div className="space-y-4">
          {/* Search */}
          <div>
            <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Search
            </label>
            <Input
              placeholder="District name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="mt-1"
            />
          </div>

          {/* Layers */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Layers className="h-4 w-4" />
                Map Layers
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <label className="flex cursor-pointer items-center justify-between">
                <span className="text-sm">Hotspots</span>
                <input
                  type="checkbox"
                  checked={showHotspots}
                  onChange={(e) => setShowHotspots(e.target.checked)}
                  className="h-4 w-4 rounded border-input bg-background"
                />
              </label>
              <label className="flex cursor-pointer items-center justify-between">
                <span className="text-sm">Risk Choropleth</span>
                <input
                  type="checkbox"
                  checked={showChoropleth}
                  onChange={(e) => setShowChoropleth(e.target.checked)}
                  className="h-4 w-4 rounded border-input bg-background"
                />
              </label>
            </CardContent>
          </Card>

          {/* Stats */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Filter className="h-4 w-4" />
                Layer Stats
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Hotspots</span>
                <span className="font-mono font-bold">{hotspots?.length ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Districts</span>
                <span className="font-mono font-bold">{riskData?.length ?? 0}</span>
              </div>
            </CardContent>
          </Card>

          {/* District list */}
          <div>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Districts ({filteredRisk?.length ?? 0})
            </h3>
            <div className="space-y-1.5 max-h-96 overflow-y-auto">
              {filteredRisk?.map((r) => {
                const level = getRiskLevel(r.risk_score)
                return (
                  <button
                    key={r.district}
                    className="flex w-full items-center justify-between rounded-md border border-border/60 bg-background/50 p-2 text-left transition-colors hover:bg-muted"
                  >
                    <div>
                      <p className="text-sm font-medium">{r.district}</p>
                      <p className="text-[10px] text-muted-foreground">
                        Rank #{r.risk_rank}
                      </p>
                    </div>
                    <Badge className={getRiskBadgeClass(r.risk_score)}>
                      {r.risk_score.toFixed(0)}
                    </Badge>
                    {/* Suppress unused */}
                    <span className="hidden">{level}</span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="relative flex-1 p-4">
        <MapView
          showHotspots={showHotspots}
          showRiskChoropleth={showChoropleth}
          height="100%"
        />
        <div className="absolute right-6 top-6">
          <MapLegend />
        </div>
        <div className="absolute left-1/2 top-6 -translate-x-1/2">
          <Button variant="outline" size="sm" className="bg-card/80 backdrop-blur">
            <Layers className="mr-1.5 h-3.5 w-3.5" />
            Toggle Layers
          </Button>
        </div>
      </div>
    </div>
  )
}

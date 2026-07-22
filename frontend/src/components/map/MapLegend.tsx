/**
 * ====================================================
 * Map Legend
 * ====================================================
 */
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui'

const LEGEND_ITEMS = [
  { label: 'Low (0–40)', color: '#10b981' },
  { label: 'Medium (40–60)', color: '#eab308' },
  { label: 'High (60–80)', color: '#f97316' },
  { label: 'Critical (80+)', color: '#ef4444' },
]

export function MapLegend() {
  return (
    <Card className="border-border/60 bg-card/95 backdrop-blur">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">
          Risk Level
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {LEGEND_ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-sm ring-1 ring-inset ring-white/20"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-xs">{item.label}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

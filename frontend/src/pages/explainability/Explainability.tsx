/**
 * ====================================================
 * Explainability Page
 * ====================================================
 */
import { Brain } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@components/ui'
import { SHAPChart } from '@components/charts'
import { useGlobalExplanation } from '@hooks/index'

export function ExplainabilityPage() {
  const { data, isLoading } = useGlobalExplanation()

  const topFeature = data?.features?.[0]

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Explainability</h1>
        <p className="text-sm text-muted-foreground">
          Global SHAP feature importance — what drives the risk model
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">
              Top Driver
            </p>
            <p className="mt-1 text-lg font-bold">
              {topFeature?.feature ?? '—'}
            </p>
            <p className="font-mono text-xs text-muted-foreground">
              Importance: {topFeature?.importance?.toFixed(4) ?? '—'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">
              Total Features
            </p>
            <p className="mt-1 text-lg font-bold">{data?.features?.length ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">
              Model Type
            </p>
            <p className="mt-1 text-lg font-bold">
              {data?.model_type ?? 'Ensemble'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* SHAP chart */}
      <SHAPChart
        title="Global SHAP Feature Importance (Top 20)"
        features={data?.features ?? []}
        loading={isLoading}
        limit={20}
        height={500}
      />

      {/* All features list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Brain className="h-4 w-4" />
            All Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-1 md:grid-cols-2">
            {data?.features?.map((f) => (
              <div
                key={f.feature}
                className="flex items-center justify-between rounded border border-border/40 bg-background/30 p-2"
              >
                <span className="text-sm font-mono">{f.feature}</span>
                <span className="font-mono text-xs text-muted-foreground">
                  {f.importance.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

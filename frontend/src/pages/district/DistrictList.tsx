/**
 * ====================================================
 * District List Page
 * ====================================================
 */
import { useState } from 'react'

import { Card, CardContent, Input } from '@components/ui'
import { RiskRankingTable } from '@components/dashboard'
import { useRiskRankings } from '@hooks/useRisk'

export function DistrictListPage() {
  const { data, isLoading } = useRiskRankings()
  const [search, setSearch] = useState('')

  const filtered = data?.filter((d) =>
    d.district.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Districts</h1>
        <p className="text-sm text-muted-foreground">
          All district risk predictions ranked by score
        </p>
      </div>

      <Card>
        <CardContent className="p-4">
          <Input
            placeholder="Search districts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </CardContent>
      </Card>

      <RiskRankingTable
        data={filtered ?? []}
        loading={isLoading}
        pageSize={20}
      />
    </div>
  )
}

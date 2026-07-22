/**
 * ====================================================
 * Risk Ranking Table
 * ====================================================
 */
import { useNavigate } from 'react-router-dom'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { useState } from 'react'
import { ArrowUpDown, ChevronRight } from 'lucide-react'

import { Badge } from '@components/ui'
import { getRiskBadgeClass, getRiskLevel } from '@utils/index'
import type { RiskRanking } from '@/types'

interface RiskTableProps {
  data: RiskRanking[]
  loading?: boolean
  pageSize?: number
  onRowClick?: (district: string) => void
}

export function RiskRankingTable({
  data,
  loading,
  pageSize = 10,
  onRowClick,
}: RiskTableProps) {
  const navigate = useNavigate()
  const [sorting, setSorting] = useState<SortingState>([{ id: 'risk_rank', desc: false }])

  const columns: ColumnDef<RiskRanking>[] = [
    {
      accessorKey: 'risk_rank',
      header: ({ column }) => (
        <button
          className="flex items-center gap-1 text-xs uppercase tracking-wider"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Rank <ArrowUpDown className="h-3 w-3" />
        </button>
      ),
      cell: ({ row }) => (
        <span className="font-mono text-sm font-bold text-muted-foreground">
          #{row.original.risk_rank}
        </span>
      ),
    },
    {
      accessorKey: 'district',
      header: 'District',
      cell: ({ row }) => (
        <div className="font-medium text-foreground">{row.original.district}</div>
      ),
    },
    {
      accessorKey: 'state',
      header: 'State',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">{row.original.state ?? '—'}</span>
      ),
    },
    {
      accessorKey: 'risk_score',
      header: ({ column }) => (
        <button
          className="flex items-center gap-1 text-xs uppercase tracking-wider"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Risk Score <ArrowUpDown className="h-3 w-3" />
        </button>
      ),
      cell: ({ row }) => {
        const score = row.original.risk_score
        const level = getRiskLevel(score)
        return (
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
              <div
                className={cn_level(level)}
                style={{ width: `${Math.min(100, score)}%` }}
              />
            </div>
            <span className="font-mono text-sm font-semibold">{score.toFixed(1)}</span>
          </div>
        )
      },
    },
    {
      accessorKey: 'confidence',
      header: 'Confidence',
      cell: ({ row }) => (
        <span className="font-mono text-sm">
          {(row.original.confidence * 100).toFixed(0)}%
        </span>
      ),
    },
    {
      accessorKey: 'predicted_crime_count',
      header: 'Predicted',
      cell: ({ row }) => (
        <span className="font-mono text-sm">
          {row.original.predicted_crime_count?.toLocaleString() ?? '—'}
        </span>
      ),
    },
    {
      id: 'actions',
      cell: () => (
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      ),
      enableSorting: false,
    },
  ]

  const table = useReactTable({
    data: data ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  const handleRowClick = (district: string) => {
    if (onRowClick) onRowClick(district)
    else navigate(`/district/${encodeURIComponent(district)}`)
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-muted/30">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left font-medium text-muted-foreground"
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {loading
            ? Array.from({ length: pageSize }).map((_, i) => (
                <tr key={i} className="border-b border-border/40">
                  {columns.map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 w-full animate-pulse rounded bg-muted/40" />
                    </td>
                  ))}
                </tr>
              ))
            : table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => handleRowClick(row.original.district)}
                  className="cursor-pointer border-b border-border/40 transition-colors hover:bg-muted/30"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  )
}

function cn_level(level: 'low' | 'medium' | 'high' | 'critical'): string {
  return {
    low: 'bg-emerald-500',
    medium: 'bg-yellow-500',
    high: 'bg-orange-500',
    critical: 'bg-red-500',
  }[level]
}

// Suppress unused import warning for Badge; kept for future column extension
void Badge
void getRiskBadgeClass

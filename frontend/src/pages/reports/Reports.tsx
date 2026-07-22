/**
 * Reports Page
 */
import { useState } from 'react'
import { Download, FileText, Plus, Trash2, Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { Button, Card, CardContent, CardHeader, CardTitle, Input, Badge } from '@components/ui'
import { useDeleteReport, useGenerateReport, useReports } from '@hooks/index'
import { reportsApi } from '@api/index'
import { useAuthStore } from '@store/index'
import { formatDate, formatRelativeTime, downloadFromUrl } from '@utils/index'
import type { Report, ReportFormat, ReportType } from '@/types'

const REPORT_TYPES: { value: ReportType; label: string }[] = [
  { value: 'dashboard_summary', label: 'Dashboard Summary' },
  { value: 'risk_ranking', label: 'Risk Ranking' },
  { value: 'hotspot_analysis', label: 'Hotspot Analysis' },
  { value: 'analytics_report', label: 'Analytics Report' },
  { value: 'district_deep_dive', label: 'District Deep Dive' },
]

const REPORT_FORMATS: { value: ReportFormat; label: string }[] = [
  { value: 'csv', label: 'CSV' },
  { value: 'pdf', label: 'PDF' },
  { value: 'geojson', label: 'GeoJSON' },
  { value: 'json', label: 'JSON' },
]

interface StatusConfig {
  icon: React.ComponentType<{ className?: string }>
  color: string
  label: string
  spin?: boolean
}

const STATUS_CONFIG: Record<string, StatusConfig> = {
  pending: { icon: Clock, color: 'text-yellow-400', label: 'Pending' },
  processing: { icon: Loader2, color: 'text-blue-400', label: 'Processing', spin: true },
  completed: { icon: CheckCircle2, color: 'text-emerald-400', label: 'Completed' },
  failed: { icon: XCircle, color: 'text-red-400', label: 'Failed' },
  expired: { icon: Clock, color: 'text-slate-400', label: 'Expired' },
}

type FormData = {
  title: string
  description?: string
  report_type: ReportType
  format: ReportFormat
}

export function ReportsPage() {
  const { data: reports, isLoading } = useReports()
  const generate = useGenerateReport()
  const del = useDeleteReport()
  const isGuest = useAuthStore((s) => s.isGuest)
  const [showForm, setShowForm] = useState(false)

  const { register, handleSubmit, reset } = useForm<FormData>({
    defaultValues: {
      title: '',
      description: '',
      report_type: 'dashboard_summary',
      format: 'csv',
    },
  })

  const onGenerate = async (data: FormData) => {
    await generate.mutateAsync(data)
    setShowForm(false)
    reset()
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Reports</h1>
          <p className="text-sm text-muted-foreground">
            Generate, manage, and download intelligence reports
          </p>
        </div>
        {!isGuest && (
          <Button onClick={() => setShowForm(!showForm)}>
            <Plus className="h-4 w-4" />
            New Report
          </Button>
        )}
      </div>

      {!isGuest && showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Generate New Report</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onGenerate)} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Title
                  </label>
                  <Input {...register('title', { required: true })} placeholder="Q1 2026 Risk Report" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Type
                  </label>
                  <select
                    {...register('report_type')}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  >
                    {REPORT_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Format
                  </label>
                  <select
                    {...register('format')}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  >
                    {REPORT_FORMATS.map((f) => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Description
                  </label>
                  <Input {...register('description')} placeholder="Optional" />
                </div>
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={generate.isPending}>
                  {generate.isPending ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Generating...</>
                  ) : (
                    <><FileText className="h-4 w-4" /> Generate</>
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>My Reports ({reports?.length ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : reports && reports.length > 0 ? (
            <div className="divide-y divide-border/40">
              {reports.map((r) => (
                <ReportRow key={r.id} report={r} onDelete={() => del.mutate(r.id)} isGuest={isGuest} />
              ))}
            </div>
          ) : (
            <p className="py-8 text-center text-sm text-muted-foreground">
              {isGuest
                ? 'No reports available in guest mode.'
                : 'No reports yet. Click "New Report" to generate one.'}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function ReportRow({
  report,
  onDelete,
  isGuest,
}: {
  report: Report
  onDelete: () => void
  isGuest: boolean
}) {
  const cfg = STATUS_CONFIG[report.status] ?? STATUS_CONFIG.pending
  const StatusIcon = cfg.icon

  const handleDownload = () => {
    let token: string | null = null
    try {
      const raw = localStorage.getItem('crime-intel-auth')
      token = raw ? (JSON.parse(raw)?.state?.token ?? null) : null
    } catch { /* ignore */ }
    if (!token) return
    fetch(reportsApi.downloadUrl(report.id), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = window.URL.createObjectURL(blob)
        downloadFromUrl(url, `${report.title}.${report.format}`)
        window.URL.revokeObjectURL(url)
      })
  }

  return (
    <div className="flex items-center justify-between p-4 transition-colors hover:bg-muted/30">
      <div className="flex items-center gap-3">
        <div className="rounded-md bg-primary/10 p-2 text-primary">
          <FileText className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-medium">{report.title}</p>
          <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="outline">{report.format.toUpperCase()}</Badge>
            <span>·</span>
            <span>{report.report_type.replace(/_/g, ' ')}</span>
            <span>·</span>
            <span>{formatRelativeTime(report.created_at)}</span>
            {report.file_size && (
              <>
                <span>·</span>
                <span>{(report.file_size / 1024).toFixed(1)} KB</span>
              </>
            )}
          </div>
          {report.expires_at && (
            <p className="mt-0.5 text-[10px] text-muted-foreground">
              Expires {formatDate(report.expires_at)}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="gap-1.5">
          <StatusIcon className={`h-3 w-3 ${cfg.color}${cfg.spin ? ' animate-spin' : ''}`} />
          {cfg.label}
        </Badge>
        {report.status === 'completed' && (
          <Button variant="ghost" size="icon" onClick={handleDownload}>
            <Download className="h-4 w-4" />
          </Button>
        )}
        {!isGuest && (
          <Button variant="ghost" size="icon" onClick={onDelete}>
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}

/**
 * ====================================================
 * Settings Page
 * ====================================================
 */
import { useState } from 'react'
import { Loader2, Check } from 'lucide-react'
import { toast } from 'sonner'

import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@components/ui'
import { useAuthStore } from '@store/index'
import { config } from '@config/index'
import { post } from '@api/client'

export function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const [name, setName] = useState(user?.full_name ?? '')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await post<typeof user>('/auth/me/profile', { full_name: name })
      if (updated && user) setUser({ ...user, full_name: name })
      toast.success('Profile updated')
    } catch {
      // Optimistic update even if backend doesn't have this endpoint yet
      if (user) setUser({ ...user, full_name: name })
      toast.success('Profile updated locally')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Account & preferences</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Full Name
              </label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Email
              </label>
              <Input value={user?.email ?? ''} disabled />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Role
              </label>
              <Input value={user?.role?.toUpperCase() ?? ''} disabled />
            </div>
            {user?.department && (
              <div className="space-y-1.5">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Department
                </label>
                <Input value={user.department} disabled />
              </div>
            )}
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}
              Save Changes
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <Row label="Application" value={config.app.name} />
            <Row label="Version" value={config.app.version} />
            <Row label="Environment" value={config.app.env} />
            <Row label="API URL" value={config.api.baseUrl} />
            <Row label="Mapbox Style" value={config.mapbox.style} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border/40 pb-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-xs">{value}</span>
    </div>
  )
}

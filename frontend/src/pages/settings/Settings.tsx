/**
 * ====================================================
 * Settings Page
 * ====================================================
 */
import { useState } from 'react'

import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@components/ui'
import { useAuthStore } from '@store/index'
import { config } from '@config/index'

export function SettingsPage() {
  const { user } = useAuthStore()
  const [name, setName] = useState(user?.full_name ?? '')

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
            <Button>Save Changes</Button>
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

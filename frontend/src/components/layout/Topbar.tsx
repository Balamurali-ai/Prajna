/**
 * ====================================================
 * Topbar
 * ====================================================
 */
import { useState } from 'react'
import { Bell, LogOut, Search, User as UserIcon } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button, Input, Badge } from '@components/ui'
import { useAuthStore } from '@store/index'

export function Topbar() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [search, setSearch] = useState('')

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (search.trim()) {
      navigate(`/district/${encodeURIComponent(search.trim())}`)
      setSearch('')
    }
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
      {/* Search */}
      <form onSubmit={handleSearch} className="relative max-w-md flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search district..."
          className="pl-9"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </form>

      {/* Right */}
      <div className="flex items-center gap-3">
        <Badge variant="success" className="gap-1.5">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
          Live
        </Badge>

        <Button variant="ghost" size="icon">
          <Bell className="h-4 w-4" />
        </Button>

        <div className="flex items-center gap-3 border-l border-border pl-3">
          <div className="text-right">
            <p className="text-sm font-medium">{user?.full_name ?? user?.email ?? 'User'}</p>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
              {user?.role ?? 'guest'}
            </p>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600">
            <UserIcon className="h-4 w-4 text-white" />
          </div>
          <Button variant="ghost" size="icon" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}

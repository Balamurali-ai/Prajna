/**
 * ====================================================
 * Sidebar
 * ====================================================
 */
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Map as MapIcon,
  BarChart3,
  Brain,
  FileText,
  Users,
  Settings,
  Shield,
  ChevronLeft,
} from 'lucide-react'

import { cn } from '@utils/index'
import { useAuthStore, useUIStore } from '@store/index'

interface NavItem {
  to: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  roles?: string[]
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/geospatial', label: 'Geospatial', icon: MapIcon },
  { to: '/district', label: 'Districts', icon: Shield },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/explainability', label: 'Explainability', icon: Brain },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/admin/users', label: 'Users', icon: Users, roles: ['admin'] },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const { user } = useAuthStore()

  const filteredItems = NAV_ITEMS.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  )

  return (
    <aside
      className={cn(
        'relative flex flex-col border-r border-border bg-card transition-all duration-300',
        sidebarOpen ? 'w-64' : 'w-16'
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        {sidebarOpen ? (
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-blue-500 to-purple-600">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold">Prajna</h1>
              <p className="text-[10px] text-muted-foreground">Command Center</p>
            </div>
          </div>
        ) : (
          <div className="mx-auto flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-blue-500 to-purple-600">
            <Shield className="h-4 w-4 text-white" />
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className={cn(
            'rounded p-1 hover:bg-muted',
            !sidebarOpen && 'absolute -right-3 top-5 hidden border border-border bg-card'
          )}
        >
          <ChevronLeft
            className={cn('h-4 w-4 transition-transform', !sidebarOpen && 'rotate-180')}
          />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {filteredItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                  !sidebarOpen && 'justify-center px-2'
                )
              }
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      {sidebarOpen && (
        <div className="border-t border-border p-3 text-[10px] text-muted-foreground">
          <p>ET AI Hackathon 2026</p>
          <p className="mt-0.5">v1.0.0</p>
        </div>
      )}
    </aside>
  )
}

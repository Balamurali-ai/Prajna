/**
 * Admin Users Page — real backend wired
 */
import { useState } from 'react'
import { Shield, Trash2, Edit2, Check, X, Loader2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { Card, CardContent, CardHeader, Badge, Button, Input } from '@components/ui'
import { adminApi } from '@api/index'
import { formatDate, formatRelativeTime } from '@utils/index'
import type { User, UserRole } from '@/types'

const ROLES: UserRole[] = ['admin', 'officer', 'analyst']

const roleBadge: Record<UserRole, string> = {
  admin: 'bg-red-500/20 text-red-400 border-red-500/30',
  officer: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  analyst: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
}

export function AdminUsersPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [editId, setEditId] = useState<string | null>(null)
  const [editRole, setEditRole] = useState<UserRole>('analyst')

  const { data: users, isLoading } = useQuery<User[]>({
    queryKey: ['admin', 'users'],
    queryFn: () => adminApi.listUsers(),
    staleTime: 30_000,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: UserRole }) =>
      adminApi.updateUser(id, { role }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      setEditId(null)
      toast.success('User role updated')
    },
    onError: () => toast.error('Failed to update user'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteUser(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
      toast.success('User removed')
    },
    onError: () => toast.error('Failed to delete user'),
  })

  const filtered = users?.filter(
    (u) =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.full_name ?? '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">User Management</h1>
          <p className="text-sm text-muted-foreground">
            Manage platform users and roles
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1.5">
            <Shield className="h-3 w-3" />
            {users?.length ?? 0} users
          </Badge>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-3">
            <Input
              placeholder="Search by email or name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-sm"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-hidden rounded-b-lg">
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-muted/30">
                <tr>
                  {['User', 'Role', 'Status', 'Last Login', 'Joined', 'Actions'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i} className="border-b border-border/40">
                        {Array.from({ length: 6 }).map((_, j) => (
                          <td key={j} className="px-4 py-3">
                            <div className="h-4 w-full animate-pulse rounded bg-muted/40" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : (filtered ?? []).map((user) => (
                      <tr key={user.id} className="border-b border-border/40 transition-colors hover:bg-muted/20">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-xs font-bold text-white">
                              {(user.full_name ?? user.email)[0].toUpperCase()}
                            </div>
                            <div>
                              <p className="font-medium">{user.full_name ?? '—'}</p>
                              <p className="text-xs text-muted-foreground">{user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {editId === user.id ? (
                            <select
                              value={editRole}
                              onChange={(e) => setEditRole(e.target.value as UserRole)}
                              className="rounded border border-input bg-background px-2 py-1 text-xs"
                            >
                              {ROLES.map((r) => (
                                <option key={r} value={r}>{r}</option>
                              ))}
                            </select>
                          ) : (
                            <Badge className={roleBadge[user.role]}>
                              {user.role}
                            </Badge>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className="text-emerald-400">
                            active
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">
                          {user.last_login_at ? formatRelativeTime(user.last_login_at) : '—'}
                        </td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">
                          {formatDate(user.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            {editId === user.id ? (
                              <>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="h-7 w-7 text-emerald-400"
                                  disabled={updateMutation.isPending}
                                  onClick={() => updateMutation.mutate({ id: user.id, role: editRole })}
                                >
                                  {updateMutation.isPending ? (
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                  ) : (
                                    <Check className="h-3.5 w-3.5" />
                                  )}
                                </Button>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="h-7 w-7 text-muted-foreground"
                                  onClick={() => setEditId(null)}
                                >
                                  <X className="h-3.5 w-3.5" />
                                </Button>
                              </>
                            ) : (
                              <>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="h-7 w-7"
                                  onClick={() => { setEditId(user.id); setEditRole(user.role) }}
                                >
                                  <Edit2 className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="h-7 w-7 text-red-400 hover:text-red-300"
                                  disabled={deleteMutation.isPending}
                                  onClick={() => deleteMutation.mutate(user.id)}
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
            {!isLoading && (filtered ?? []).length === 0 && (
              <div className="py-12 text-center text-sm text-muted-foreground">
                No users found
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

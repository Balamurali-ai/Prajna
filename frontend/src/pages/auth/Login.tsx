/**
 * ====================================================
 * Login Page (Supabase Auth)
 * ====================================================
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Mail, Lock, Loader2, AlertCircle, UserRound } from 'lucide-react'

import { Button, Card, CardContent, Input } from '@components/ui'
import { getSupabase } from '@services/supabase'
import { useAuthStore } from '@store/index'
import { config } from '@config/index'

export function LoginPage() {
  const navigate = useNavigate()
  const setSession = useAuthStore((s) => s.setSession)
  const loginAsGuest = useAuthStore((s) => s.loginAsGuest)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Try Supabase Auth first
      try {
        const supabase = getSupabase()
        const { data, error: sbError } = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (sbError) throw sbError
        if (data.session) {
          const { authApi } = await import('@api/index')
          const user = await authApi.me(data.session.access_token)
          setSession(data.session.access_token, user, data.session.expires_in ?? 3600)
          navigate('/dashboard')
          return
        }
      } catch (sbErr) {
        console.warn('Supabase login failed, using backend:', sbErr)
      }

      // Backend login fallback
      const { authApi } = await import('@api/index')
      const result = await authApi.login(email, password)
      setSession(result.access_token, result.user, result.expires_in)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleGuestLogin = () => {
    loginAsGuest()
    navigate('/dashboard')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
            <Shield className="h-7 w-7 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold">Prajna</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Geospatial Pattern Intelligence — Command Center
          </p>
        </div>

        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <div className="flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="email"
                    required
                    placeholder="officer@prajna.gov"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </Button>
            </form>

            <div className="mt-3 flex items-center gap-3">
              <div className="h-px flex-1 bg-border" />
              <span className="text-xs text-muted-foreground">or</span>
              <div className="h-px flex-1 bg-border" />
            </div>

            <Button
              type="button"
              variant="outline"
              className="mt-3 w-full"
              onClick={handleGuestLogin}
            >
              <UserRound className="h-4 w-4" />
              Continue as Guest
            </Button>

            <p className="mt-4 text-center text-xs text-muted-foreground">
              Secured by Supabase Auth • Prajna
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

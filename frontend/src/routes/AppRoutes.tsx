/**
 * ====================================================
 * App Router
 * ====================================================
 */
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@components/layout'
import {
  AdminUsersPage,
  AnalyticsPage,
  DashboardPage,
  DistrictDetailsPage,
  DistrictListPage,
  ExplainabilityPage,
  GeospatialPage,
  LoginPage,
  NotFoundPage,
  ReportsPage,
  SettingsPage,
} from '@pages/index'
import { useAuthStore } from '@store/index'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuth = useAuthStore((s) => s.isAuthenticated)
  const isGuest = useAuthStore((s) => s.isGuest)
  const expiresAt = useAuthStore((s) => s.expiresAt)
  const logout = useAuthStore((s) => s.logout)

  // Only check token expiry for real (non-guest) sessions
  if (!isGuest && isAuth && expiresAt && Date.now() > expiresAt) {
    logout()
    return <Navigate to="/login" replace />
  }
  if (!isAuth) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const role = useAuthStore((s) => s.user?.role)
  if (role !== 'admin') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="geospatial" element={<GeospatialPage />} />
        <Route path="district" element={<DistrictListPage />} />
        <Route path="district/:name" element={<DistrictDetailsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="explainability" element={<ExplainabilityPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route
          path="admin/users"
          element={
            <AdminRoute>
              <AdminUsersPage />
            </AdminRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

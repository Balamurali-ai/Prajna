/**
 * ====================================================
 * App Component
 * ====================================================
 */
import { useEffect } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'sonner'

import { AppRoutes } from '@routes/index'
import { useAuthStore } from '@store/index'
import { config } from '@config/index'

// React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export default function App() {
  const fetchMe = useAuthStore((s) => s.fetchMe)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const token = useAuthStore((s) => s.token)

  // Verify session on app load
  useEffect(() => {
    if (isAuthenticated && token) {
      fetchMe()
    }
  }, [isAuthenticated, token, fetchMe])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
        <Toaster
          position="bottom-right"
          theme="dark"
          richColors
          closeButton
          duration={5000}
        />
      </BrowserRouter>
      {config.app.env === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  )
}

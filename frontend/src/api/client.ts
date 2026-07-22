/**
 * ====================================================
 * Axios HTTP Client
 * ====================================================
 */
import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from 'axios'

import { config } from '@config/index'

const client: AxiosInstance = axios.create({
  baseURL: config.api.baseUrl,
  timeout: config.api.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Read token from Zustand persisted store — single source of truth
function getToken(): string | null {
  try {
    const raw = localStorage.getItem('crime-intel-auth')
    if (!raw) return null
    return (JSON.parse(raw)?.state?.token as string) ?? null
  } catch {
    return null
  }
}

// ====================================================
// Request Interceptor — Attach Auth Token
// ====================================================
client.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ====================================================
// Response Interceptor — Handle Errors
// ====================================================
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const url = error.config?.url ?? ''
      // Don't wipe session for background session-check calls
      if (!url.includes('/auth/me')) {
        localStorage.removeItem('crime-intel-auth')
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default client

// ====================================================
// Helper Functions
// ====================================================
export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await client.get<T>(url, config)
  return response.data
}

export async function post<T, D = unknown>(
  url: string,
  data?: D,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await client.post<T>(url, data, config)
  return response.data
}

export async function patch<T, D = unknown>(
  url: string,
  data?: D,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await client.patch<T>(url, data, config)
  return response.data
}

export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await client.delete<T>(url, config)
  return response.data
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return (
      (error.response?.data as { error?: { message?: string } })?.error?.message ??
      error.message
    )
  }
  if (error instanceof Error) return error.message
  return 'An unknown error occurred'
}

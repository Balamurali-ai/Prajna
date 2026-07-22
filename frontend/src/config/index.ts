/**
 * ====================================================
 * Application Configuration
 * ====================================================
 * Reads from Vite env vars. All `VITE_*` vars are
 * exposed to the client at build time.
 * ====================================================
 */

const env = import.meta.env

const trimTrailingSlash = (value: string | undefined): string =>
  (value ?? '').replace(/\/+$/, '')

const apiBaseUrl = (() => {
  const baseUrl = trimTrailingSlash(env.VITE_API_BASE_URL)
  if (!baseUrl) return ''
  return baseUrl.endsWith('/api/v1') ? baseUrl : `${baseUrl}/api/v1`
})()

const wsBaseUrl = trimTrailingSlash(env.VITE_WS_BASE_URL)
  .replace(/^http:\/\//, 'ws://')
  .replace(/^https:\/\//, 'wss://')

export const config = {
  app: {
    name: env.VITE_APP_NAME ?? 'Prajna',
    version: env.VITE_APP_VERSION ?? '1.0.0',
    env: env.VITE_APP_ENV ?? 'development',
  },
  api: {
    baseUrl: apiBaseUrl,
    wsUrl: wsBaseUrl,
    timeout: 30_000,
  },
  supabase: {
    url: env.VITE_SUPABASE_URL ?? '',
    anonKey: env.VITE_SUPABASE_ANON_KEY ?? '',
  },
  map: {
    defaultCenter: (env.VITE_DEFAULT_MAP_CENTER ?? '20.5937,78.9629')
      .split(',')
      .map(Number) as [number, number],
    defaultZoom: Number(env.VITE_DEFAULT_MAP_ZOOM ?? 5),
  },
  features: {
    websockets: env.VITE_FEATURE_WEBSOCKETS === 'true',
    pdfExport: env.VITE_FEATURE_PDF_EXPORT === 'true',
    geojsonExport: env.VITE_FEATURE_GEOJSON_EXPORT === 'true',
  },
} as const

export type AppConfig = typeof config

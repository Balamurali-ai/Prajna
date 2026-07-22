/**
 * ====================================================
 * Application Configuration
 * ====================================================
 * Reads from Vite env vars. All `VITE_*` vars are
 * exposed to the client at build time.
 * ====================================================
 */

const env = import.meta.env

export const config = {
  app: {
    name: env.VITE_APP_NAME ?? 'Crime Intelligence Platform',
    version: env.VITE_APP_VERSION ?? '1.0.0',
    env: env.VITE_APP_ENV ?? 'development',
  },
  api: {
    baseUrl: env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
    wsUrl: env.VITE_WS_BASE_URL ?? 'ws://localhost:8000',
    timeout: 30_000,
  },
  supabase: {
    url: env.VITE_SUPABASE_URL ?? '',
    anonKey: env.VITE_SUPABASE_ANON_KEY ?? '',
  },
  mapbox: {
    token: env.VITE_MAPBOX_PUBLIC_TOKEN ?? '',
    style: env.VITE_MAPBOX_STYLE ?? 'dark-v11',
    defaultCenter: (env.VITE_DEFAULT_MAP_CENTER ?? '78.9629,20.5937')
      .split(',')
      .map(Number) as [number, number],
    defaultZoom: Number(env.VITE_DEFAULT_MAP_ZOOM ?? 4),
  },
  features: {
    websockets: env.VITE_FEATURE_WEBSOCKETS === 'true',
    pdfExport: env.VITE_FEATURE_PDF_EXPORT === 'true',
    geojsonExport: env.VITE_FEATURE_GEOJSON_EXPORT === 'true',
  },
} as const

export type AppConfig = typeof config

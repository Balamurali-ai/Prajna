/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_WS_BASE_URL: string
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  readonly VITE_MAPBOX_PUBLIC_TOKEN: string
  readonly VITE_MAPBOX_STYLE: string
  readonly VITE_DEFAULT_MAP_CENTER: string
  readonly VITE_DEFAULT_MAP_ZOOM: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_APP_ENV: string
  readonly VITE_FEATURE_WEBSOCKETS: string
  readonly VITE_FEATURE_PDF_EXPORT: string
  readonly VITE_FEATURE_GEOJSON_EXPORT: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

/**
 * ====================================================
 * Supabase Client
 * ====================================================
 */
import { createClient, type SupabaseClient } from '@supabase/supabase-js'

import { config } from '@config/index'

let _client: SupabaseClient | null = null

export function getSupabase(): SupabaseClient {
  if (!_client) {
    if (!config.supabase.url || !config.supabase.anonKey) {
      throw new Error(
        'Supabase configuration missing. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.'
      )
    }
    _client = createClient(config.supabase.url, config.supabase.anonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storage: localStorage,
      },
    })
  }
  return _client
}

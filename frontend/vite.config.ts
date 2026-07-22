// ====================================================
// Vite Configuration
// ====================================================
import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
  '@': path.resolve(__dirname, './src'),
  '@components': path.resolve(__dirname, './src/components'),
  '@pages': path.resolve(__dirname, './src/pages'),
  '@routes': path.resolve(__dirname, './src/routes'),
  '@hooks': path.resolve(__dirname, './src/hooks'),
  '@api': path.resolve(__dirname, './src/api'),
  '@store': path.resolve(__dirname, './src/store'),
  '@services': path.resolve(__dirname, './src/services'),
  '@types': path.resolve(__dirname, './src/types'),
  '@utils': path.resolve(__dirname, './src/utils'),
  '@config': path.resolve(__dirname, './src/config'),
},
  },
  server: {
    port: 5173,
    host: true,
    strictPort: false,
  },
  build: {
    target: 'es2022',
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          map: ['mapbox-gl', 'react-map-gl'],
          charts: ['recharts'],
          supabase: ['@supabase/supabase-js'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },
  preview: {
    port: 4173,
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In production (Render), VITE_API_URL env var points to the backend service.
// In development, proxy to local backend at port 8000.
const isDev = process.env.NODE_ENV !== 'production'

export default defineConfig({
  plugins: [react()],
  // Development proxy — only active with `npm run dev`
  server: isDev ? {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  } : {},
  build: {
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react':  ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts'],
          'vendor-icons':  ['lucide-react'],
          'vendor-utils':  ['axios', 'zustand', 'clsx', 'date-fns'],
        },
      },
    },
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { createTanStackStartPlugin } from '@tanstack/start-plugin'

export default defineConfig({
  plugins: [
    react(),
    createTanStackStartPlugin({
      router: {
        handler: './src/router.tsx',
      },
    }),
  ],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true,
        secure: false,
        ws: true,
      }
    }
  }
})

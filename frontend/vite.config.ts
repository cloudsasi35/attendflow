import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Browser telemetry: same-origin OTLP/HTTP requests forwarded to the collector.
      '/otel': {
        target: process.env.OTEL_PROXY_TARGET || 'http://otel-collector:4318',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/otel/, ''),
      },
    },
  },
})

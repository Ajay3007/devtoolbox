import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8080,
    proxy: {
      // Backend default is 5001 (see backend/app.py and start.sh). On macOS
      // port 5000 is taken by the AirPlay Receiver (Control Center), which
      // answers every request with 403 — so the project standardizes on 5001.
      // Override via VITE_PROXY_TARGET for a parallel/worktree instance.
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:5001',
        changeOrigin: true
      }
    }
  }
})

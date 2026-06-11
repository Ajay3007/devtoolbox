import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8080,
    proxy: {
      // Backend default is 5000 (see backend/app.py). The previous 5001 here
      // broke standalone `npm run dev`; start.ps1 sidesteps the proxy by
      // setting VITE_API_BASE_URL directly. Allow override via env for the
      // parallel/worktree instance.
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})

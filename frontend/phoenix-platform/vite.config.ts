import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import packageJson from './package.json'

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(packageJson.version),
  },
  plugins: [react()],
  server: {
    port: 5174,
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  preview: {
    port: 5174,
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})

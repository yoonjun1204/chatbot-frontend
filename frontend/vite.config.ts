import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Make the Docker container accessible from the outside
    host: true,
    port: 5173,
    // Optimization: for Windows file watching
    watch: {
      usePolling: true,
    },
  },
})

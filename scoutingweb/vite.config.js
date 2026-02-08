// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      onwarn(warning, warn) {
        // Ignore "use client" warnings
        if (warning.message.includes('use client') || 
            warning.message.includes('Module level directives')) {
          return
        }
        warn(warning)
      }
    },
    // Also set chunk size warning limit higher if needed
    chunkSizeWarningLimit: 1000
  },
  // Suppress esbuild warnings
  esbuild: {
    logOverride: { 
      'this-is-undefined-in-esm': 'silent' 
    }
  }
})
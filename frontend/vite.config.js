import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // --- Key configurations added or modified ---
  root: 'public',

  build: {
    outDir: '../dist',
    emptyOutDir: true, // Empty the output directory before each build to ensure it is up to date
  },

  // --- Other configurations remain unchanged ---
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000', 
        changeOrigin: true,
      },
    },
  },
});
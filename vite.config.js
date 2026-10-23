import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Relative asset paths work both on a custom domain and GitHub Pages project URLs.
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})

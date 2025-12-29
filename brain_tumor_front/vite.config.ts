import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve : {
    alias : {
      '@' : path.resolve(__dirname, 'src'), // @를 src 폴더로 mapping 해줌
    },
  },
  // vite.config.ts
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

})

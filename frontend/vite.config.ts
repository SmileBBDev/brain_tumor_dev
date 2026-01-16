import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// WSL에서 Windows 호스트에 접근하기 위한 설정
// Windows WSL 네트워크 어댑터 IP 사용 (ipconfig에서 vEthernet (WSL) 확인)
const WINDOWS_HOST = process.env.WINDOWS_HOST || '172.29.64.1'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://${WINDOWS_HOST}:8000`,
        changeOrigin: true,
      },
      '/ws': {
        target: `ws://${WINDOWS_HOST}:8000`,
        ws: true,
      },
    },
  },
})

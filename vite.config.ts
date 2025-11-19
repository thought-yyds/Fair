import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 所有以 /api 开头的请求，都会转发到 FastAPI 地址
      '/api': {
        target: 'http://localhost:8000', // FastAPI 后端的地址（默认端口8000）
        changeOrigin: true, // 允许跨域
        rewrite: (path) => path // 保持路径不变
      }
    }
  },
  resolve: {
    alias: {
      // 关键：@ 映射到 src 目录
      '@': path.resolve(__dirname, './src')
    }
  }
})

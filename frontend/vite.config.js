import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// 说明：通过 Vite 代理将前端的 '/api' 请求转发到后端，前端代码只用 '/api/...'
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const backend = env.VITE_BACKEND_URL || 'http://localhost:8000' // 默认后端地址，建议通过 .env.local 中的 VITE_BACKEND_URL 配置

  return {
    plugins: [vue()],
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: backend,
          changeOrigin: true,
          // 如果后端不需要重写路径，可以去掉 rewrite
          // rewrite: (path) => path
        }
      }
    }
  }
})

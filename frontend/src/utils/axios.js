import axios from 'axios'
import { useAuthStore } from '../stores/auth.js'

// 说明：
// - 开发环境建议配合 Vite 代理，前端统一使用 '/api' 前缀，不要写死完整后端地址。
// - 如果不使用 Vite 代理，或生产环境直连后端，请在 .env 中设置 VITE_API_BASE_URL 为完整后端地址，例如：
//   VITE_API_BASE_URL=http://localhost:8000/api
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api' // 默认使用相对路径配合 Vite 代理，生产环境需在 .env 中设置完整后端地址

const api = axios.create({
  baseURL: API_BASE,
  timeout: 600000,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore?.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    // 401 自动尝试刷新 token
    if (error.response?.status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true
      try {
        const authStore = useAuthStore()
        const refreshToken = authStore?.refreshToken
        if (!refreshToken) {
          authStore?.clearToken?.()
          // 注意：使用 window.location 会触发完整页面重载，清除所有应用状态
          window.location.href = '/'
          return Promise.reject(error)
        }
        // 刷新 token 接口（相对于 baseURL）
        const refreshResponse = await axios.post(
          `${API_BASE}/auth/refresh/`,
          { refresh: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        )
        const newAccess = refreshResponse.data.access
        authStore?.setToken?.(newAccess)
        originalRequest.headers.Authorization = `Bearer ${newAccess}`
        return api(originalRequest)
      } catch (refreshError) {
        const authStore = useAuthStore()
        authStore?.clearToken?.()
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  }
)

export default api
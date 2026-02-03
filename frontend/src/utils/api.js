import axios from 'axios'

// frontend/src/utils/api.js
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000', // 注意：不要写成 '/api'
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

// 可选：从 localStorage 获取 JWT 并在请求中自动添加
api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
  } catch (e) {
    // ignore
  }
  return config
}, (error) => Promise.reject(error))

// 可选：响应拦截器（简单统一错误处理）
api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    // 简单示例：若 401 则清理 token
    if (error.response && error.response.status === 401) {
      try { localStorage.removeItem('access_token') } catch (e) {}
    }
    return Promise.reject(error)
  }
)

// 辅助函数：设置/清除 token（前端登录后可调用）
export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('access_token', token)
  } else {
    localStorage.removeItem('access_token')
  }
}

export default api

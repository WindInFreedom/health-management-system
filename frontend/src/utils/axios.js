import axios from 'axios'
import { useAuthStore } from '../stores/auth.js'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
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
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const authStore = useAuthStore()
        const refreshToken = authStore.refreshToken
        if (!refreshToken) {
          authStore.clearToken()
          window.location.href = '/'
          return Promise.reject(error)
        }
        const refreshResponse = await axios.post(
          (import.meta.env.VITE_API_BASE || 'http://localhost:8000/api') + '/auth/refresh/',
          { refresh: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        )
        const newAccess = refreshResponse.data.access
        authStore.setToken(newAccess)
        originalRequest.headers.Authorization = `Bearer ${newAccess}`
        return api(originalRequest)
      } catch (refreshError) {
        const authStore = useAuthStore()
        authStore.clearToken()
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  }
)

export default api
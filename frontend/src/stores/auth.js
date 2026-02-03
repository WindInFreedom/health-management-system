import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({ 
    token: localStorage.getItem('token') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  actions: {
    setToken(token) {
      this.token = token
      if (token) localStorage.setItem('token', token)
      else localStorage.removeItem('token')
    },
    setRefreshToken(token) {
      this.refreshToken = token
      if (token) localStorage.setItem('refreshToken', token)
      else localStorage.removeItem('refreshToken')
    },
    setUser(user) {
      this.user = user
      if (user) localStorage.setItem('user', JSON.stringify(user))
      else localStorage.removeItem('user')
    },
    clearToken() {
      this.token = null
      this.refreshToken = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
    }
  }
})

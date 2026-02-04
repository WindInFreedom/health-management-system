<template>
  <div class="login-page">
    <main class="login-main">
      <div class="login-card">
        <!-- 标题放到卡片内 -->
        <div class="card-title">
          <h1>健康管理系统 - 登录</h1>
        </div>

        <label class="field-label">用户名</label>
        <input v-model="username" type="text" placeholder="请输入用户名" class="field-input" />

        <label class="field-label" style="margin-top:12px;">密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" class="field-input" />

        <div class="actions">
          <button class="btn-primary" @click="handleLogin" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </div>

        <div v-if="message" class="message">{{ message }}</div>

        <div class="foot" style="text-align:center; margin-top:12px;">
          <a href="#" @click.prevent="router.push('/register')">没有账号？去注册</a>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../utils/axios.js'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const message = ref('')

const handleLogin = async () => {
  loading.value = true
  message.value = ''
  try {
    // 说明：路径相对于 baseURL（默认为 /api 或 .env 中的 VITE_API_BASE_URL）
    const { data } = await api.post('/auth/login/', {
      username: username.value,
      password: password.value
    })

    if (!data?.access) {
      message.value = '登录返回缺少 access token'
      loading.value = false
      return
    }

    // 保存 token
    authStore.setToken(data.access)
    // 如后端返回 refresh token，也一并保存
    if (data.refresh && authStore.setRefreshToken) {
      authStore.setRefreshToken(data.refresh)
    }

    // 获取用户信息（若后端提供）
    try {
      const userRes = await api.get('/users/me/')
      authStore.setUser(userRes.data)
    } catch (e) {
      console.error('获取用户信息失败：', e)
    }

    message.value = '登录成功'
    setTimeout(() => router.push('/dashboard'), 600)
  } catch (error) {
    console.error(error)
    message.value = '登录失败：' + (error.response?.data?.detail || error.message || error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f6fbff 0%, #ffffff 100%);
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", "Microsoft YaHei", Arial;
  color: #2c3e50;
}

.login-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-card {
  width: 420px;
  background: #fff;
  border-radius: 10px;
  padding: 24px 28px;
  box-shadow: 0 6px 20px rgba(31, 110, 235, 0.08);
  box-sizing: border-box;
}

/* 标题在卡片顶部，与表单在同一框内 */
.card-title {
  text-align: center;
  margin-bottom: 14px;
}

.card-title h1 {
  margin: 0;
  font-size: 24px;
  color: #1f6feb;
  font-weight: 600;
}

.field-label {
  display: block;
  font-size: 15px;
  margin-bottom: 6px;
  color: #4b5563;
  font-weight: 500;
}

.field-input {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  border-radius: 8px;
  border: 1px solid #e6eef8;
  box-sizing: border-box;
  outline: none;
}

.field-input:focus {
  border-color: #7fb3ff;
  box-shadow: 0 0 0 4px rgba(127, 179, 255, 0.08);
}

.actions {
  margin-top: 18px;
  display: flex;
  justify-content: center;
}

.btn-primary {
  background: linear-gradient(90deg, #2f80ed, #1f6feb);
  color: white;
  padding: 12px 26px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  width: 100%;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message {
  margin-top: 12px;
  text-align: center;
  color: #e74c3c;
  font-size: 14px;
}

.foot a {
  color: #1f6feb;
  cursor: pointer;
  text-decoration: none;
}
</style>
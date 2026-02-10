<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="header-wrap">
          <div class="title-wrap">
            <h1 class="sys-title">健康管理系统 - 登录</h1>
            <p class="subtitle">欢迎使用智能健康管理平台</p>
          </div>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px" class="login-form">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" class="input-large" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" class="input-large" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" class="btn-large" style="width:100%;">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <!-- demo info removed to keep UI clean -->
      <div style="text-align:center; margin-top:8px;">
          <el-button type="text" @click="$router.push('/register')">没有账号？注册</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth.js'
import api from '../utils/axios.js'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const form = ref({
  username: '',
  password: ''
})
const rules = {
  username: [{required: true, message: '请输入用户名', trigger: 'blur'}],
  password: [{required: true, message: '请输入密码', trigger: 'blur'}]
}

const loading = ref(false)

const handleLogin = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const { data } = await api.post('/auth/login/', {
        username: form.value.username,
        password: form.value.password
      })

      if (!data?.access) {
        ElMessage.error('登录返回缺少 access token')
        loading.value = false
        return
      }

      authStore.setToken(data.access)
      if (data.refresh && authStore.setRefreshToken) {
        authStore.setRefreshToken(data.refresh)
      }

      // 获取用户信息（可选）
      try {
        const userRes = await api.get('/users/me/')
        authStore.setUser(userRes.data)
      } catch (e) {
        console.error('获取用户信息失败', e)
      }

      ElMessage.success('登录成功')
      setTimeout(() => router.push('/dashboard'), 600)
    } catch (error) {
      console.error(error)
      ElMessage.error('登录失败：' + (error.response?.data?.detail || error.message || error))
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  min-height: 100vh;
  background: linear-gradient(180deg, #f7fbff, #ffffff);
}

.login-card {
  width: 520px;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(31, 110, 235, 0.07);
}

.header-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.sys-title {
  margin: 0;
  font-size: 28px;
  color: #1f6feb;
  font-weight: 600;
}

.subtitle {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.login-form {
  padding: 8px 6px 22px 6px;
}

.input-large ::v-deep .el-input__inner {
  font-size: 16px;
  padding: 12px;
  border-radius: 8px;
}

.btn-large {
  font-size: 16px;
  padding: 12px 18px;
  border-radius: 8px;
}
</style>
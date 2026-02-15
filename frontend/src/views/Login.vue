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
  background: transparent;
  position: relative;
  overflow: hidden;
}



.login-card {
  width: 480px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  z-index: 1;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
}

.header-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px 0;
}

.sys-title {
  margin: 0;
  font-size: 28px;
  color: #ffffff;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.subtitle {
  margin: 12px 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.login-form {
  padding: 20px 30px 30px;
}

.input-large ::v-deep .el-input__inner {
  font-size: 16px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  transition: all 0.3s ease;
}

.input-large ::v-deep .el-input__inner::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.input-large ::v-deep .el-input__inner:focus {
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.15);
}

/* 链接颜色 */
.el-button--text {
  color: rgba(255, 255, 255, 0.8) !important;
}

.el-button--text:hover {
  color: #ffffff !important;
  text-decoration: underline;
}

.btn-large {
  font-size: 16px;
  padding: 14px 20px;
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-large:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 20px;
  }
  
  .login-card {
    width: 100%;
    max-width: 400px;
  }
  
  .login-form {
    padding: 20px 20px 30px;
  }
  
  .sys-title {
    font-size: 24px;
  }
  
  .subtitle {
    font-size: 14px;
  }
}
</style>
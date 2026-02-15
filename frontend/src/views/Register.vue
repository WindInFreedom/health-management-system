<template>
  <div class="register-page">
    <main class="register-main">
      <div class="register-card">
        <div class="card-title">
          <h1>注册新用户</h1>
          <p class="card-subtitle">创建您的健康管理账号，开始智能健康之旅</p>
        </div>

        <label class="field-label">用户名</label>
        <input v-model="form.username" type="text" placeholder="请输入用户名" class="field-input" />

        <label class="field-label">邮箱</label>
        <input v-model="form.email" type="email" placeholder="请输入邮箱" class="field-input" />

        <label class="field-label">密码</label>
        <input v-model="form.password" type="password" placeholder="请输入密码" class="field-input" />

        <label class="field-label">确认密码</label>
        <input v-model="form.password2" type="password" placeholder="请再次输入密码" class="field-input" />

        <div class="actions">
          <button class="btn-primary" @click="handleRegister" :disabled="submitting">
            {{ submitting ? '注册中...' : '注册' }}
          </button>
        </div>

        <div v-if="message" class="message">{{ message }}</div>

        <div class="foot">
          <a @click.prevent="goLogin" href="#">已有账号？去登录</a>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../utils/axios.js' // 如果项目使用 axios 实例
// 如果没有 axios util，请使用 fetch

const router = useRouter()
const submitting = ref(false)
const message = ref('')

const form = reactive({
  username: '',
  email: '',
  password: '',
  password2: ''
})

const handleRegister = async () => {
  message.value = ''
  if (!form.username || !form.email || !form.password || !form.password2) {
    message.value = '请填写所有必填项'
    return
  }
  if (form.password !== form.password2) {
    message.value = '两次输入的密码不一致'
    return
  }

  submitting.value = true
  try {
    // 使用项目已有的 axios 实例（若没有，可替换为 fetch）
    const res = await api.post('/auth/register/', {
      username: form.username,
      email: form.email,
      password: form.password,
      password2: form.password2
    })
    message.value = '注册成功，请使用新账号登录'
    setTimeout(() => router.push('/'), 900)
  } catch (err) {
    console.error('注册错误', err)
    // 尝试解析后端错误信息
    const errMsg = err?.response?.data || err?.message || '注册失败'
    if (typeof errMsg === 'string') message.value = errMsg
    else if (err?.response?.data) message.value = JSON.stringify(err.response.data)
    else message.value = '注册失败，请检查输入'
  } finally {
    submitting.value = false
  }
}

const goLogin = () => {
  router.push('/')
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  position: relative;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}



.register-main {
  position: relative;
  z-index: 1;
}

.register-card {
  width: 480px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.register-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
}

.card-title {
  text-align: center;
  margin-bottom: 30px;
}

.card-title h1 {
  margin: 0 0 10px 0;
  font-size: 28px;
  color: #ffffff;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.card-subtitle {
  margin: 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.field-label {
  font-size: 15px;
  margin-top: 20px;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  display: block;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.field-input {
  width: 100%;
  padding: 14px 16px;
  font-size: 16px;
  border-radius: 10px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.field-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.field-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.15);
}

.actions {
  margin-top: 30px;
}

.btn-primary {
  width: 100%;
  padding: 14px 20px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  color: #fff;
  border-radius: 10px;
  border: none;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.message {
  margin-top: 16px;
  color: #ff6b6b;
  text-align: center;
  font-size: 14px;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.foot {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
}

.foot a {
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  font-weight: 500;
  transition: color 0.3s ease;
  text-decoration: none;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.foot a:hover {
  color: #ffffff;
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .register-page {
    padding: 20px;
  }
  
  .register-card {
    width: 100%;
    max-width: 400px;
    padding: 20px;
  }
  
  .card-title h1 {
    font-size: 24px;
  }
  
  .field-input {
    padding: 12px 14px;
  }
  
  .btn-primary {
    padding: 12px 18px;
  }
}
</style>
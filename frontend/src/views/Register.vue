<template>
  <div class="register-page">
    <main class="register-main">
      <div class="register-card">
        <div class="card-title">
          <h1>注册新用户</h1>
        </div>

        <label class="field-label">用户名</label>
        <input v-model="form.username" type="text" placeholder="请输入用户名" class="field-input" />

        <label class="field-label" style="margin-top:12px;">邮箱</label>
        <input v-model="form.email" type="email" placeholder="请输入邮箱" class="field-input" />

        <label class="field-label" style="margin-top:12px;">密码</label>
        <input v-model="form.password" type="password" placeholder="请输入密码" class="field-input" />

        <label class="field-label" style="margin-top:12px;">确认密码</label>
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
/* 与登录页风格保持一致的简单样式 */
.register-page { min-height:100vh; display:flex; align-items:center; justify-content:center; background:linear-gradient(180deg,#f6fbff,#fff); font-family:...; }
.register-card { width:420px; background:#fff; border-radius:10px; padding:24px; box-shadow:0 6px 20px rgba(31,110,235,0.08); }
.card-title h1 { margin:0; font-size:22px; color:#1f6feb; text-align:center; }
.field-label { font-size:15px; margin-top:8px; color:#4b5563; }
.field-input { width:100%; padding:12px; font-size:15px; border-radius:8px; border:1px solid #e6eef8; }
.actions { margin-top:16px; }
.btn-primary { width:100%; padding:12px; background:linear-gradient(90deg,#2f80ed,#1f6feb); color:#fff; border-radius:8px; border:none; }
.message { margin-top:12px; color:#e74c3c; text-align:center; }
.foot { margin-top:10px; text-align:center; font-size:13px; }
.foot a { color:#1f6feb; cursor:pointer; }
</style>
<template>
  <div style="padding: 20px;">
    <h1>测试页面</h1>
    <p>Vue应用正在运行</p>
    <p>Token状态: {{ tokenStatus }}</p>
    <p>用户信息: {{ userInfo }}</p>
    <button @click="$router.push('/')" style="margin-right: 10px;">返回登录</button>
    <button @click="logout">退出登录</button>
    <div style="margin-top: 20px;">
      <button @click="testAPI" style="margin-right: 10px;">测试API</button>
      <button @click="$router.push('/measurements')">查看测量记录</button>
    </div>
    <div v-if="apiResult" style="margin-top: 20px; padding: 10px; background: #f5f5f5;">
      <h3>API测试结果:</h3>
      <pre>{{ apiResult }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth.js'
import api from '../../utils/axios.js'

const router = useRouter()
const authStore = useAuthStore()
const apiResult = ref('')

const tokenStatus = computed(() => authStore.token ? '已登录' : '未登录')
const userInfo = computed(() => {
  if (authStore.token) {
    try {
      const payload = JSON.parse(atob(authStore.token.split('.')[1]))
      return `用户ID: ${payload.user_id}`
    } catch (e) {
      return 'Token解析失败'
    }
  }
  return '未登录'
})

const logout = () => {
  authStore.clearToken()
  window.location.href = '/'
}

const testAPI = async () => {
  try {
    const { data } = await api.get('/measurements/')
    apiResult.value = `API调用成功!\n测量记录数量: ${Array.isArray(data) ? data.length : data.results?.length || 0}`
  } catch (error) {
    apiResult.value = `API调用错误: ${error.message}`
  }
}

onMounted(() => {
  console.log('TestDashboard mounted, token:', !!authStore.token)
})
</script>

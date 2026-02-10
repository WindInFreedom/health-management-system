<template>
  <div class="personal-center-container">
    <el-card class="main-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h2 class="page-title">个人中心</h2>
        </div>
      </template>

      <div class="profile-content">
        <!-- Avatar Section -->
        <div class="avatar-section">
          <el-upload
            class="avatar-uploader"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleAvatarSuccess"
            :on-error="handleAvatarError"
            :before-upload="beforeAvatarUpload"
            :disabled="loading"
            name="avatar"
          >
            <!-- ⭐ 修改：使用 avatarUrl 而不是 userInfo.avatar -->
            <img v-if="avatarUrl" :src="avatarUrl" class="avatar" alt="用户头像" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <p class="avatar-tip">点击上传头像（JPG/PNG/GIF/WebP，≤5MB）</p>
        </div>

        <!-- User Info Form -->
        <el-form
          ref="userFormRef"
          :model="userForm"
          :rules="userRules"
          label-width="100px"
          class="user-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="userForm.username" placeholder="请输入用户名" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="updateUserInfo" :loading="loading">
              更新信息
            </el-button>
          </el-form-item>
        </el-form>

        <!-- Change Password Form -->
        <el-divider />
        <h3 class="section-title">修改密码</h3>
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
          class="password-form"
        >
          <el-form-item label="旧密码" prop="old_password">
            <el-input
              v-model="passwordForm.old_password"
              type="password"
              placeholder="请输入旧密码"
              show-password
            />
          </el-form-item>

          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="passwordForm.confirm_password"
              type="password"
              placeholder="请再次输入新密码"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-button type="warning" @click="changePassword" :loading="loading">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'  // ⭐ 添加 computed
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../utils/axios.js'
import { useAuthStore } from '../stores/auth.js'

const authStore = useAuthStore()
const loading = ref(false)
const userFormRef = ref(null)
const passwordFormRef = ref(null)

const userInfo = reactive({
  avatar: '',
  username: ''
})

const userForm = reactive({
  username: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// ⭐ 新增：计算属性 - 处理头像 URL
const avatarUrl = computed(() => {
  if (!userInfo.avatar) return ''

  // 如果已经是完整 URL，直接返回
  if (userInfo.avatar.startsWith('http://') || userInfo.avatar.startsWith('https://')) {
    return userInfo.avatar
  }

  // 拼接后端 URL
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

  // 确保路径以 / 开头
  const path = userInfo.avatar.startsWith('/') ? userInfo.avatar : '/' + userInfo.avatar

  const fullUrl = `${backendUrl}${path}`

  console.log('头像 URL 处理:', {
    原始路径: userInfo.avatar,
    完整URL: fullUrl
  })

  return fullUrl
})

const uploadUrl = ref((import.meta.env.VITE_API_BASE_URL || '/api') + '/users/me/avatar/')
const uploadHeaders = ref({
  Authorization: `Bearer ${authStore.token}`
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'))
  } else if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 30, message: '用户名长度为 3-30 个字符', trigger: 'blur' }
  ]
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少为 8 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const fetchUserInfo = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/users/me/')

    console.log('获取到的用户信息:', data)  // ⭐ 调试日志

    userInfo.avatar = data.avatar
    userInfo.username = data.username
    userForm.username = data.username
  } catch (error) {
    ElMessage.error('获取用户信息失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const updateUserInfo = async () => {
  try {
    await userFormRef.value.validate()
    loading.value = true
    await api.patch('/users/me/', {
      username: userForm.username
    })
    userInfo.username = userForm.username
    ElMessage.success('用户信息更新成功')
  } catch (error) {
    if (error.response) {
      ElMessage.error('更新失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    loading.value = false
  }
}

const changePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    loading.value = true
    await api.post('/auth/change-password/', {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordFormRef.value.resetFields()

    setTimeout(() => {
      authStore.clearToken()
      window.location.href = '/'
    }, 1500)
  } catch (error) {
    ElMessage.error('修改密码失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const handleAvatarSuccess = (response, file) => {
  console.log('上传成功响应:', response)
  if (response.avatar_url) {
    userInfo.avatar = response.avatar_url
    ElMessage.success('头像上传成功')
  } else if (response.message) {
    ElMessage.success(response.message)
    fetchUserInfo()  // 重新获取用户信息
  }
}

const handleAvatarError = (error, file) => {
  console.error('上传失败:', error)
  let errorMessage = '头像上传失败'

  try {
    const response = JSON.parse(error.message)
    errorMessage = response.error || response.detail || errorMessage
  } catch (e) {
    // 解析失败，使用默认错误消息
  }

  ElMessage.error(errorMessage)
}

const beforeAvatarUpload = (file) => {
  console.log('准备上传文件:', {
    name: file.name,
    type: file.type,
    size: (file.size / 1024 / 1024).toFixed(2) + 'MB'
  })

  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
    return false
  }
  return true
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
/* 样式代码保持不变 */
.personal-center-container {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.main-card {
  max-width: 800px;
  margin: 0 auto;
  border-radius: 15px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.profile-content {
  padding: 20px 0;
}

.avatar-section {
  text-align: center;
  margin-bottom: 30px;
}

.avatar-uploader {
  display: inline-block;
}

.avatar-uploader :deep(.el-upload) {
  border: 2px dashed #d9d9d9;
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-uploader :deep(.el-upload:hover) {
  border-color: #667eea;
}

.avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-uploader-icon {
  font-size: 40px;
  color: #8c939d;
}

.avatar-tip {
  margin-top: 10px;
  color: #999;
  font-size: 14px;
}

.user-form,
.password-form {
  max-width: 500px;
  margin: 0 auto;
}

.section-title {
  font-size: 18px;
  margin: 20px 0;
  color: #333;
}

:deep(.el-divider) {
  margin: 30px 0;
}

@media (max-width: 768px) {
  .personal-center-container {
    padding: 10px;
  }

  .main-card {
    margin: 10px;
  }

  .user-form,
  .password-form {
    max-width: 100%;
  }

  :deep(.el-form-item__label) {
    width: 80px !important;
  }
}
</style>
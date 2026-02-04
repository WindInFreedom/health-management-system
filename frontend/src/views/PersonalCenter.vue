<!-- 替换本地内容：个人中心页面 - 用户信息编辑和密码修改 -->
<template>
  <div class="personal-center">
    <el-card class="center-card">
      <template #header>
        <h2>个人中心</h2>
      </template>

      <el-tabs v-model="activeTab" class="center-tabs">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="info">
          <el-form
            ref="infoFormRef"
            :model="userForm"
            :rules="infoRules"
            label-width="120px"
            class="info-form"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userForm.username" placeholder="请输入用户名" />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userForm.email" placeholder="请输入邮箱" />
            </el-form-item>

            <el-form-item label="姓名">
              <el-input v-model="userForm.first_name" placeholder="名" style="width: 48%" />
              <el-input
                v-model="userForm.last_name"
                placeholder="姓"
                style="width: 48%; margin-left: 4%"
              />
            </el-form-item>

            <el-form-item label="手机号">
              <el-input v-model="userForm.phone" placeholder="请输入手机号" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleUpdateInfo" :loading="updating">
                保存信息
              </el-button>
              <el-button @click="loadUserInfo">取消</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 头像设置 -->
        <el-tab-pane label="头像设置" name="avatar">
          <div class="avatar-section">
            <div class="current-avatar">
              <h3>当前头像</h3>
              <el-avatar :src="userForm.avatar_url" :size="120">
                <el-icon><User /></el-icon>
              </el-avatar>
            </div>

            <el-upload
              class="avatar-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :on-success="handleAvatarSuccess"
              :on-error="handleAvatarError"
            >
              <el-button type="primary" :icon="Upload">上传新头像</el-button>
              <template #tip>
                <div class="upload-tip">
                  只能上传 jpg/png/gif 文件，且不超过 5MB
                </div>
              </template>
            </el-upload>
          </div>
        </el-tab-pane>

        <!-- 密码修改 -->
        <el-tab-pane label="修改密码" name="password">
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="120px"
            class="password-form"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入原密码"
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

            <el-form-item label="确认新密码" prop="new_password2">
              <el-input
                v-model="passwordForm.new_password2"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">
                修改密码
              </el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Upload } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import api from '../utils/axios'

const authStore = useAuthStore()
const activeTab = ref('info')

// 表单refs
const infoFormRef = ref(null)
const passwordFormRef = ref(null)

// 用户信息表单
const userForm = reactive({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  avatar_url: ''
})

// 密码修改表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  new_password2: ''
})

// 状态
const updating = ref(false)
const changingPassword = ref(false)

// 上传配置
const uploadUrl = computed(() => `${api.defaults.baseURL}/auth/upload-avatar/`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${authStore.token}`
}))

// 表单验证规则
const infoRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于 8 个字符', trigger: 'blur' }
  ],
  new_password2: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const response = await api.get('/auth/user-profile/me/')
    Object.assign(userForm, response.data)
  } catch (error) {
    ElMessage.error('加载用户信息失败')
    console.error('Load user info error:', error)
  }
}

// 更新用户信息
const handleUpdateInfo = async () => {
  if (!infoFormRef.value) return

  await infoFormRef.value.validate(async (valid) => {
    if (valid) {
      updating.value = true
      try {
        const response = await api.put('/auth/user-profile/me/', userForm)
        Object.assign(userForm, response.data)
        authStore.user = response.data
        ElMessage.success('信息更新成功')
      } catch (error) {
        ElMessage.error(error.response?.data?.error || '更新失败')
      } finally {
        updating.value = false
      }
    }
  })
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changingPassword.value = true
      try {
        await api.post('/auth/change-password/', passwordForm)
        ElMessage.success('密码修改成功，请重新登录')
        resetPasswordForm()
        // 可以选择自动登出
        setTimeout(() => {
          authStore.logout()
          window.location.href = '/'
        }, 2000)
      } catch (error) {
        ElMessage.error(error.response?.data?.error || '修改失败')
      } finally {
        changingPassword.value = false
      }
    }
  })
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.new_password2 = ''
  if (passwordFormRef.value) {
    passwordFormRef.value.clearValidate()
  }
}

// 头像上传前验证
const beforeAvatarUpload = (file) => {
  const isImage = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB！')
    return false
  }
  return true
}

// 头像上传成功
const handleAvatarSuccess = (response) => {
  userForm.avatar_url = response.avatar_url
  authStore.user.avatar_url = response.avatar_url
  ElMessage.success('头像上传成功')
}

// 头像上传失败
const handleAvatarError = (error) => {
  ElMessage.error('头像上传失败')
  console.error('Upload error:', error)
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.personal-center {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.center-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.center-card :deep(.el-card__header) h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.center-tabs {
  margin-top: 20px;
}

.info-form,
.password-form {
  max-width: 500px;
  margin-top: 20px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 20px;
}

.current-avatar {
  text-align: center;
}

.current-avatar h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #606266;
}

.avatar-uploader {
  text-align: center;
}

.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .personal-center {
    padding: 16px;
  }

  .info-form,
  .password-form {
    max-width: 100%;
  }
}
</style>

<!-- 替换本地内容：顶部标题栏和用户菜单 -->
<template>
  <div class="header-bar">
    <div class="header-left">
      <h1 class="header-title">个人健康管理系统-用户</h1>
    </div>

    <div class="header-right">
      <!-- 通知图标 -->
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
        <el-button :icon="Bell" circle @click="showNotifications" />
      </el-badge>

      <!-- 用户头像和下拉菜单 -->
      <el-dropdown @command="handleCommand" trigger="click">
        <div class="user-avatar-wrapper">
          <el-avatar :src="userAvatar" :size="40">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="username">{{ username }}</span>
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="personal-center">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="profile">
              <el-icon><Edit /></el-icon>
              个人档案
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 通知抽屉 -->
    <el-drawer
      v-model="notificationDrawer"
      title="通知中心"
      direction="rtl"
      size="400px"
    >
      <div class="notifications-list">
        <el-empty v-if="notifications.length === 0" description="暂无通知" />
        <div
          v-for="notif in notifications"
          :key="notif.id"
          class="notification-item"
          :class="{ unread: !notif.read }"
        >
          <div class="notification-header">
            <span class="notification-title">{{ notif.title }}</span>
            <el-tag :type="getNotificationType(notif.type)" size="small">
              {{ notif.type }}
            </el-tag>
          </div>
          <p class="notification-content">{{ notif.content }}</p>
          <span class="notification-time">{{ formatTime(notif.time) }}</span>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Bell,
  ArrowDown,
  Edit,
  Setting,
  SwitchButton
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import api from '../utils/axios'

const router = useRouter()
const authStore = useAuthStore()

// 用户信息
const username = computed(() => authStore.user?.username || '用户')
const userAvatar = computed(() => authStore.user?.avatar_url || '')

// 通知相关
const notificationDrawer = ref(false)
const notifications = ref([
  // 示例通知数据
])
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

// 处理下拉菜单命令
const handleCommand = (command) => {
  switch (command) {
    case 'personal-center':
      router.push('/personal-center')
      break
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  } catch (error) {
    // 用户取消
  }
}

// 显示通知
const showNotifications = () => {
  notificationDrawer.value = true
}

// 获取通知类型标签样式
const getNotificationType = (type) => {
  const typeMap = {
    'warning': 'warning',
    'info': 'info',
    'success': 'success',
    'error': 'danger'
  }
  return typeMap[type] || 'info'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN')
}

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const response = await api.get('/auth/users/me/')
    if (response.data) {
      authStore.user = response.data
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: sticky;
  top: 0;
  z-index: 999;
}

.header-left {
  flex: 1;
}

.header-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.notification-badge {
  margin-right: 8px;
}

.user-avatar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-avatar-wrapper:hover {
  background-color: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.dropdown-icon {
  color: #909399;
  font-size: 12px;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  transition: all 0.3s;
  cursor: pointer;
}

.notification-item:hover {
  background-color: #f5f7fa;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.notification-item.unread {
  border-left: 3px solid #409eff;
  background-color: #ecf5ff;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.notification-content {
  margin: 8px 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-title {
    font-size: 16px;
  }
  
  .username {
    display: none;
  }
  
  .user-avatar-wrapper {
    padding: 4px;
  }
}
</style>

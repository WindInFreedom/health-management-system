<template>
  <div class="header-bar">
    <div class="header-title">
      <h1>个人健康管理系统-用户</h1>
    </div>
    
    <div class="header-actions">
      <div class="user-menu" @click="toggleDropdown" v-click-outside="closeDropdown">
        <el-avatar 
          :size="40" 
          :src="avatarUrl"
          class="user-avatar"
        >
          {{ username.charAt(0).toUpperCase() }}
        </el-avatar>
        <span class="username">{{ username }}</span>
        <span class="dropdown-icon">▼</span>
        
        <div v-if="showDropdown" class="dropdown-menu">
          <router-link to="/personal-center" class="dropdown-item">
            <span class="item-icon">👤</span>
            个人中心
          </router-link>
          <div class="dropdown-item" @click="handleLogout">
            <span class="item-icon">🚪</span>
            退出登录
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { ElAvatar } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const showDropdown = ref(false)

const username = computed(() => authStore.user?.username || '用户')

// ⭐ 修复：正确处理头像 URL
const avatarUrl = computed(() => {
  const avatar = authStore.user?.avatar
  if (!avatar) return null

  // 如果已经是完整 URL，直接返回
  if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
    return avatar
  }

  // 拼接后端 URL
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
  const path = avatar.startsWith('/') ? avatar : '/' + avatar

  return `${backendUrl}${path}`
})

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function closeDropdown() {
  showDropdown.value = false
}

function handleLogout() {
  authStore.clearToken()
  router.push('/')
}

// Click outside directive
const vClickOutside = {
  mounted(el, binding) {
    el.clickOutsideEvent = function(event) {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value()
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}
</script>

<style scoped>
.header-bar {
  height: 60px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 99;
}

.header-title h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 15px;
  border-radius: 8px;
  transition: background 0.2s;
  position: relative;
}

.user-menu:hover {
  background: #f5f5f5;
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.dropdown-icon {
  font-size: 10px;
  color: #666;
  transition: transform 0.2s;
}

.user-menu:hover .dropdown-icon {
  transform: translateY(2px);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 5px);
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 160px;
  overflow: hidden;
  z-index: 1000;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  color: #333;
  text-decoration: none;
  transition: background 0.2s;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background: #f5f5f5;
}

.item-icon {
  font-size: 16px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .header-title h1 {
    font-size: 16px;
  }

  .username {
    display: none;
  }

  .header-bar {
    padding: 0 15px;
  }
}
</style>
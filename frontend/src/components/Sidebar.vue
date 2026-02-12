<template>
  <div class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <h3 v-if="!isCollapsed">健康管理</h3>
      <button class="toggle-btn" @click="toggleCollapse">
        <span v-if="isCollapsed">☰</span>
        <span v-else>‹</span>
      </button>
    </div>
    
    <nav class="sidebar-nav">
      <router-link 
        v-for="item in menuItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-if="!isCollapsed" class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapsed = ref(false)

const menuItems = [
  { path: '/dashboard-user', icon: '🏠', label: '首页' },
  { path: '/personal-center', icon: '👤', label: '个人中心' },
  { path: '/profile', icon: '📋', label: '基本档案' },
  { path: '/measurements', icon: '📊', label: '基本指标' },
  { path: '/health-report', icon: '📈', label: '健康报告' },
  { path: '/medications', icon: '💊', label: '用药记录' },
  { path: '/sleep-logs', icon: '😴', label: '睡眠记录' },
  { path: '/mood-logs', icon: '😊', label: '心情记录' },
]

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.toggle-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: background 0.2s;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.sidebar-nav {
  flex: 1;
  padding: 10px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border-left-color: white;
  font-weight: 600;
}

.nav-icon {
  font-size: 20px;
  min-width: 30px;
  display: inline-block;
}

.nav-label {
  margin-left: 10px;
  white-space: nowrap;
}

.sidebar.collapsed .nav-label {
  display: none;
}

.sidebar.collapsed .sidebar-header h3 {
  display: none;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 15px 10px;
}

/* Scrollbar styling */
.sidebar-nav::-webkit-scrollbar {
  width: 5px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 5px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>

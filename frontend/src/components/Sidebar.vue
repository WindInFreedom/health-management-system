<!-- 替换本地内容：左侧侧边栏导航重构 -->
<template>
  <div class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <h3 v-if="!isCollapsed">健康管理系统</h3>
      <el-button
        :icon="isCollapsed ? 'expand' : 'fold'"
        circle
        @click="toggleCollapse"
        class="collapse-btn"
      />
    </div>

    <el-menu
      :default-active="activeMenu"
      class="sidebar-menu"
      :collapse="isCollapsed"
      router
    >
      <!-- 个人账户信息 -->
      <el-menu-item index="/dashboard-user">
        <el-icon><Home /></el-icon>
        <template #title>仪表板</template>
      </el-menu-item>

      <!-- 个人基本档案 -->
      <el-menu-item index="/profile">
        <el-icon><User /></el-icon>
        <template #title>个人基本档案</template>
      </el-menu-item>

      <!-- 个人健康记录（增删改查） -->
      <el-sub-menu index="records">
        <template #title>
          <el-icon><Document /></el-icon>
          <span>健康记录管理</span>
        </template>
        <el-menu-item index="/measurements">测量记录</el-menu-item>
        <el-menu-item index="/medications">药物记录</el-menu-item>
        <el-menu-item index="/sleep-logs">睡眠记录</el-menu-item>
        <el-menu-item index="/mood-logs">情绪记录</el-menu-item>
      </el-sub-menu>

      <!-- 健康记录可视化 -->
      <el-menu-item index="/visualizations">
        <el-icon><TrendCharts /></el-icon>
        <template #title>健康数据可视化</template>
      </el-menu-item>

      <!-- 个人健康报告 -->
      <el-menu-item index="/health-report">
        <el-icon><Document /></el-icon>
        <template #title>个人健康报告</template>
      </el-menu-item>

      <!-- 个人中心 -->
      <el-menu-item index="/personal-center">
        <el-icon><Setting /></el-icon>
        <template #title>个人中心</template>
      </el-menu-item>
    </el-menu>

    <div class="sidebar-footer" v-if="!isCollapsed">
      <p class="version-text">版本 1.0.0</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Home,
  User,
  Document,
  TrendCharts,
  Setting
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapsed = ref(false)

// 根据当前路由计算活动菜单项
const activeMenu = computed(() => route.path)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 监听路由变化，自动激活对应菜单
watch(
  () => route.path,
  (newPath) => {
    console.log('当前路由:', newPath)
  }
)
</script>

<style scoped>
.sidebar {
  height: 100vh;
  background-color: #304156;
  transition: width 0.3s;
  width: 250px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background-color: #263445;
  color: #fff;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}

.collapse-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background-color: #304156;
}

.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  color: #bfcbd9;
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background-color: #263445;
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #409eff;
  color: #fff;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  background-color: #1f2d3d;
  min-width: 0;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item:hover) {
  background-color: #001528;
}

.sidebar-footer {
  padding: 20px;
  text-align: center;
  background-color: #263445;
  color: #bfcbd9;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.version-text {
  margin: 0;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1000;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  }
}
</style>

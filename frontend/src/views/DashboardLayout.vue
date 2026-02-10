<template>
  <div class="dashboard-layout">
    <Sidebar />
    <div class="main-content" :class="{ 'with-sidebar': true }">
      <HeaderBar />
      <div class="content-area">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import Sidebar from '../components/Sidebar.vue'
import HeaderBar from '../components/HeaderBar.vue'
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 240px; /* Width of sidebar */
  transition: margin-left 0.3s ease;
}

.content-area {
  flex: 1;
  overflow-y: auto;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }
}
</style>

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
  background: transparent;
  position: relative;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 240px; /* Width of sidebar */
  transition: margin-left 0.3s ease;
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  margin: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.content-area {
  flex: 1;
  overflow-y: auto;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
    margin: 10px;
  }
}
</style>

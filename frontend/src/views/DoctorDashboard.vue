<template>
  <div class="doctor-dashboard">
    <!-- Header -->
    <el-card class="header-card">
      <div class="header-content">
        <div class="user-info">
          <el-avatar :size="50" />
          <div class="user-details">
            <h3>医生工作台</h3>
            <p>{{ userInfo.department }} - {{ userInfo.username }}</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button @click="$router.push('/patients')">
            患者管理
          </el-button>
          <el-button @click="$router.push('/health-alerts')">
            健康预警
          </el-button>
          <el-button @click="$router.push('/user-management')">
            用户管理
          </el-button>
          <el-button type="danger" @click="handleLogout">
            退出登录
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Statistics Cards -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon patients">👥</div>
          <div class="stat-info">
            <h4>总患者数</h4>
            <p class="stat-value">{{ stats.total_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon active">📊</div>
          <div class="stat-info">
            <h4>活跃患者</h4>
            <p class="stat-value">{{ stats.active_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon alerts">⚠️</div>
          <div class="stat-info">
            <h4>健康预警</h4>
            <p class="stat-value">{{ healthAlerts.length }}</p>
            <span class="stat-label">条</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon regular">📈</div>
          <div class="stat-info">
            <h4>普通用户</h4>
            <p class="stat-value">{{ stats.regular_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Health Alerts -->
    <el-card class="alerts-card">
      <template #header>
        <div class="card-header">
          <h3>健康预警</h3>
          <el-button @click="refreshAlerts" size="small">刷新</el-button>
        </div>
      </template>
      <div class="alerts-content">
        <div v-if="healthAlerts.length === 0" class="no-alerts">
          <p>暂无健康预警</p>
        </div>
        <div v-else>
          <div v-for="alert in healthAlerts.slice(0, 10)" :key="alert.user.id" class="alert-item">
            <el-card class="alert-card">
              <div class="alert-header">
                <div class="patient-info">
                  <el-tag type="primary">{{ alert.user.username }}</el-tag>
                  <el-tag type="info">{{ alert.user.role }}</el-tag>
                  <span class="alert-time">{{ formatDate(alert.measurement_date) }}</span>
                </div>
                <el-tag :type="getSeverityType(alert.alerts[0].severity)">
                  {{ getSeverityText(alert.alerts[0].severity) }}
                </el-tag>
              </div>
              <div class="alert-content">
                <div v-for="(alert_detail, index) in alert.alerts" :key="index" class="alert-detail">
                  <el-alert
                    :title="alert_detail.message"
                    :type="getSeverityType(alert_detail.severity)"
                    :closable="false"
                    show-icon
                  />
                </div>
              </div>
              <div class="alert-actions">
                <el-button size="small" @click="viewPatientDetails(alert.user.id)">
                  查看详情
                </el-button>
                <el-button size="small" type="primary" @click="sendRecommendation(alert.user.id)">
                  发送建议
                </el-button>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Recent Patients -->
    <el-card class="recent-patients-card">
      <template #header>
        <h3>最近注册患者</h3>
      </template>
      <el-table :data="recentPatients" stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.date_joined) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewPatientDetails(row.id)">
              查看详情
            </el-button>
            <el-button size="small" type="primary" @click="viewHealthSummary(row.id)">
              健康摘要
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../utils/axios.js'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const userInfo = ref({})
const stats = ref({})
const healthAlerts = ref([])
const recentPatients = ref([])

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const handleLogout = () => {
  authStore.clearToken()
  ElMessage.success('已退出登录')
  router.push('/')
}

const getSeverityType = (severity) => {
  const types = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return types[severity] || 'info'
}

const getSeverityText = (severity) => {
  const texts = {
    'high': '高风险',
    'medium': '中风险',
    'low': '低风险'
  }
  return texts[severity] || '未知'
}

const getRoleType = (role) => {
  const types = {
    'admin': 'danger',
    'doctor': 'warning',
    'user': 'success'
  }
  return types[role] || 'info'
}

const getRoleText = (role) => {
  const texts = {
    'admin': '管理员',
    'doctor': '医生',
    'user': '普通用户'
  }
  return texts[role] || '未知'
}

const fetchUserInfo = async () => {
  try {
    const response = await api.get('/users/me/')
    userInfo.value = response.data
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const fetchStats = async () => {
  try {
    const response = await api.get('/users/management/statistics/')
    stats.value = response.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchHealthAlerts = async () => {
  try {
    const response = await api.get('/users/management/alerts/')
    healthAlerts.value = response.data.alerts || []
  } catch (error) {
    console.error('获取健康预警失败:', error)
  }
}

const refreshAlerts = () => {
  fetchHealthAlerts()
  ElMessage.success('预警数据已刷新')
}

const viewPatientDetails = (userId) => {
  router.push(`/patient-details/${userId}`)
}

const viewHealthSummary = (userId) => {
  router.push(`/patient-health-summary/${userId}`)
}

const sendRecommendation = (userId) => {
  ElMessage.info('发送建议功能开发中...')
}

onMounted(async () => {
  await fetchUserInfo()
  await fetchStats()
  await fetchHealthAlerts()
  
  // 获取最近注册患者
  try {
    const response = await api.get('/users/management/users/', {
      params: { ordering: '-date_joined', page_size: 5 }
    })
    recentPatients.value = response.data.results || []
  } catch (error) {
    console.error('获取最近患者失败:', error)
  }
})
</script>

<style scoped>
.doctor-dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-details h3 {
  margin: 0;
  color: #303133;
}

.user-details p {
  margin: 5px 0 0 0;
  color: #909399;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.patients { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-icon.active { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-icon.alerts { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.stat-icon.regular { background: linear-gradient(135deg, #43e97b, #38f9d7); }

.stat-info h4 {
  margin: 0 0 5px 0;
  color: #909399;
  font-size: 14px;
}

.stat-value {
  margin: 0 0 5px 0;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #C0C4CC;
}

.alerts-card,
.recent-patients-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.no-alerts {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.alert-item {
  margin-bottom: 15px;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.patient-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}

.alert-content {
  margin-bottom: 10px;
}

.alert-detail {
  margin-bottom: 5px;
}

.alert-actions {
  display: flex;
  gap: 10px;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .alert-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
}
</style>

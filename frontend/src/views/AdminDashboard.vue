<template>
  <div class="admin-dashboard">
    <!-- Header -->
    <el-card class="header-card">
      <div class="header-content">
        <div class="user-info">
          <el-avatar :size="50" />
          <div class="user-details">
            <h3>系统管理</h3>
            <p>管理员 - {{ userInfo.username }}</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button @click="$router.push('/user-management')">
            用户管理
          </el-button>
          <el-button @click="$router.push('/system-stats')">
            系统统计
          </el-button>
          <el-button @click="$router.push('/health-alerts')">
            健康预警
          </el-button>
          <el-button type="danger" @click="handleLogout">
            退出登录
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- System Statistics -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon total">👥</div>
          <div class="stat-info">
            <h4>总用户数</h4>
            <p class="stat-value">{{ stats.total_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon admin">👨‍⚕️</div>
          <div class="stat-info">
            <h4>管理员</h4>
            <p class="stat-value">{{ stats.admin_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon doctor">👩‍⚕️</div>
          <div class="stat-info">
            <h4>医生</h4>
            <p class="stat-value">{{ stats.doctor_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon regular">👤</div>
          <div class="stat-info">
            <h4>普通用户</h4>
            <p class="stat-value">{{ stats.regular_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon active">📊</div>
          <div class="stat-info">
            <h4>活跃用户</h4>
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
    </div>

    <!-- Quick Actions -->
    <el-card class="actions-card">
      <template #header>
        <h3>快速操作</h3>
      </template>
      <div class="actions-grid">
        <el-button type="primary" @click="showCreateDoctorDialog = true">
          <el-icon><Plus /></el-icon>
          创建医生账号
        </el-button>
        <el-button type="success" @click="$router.push('/user-management')">
          <el-icon><User /></el-icon>
          用户管理
        </el-button>
        <el-button type="warning" @click="$router.push('/health-alerts')">
          <el-icon><Bell /></el-icon>
          健康预警
        </el-button>
        <el-button type="info" @click="$router.push('/system-stats')">
          <el-icon><DataAnalysis /></el-icon>
          系统统计
        </el-button>
      </div>
    </el-card>

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
                  <el-tag :type="getRoleType(alert.user.role)">{{ getRoleText(alert.user.role) }}</el-tag>
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
                <el-button size="small" @click="viewUserDetails(alert.user.id)">
                  查看详情
                </el-button>
                <el-button size="small" type="primary" @click="viewUserHealthSummary(alert.user.id)">
                  健康摘要
                </el-button>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Recent Users -->
    <el-card class="recent-users-card">
      <template #header>
        <h3>最近注册用户</h3>
      </template>
      <el-table :data="recentUsers" stripe>
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
            <el-button size="small" @click="viewUserDetails(row.id)">
              查看详情
            </el-button>
            <el-button size="small" type="primary" @click="editUser(row.id)">
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create Doctor Dialog -->
    <el-dialog v-model="showCreateDoctorDialog" title="创建医生账号" width="500px">
      <el-form :model="doctorForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="doctorForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="doctorForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="doctorForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="doctorForm.first_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="科室">
          <el-input v-model="doctorForm.department" placeholder="请输入科室" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDoctorDialog = false">取消</el-button>
        <el-button type="primary" @click="createDoctor" :loading="creatingDoctor">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, User, Bell, DataAnalysis } from '@element-plus/icons-vue'
import api from '../utils/axios.js'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const userInfo = ref({})
const stats = ref({})
const healthAlerts = ref([])
const recentUsers = ref([])
const showCreateDoctorDialog = ref(false)
const creatingDoctor = ref(false)

const doctorForm = reactive({
  username: '',
  email: '',
  password: '',
  first_name: '',
  department: ''
})

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

const viewUserDetails = (userId) => {
  router.push(`/user-details/${userId}`)
}

const viewUserHealthSummary = (userId) => {
  router.push(`/user-health-summary/${userId}`)
}

const editUser = (userId) => {
  router.push(`/edit-user/${userId}`)
}

const createDoctor = async () => {
  creatingDoctor.value = true
  try {
    const response = await api.post('/users/management/create-doctor/', doctorForm)
    ElMessage.success('医生账号创建成功')
    showCreateDoctorDialog.value = false
    
    // 重置表单
    Object.assign(doctorForm, {
      username: '',
      email: '',
      password: '',
      first_name: '',
      department: ''
    })
    
    // 刷新用户列表
    fetchRecentUsers()
  } catch (error) {
    console.error('创建医生失败:', error)
    ElMessage.error('创建医生失败')
  } finally {
    creatingDoctor.value = false
  }
}

const fetchRecentUsers = async () => {
  try {
    const response = await api.get('/users/management/users/', {
      params: { ordering: '-date_joined', page_size: 5 }
    })
    recentUsers.value = response.data.results || []
  } catch (error) {
    console.error('获取最近用户失败:', error)
  }
}

onMounted(async () => {
  await fetchUserInfo()
  await fetchStats()
  await fetchHealthAlerts()
  await fetchRecentUsers()
})
</script>

<style scoped>
.admin-dashboard {
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

.stat-icon.total { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-icon.admin { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-icon.doctor { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.stat-icon.regular { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.stat-icon.active { background: linear-gradient(135deg, #fa709a, #fee140); }
.stat-icon.alerts { background: linear-gradient(135deg, #30cfd0, #330867); }

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

.actions-card,
.alerts-card,
.recent-users-card {
  margin-bottom: 20px;
}

.actions-card h3,
.alerts-card h3,
.recent-users-card h3 {
  margin: 0;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
    grid-template-columns: repeat(2, 1fr);
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }

  .alert-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
}
</style>

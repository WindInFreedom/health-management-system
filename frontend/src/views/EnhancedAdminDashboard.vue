<template>
  <div class="enhanced-admin-dashboard">
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
          <el-button @click="refreshAllData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
          <el-button @click="$router.push('/health-report')">
            健康报告
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
            <p class="stat-value">{{ userStats.total_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon admin">👨‍⚕️</div>
          <div class="stat-info">
            <h4>管理员</h4>
            <p class="stat-value">{{ userStats.admin_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon doctor">👩‍⚕️</div>
          <div class="stat-info">
            <h4>医生</h4>
            <p class="stat-value">{{ userStats.doctor_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon regular">👤</div>
          <div class="stat-info">
            <h4>普通用户</h4>
            <p class="stat-value">{{ userStats.regular_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon active">📊</div>
          <div class="stat-info">
            <h4>活跃用户</h4>
            <p class="stat-value">{{ userStats.active_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon alerts">⚠️</div>
          <div class="stat-info">
            <h4>健康预警</h4>
            <p class="stat-value">{{ healthAlerts.total_alerts }}</p>
            <span class="stat-label">条</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <el-card class="chart-card">
        <template #header>
          <h3>用户角色分布</h3>
        </template>
        <div ref="roleChart" style="width: 100%; height: 300px;"></div>
      </el-card>

      <el-card class="chart-card">
        <template #header>
          <h3>健康状态分布</h3>
        </template>
        <div ref="healthStatusChart" style="width: 100%; height: 300px;"></div>
      </el-card>

      <el-card class="chart-card">
        <template #header>
          <h3>血压分布</h3>
        </template>
        <div ref="bloodPressureChart" style="width: 100%; height: 300px;"></div>
      </el-card>

      <el-card class="chart-card">
        <template #header>
          <h3>体重分布</h3>
        </template>
        <div ref="weightChart" style="width: 100%; height: 300px;"></div>
      </el-card>
    </div>

    <!-- Quick Actions -->
    <el-card class="actions-card">
      <template #header>
        <h3>快速操作</h3>
      </template>
      <div class="actions-grid">
        <el-button type="primary" @click="showCreateUserDialog = true">
          <el-icon><Plus /></el-icon>
          创建用户
        </el-button>
        <el-button type="success" @click="showCreateDoctorDialog = true">
          <el-icon><User /></el-icon>
          创建医生
        </el-button>
        <el-button type="warning" @click="showAddMeasurementDialog = true">
          <el-icon><DataAnalysis /></el-icon>
          添加测量数据
        </el-button>
        <el-button type="info" @click="exportData">
          <el-icon><Download /></el-icon>
          导出数据
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
        <div v-if="healthAlerts.alerts?.length === 0" class="no-alerts">
          <p>暂无健康预警</p>
        </div>
        <div v-else>
          <div v-for="alert in healthAlerts.alerts.slice(0, 10)" :key="alert.user.id" class="alert-item">
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
                <el-button size="small" type="primary" @click="editUserData(alert.user.id)">
                  编辑用户
                </el-button>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-card>

    <!-- User Management Table -->
    <el-card class="users-table-card">
      <template #header>
        <div class="card-header">
          <h3>用户管理</h3>
          <div class="table-actions">
            <el-input
              v-model="searchText"
              placeholder="搜索用户..."
              style="width: 200px; margin-right: 10px;"
              clearable
            />
            <el-select v-model="selectedRole" placeholder="筛选角色" style="width: 120px; margin-right: 10px;">
              <el-option label="全部" value="" />
              <el-option label="管理员" value="admin" />
              <el-option label="医生" value="doctor" />
              <el-option label="普通用户" value="user" />
            </el-select>
            <el-button @click="showCreateUserDialog = true" type="primary">
              <el-icon><Plus /></el-icon>
              创建用户
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="filteredUsers" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="科室" width="120" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.date_joined) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_login) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewUserDetails(row.id)">
              查看详情
            </el-button>
            <el-button size="small" type="primary" @click="editUserData(row.id)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteUser(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create User Dialog -->
    <el-dialog v-model="showCreateUserDialog" title="创建用户" width="500px">
      <el-form :model="userForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="userForm.first_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.role" placeholder="选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="医生" value="doctor" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="科室" v-if="userForm.role === 'doctor'">
          <el-input v-model="userForm.department" placeholder="请输入科室" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateUserDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

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
        <el-button type="primary" @click="createDoctor" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- Add Measurement Dialog -->
    <el-dialog v-model="showAddMeasurementDialog" title="添加测量数据" width="500px">
      <el-form :model="measurementForm" label-width="100px">
        <el-form-item label="用户">
          <el-select v-model="measurementForm.user_id" placeholder="选择用户" style="width: 100%">
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="体重 (kg)">
          <el-input-number v-model="measurementForm.weight_kg" :min="30" :max="200" :precision="1" />
        </el-form-item>
        <el-form-item label="收缩压">
          <el-input-number v-model="measurementForm.systolic" :min="60" :max="250" />
        </el-form-item>
        <el-form-item label="舒张压">
          <el-input-number v-model="measurementForm.diastolic" :min="40" :max="150" />
        </el-form-item>
        <el-form-item label="心率">
          <el-input-number v-model="measurementForm.heart_rate" :min="40" :max="200" />
        </el-form-item>
        <el-form-item label="血糖">
          <el-input-number v-model="measurementForm.blood_glucose" :min="2" :max="20" :precision="1" />
        </el-form-item>
        <el-form-item label="测量时间">
          <el-date-picker
            v-model="measurementForm.measured_at"
            type="datetime"
            placeholder="选择时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMeasurementDialog = false">取消</el-button>
        <el-button type="primary" @click="submitMeasurement" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, User, DataAnalysis, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../utils/axios.js'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const submitting = ref(false)
const userInfo = ref({})
const userStats = ref({})
const healthAlerts = ref({ total_alerts: 0, high_priority_alerts: 0, alerts: [] })
const allStats = ref({ total_users: 0, users_stats: [] })
const userList = ref([])
const searchText = ref('')
const selectedRole = ref('')

const showCreateUserDialog = ref(false)
const showCreateDoctorDialog = ref(false)
const showAddMeasurementDialog = ref(false)

const userForm = reactive({
  username: '',
  email: '',
  password: '',
  first_name: '',
  role: 'user',
  department: ''
})

const doctorForm = reactive({
  username: '',
  email: '',
  password: '',
  first_name: '',
  department: ''
})

const measurementForm = reactive({
  user_id: null,
  weight_kg: 70,
  systolic: 120,
  diastolic: 80,
  heart_rate: 75,
  blood_glucose: 5.5,
  measured_at: new Date()
})

// Chart references
const roleChart = ref(null)
const healthStatusChart = ref(null)
const bloodPressureChart = ref(null)
const weightChart = ref(null)

// Computed properties
const filteredUsers = computed(() => {
  let users = userList.value || []
  
  if (searchText.value) {
    users = users.filter(user => 
      user.username.toLowerCase().includes(searchText.value.toLowerCase()) ||
      user.email.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }
  
  if (selectedRole.value) {
    users = users.filter(user => user.role === selectedRole.value)
  }
  
  return users
})

const formatDate = (dateString) => {
  if (!dateString) return '--'
  return new Date(dateString).toLocaleString('zh-CN')
}

const handleLogout = () => {
  authStore.clearToken()
  ElMessage.success('已退出登录')
  router.push('/')
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

const fetchUserInfo = async () => {
  try {
    const response = await api.get('/me/')
    userInfo.value = response.data
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const fetchUserStats = async () => {
  try {
    const response = await api.get('/users/management/statistics/')
    userStats.value = response.data
  } catch (error) {
    console.error('获取用户统计失败:', error)
  }
}

const fetchHealthAlerts = async () => {
  try {
    const response = await api.get('/measurements/admin/alerts-all/')
    healthAlerts.value = response.data
  } catch (error) {
    console.error('获取健康预警失败:', error)
  }
}

const fetchAllStats = async () => {
  try {
    const response = await api.get('/measurements/admin/statistics-all/')
    allStats.value = response.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchUserList = async () => {
  try {
    const response = await api.get('/users/management/users/')
    userList.value = response.data.results || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

const refreshAllData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchUserInfo(),
      fetchUserStats(),
      fetchHealthAlerts(),
      fetchAllStats(),
      fetchUserList()
    ])
    updateCharts()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const refreshAlerts = () => {
  fetchHealthAlerts()
  ElMessage.success('预警数据已刷新')
}

const viewUserDetails = (userId) => {
  router.push(`/user-details/${userId}`)
}

const editUserData = (userId) => {
  router.push(`/edit-user/${userId}`)
}

const deleteUser = async (userId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个用户吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/users/management/users/${userId}/`)
    ElMessage.success('用户删除成功')
    await fetchUserList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除用户失败')
    }
  }
}

const createUser = async () => {
  submitting.value = true
  try {
    await api.post('/users/management/users/', userForm)
    ElMessage.success('用户创建成功')
    showCreateUserDialog.value = false
    
    // 重置表单
    Object.assign(userForm, {
      username: '',
      email: '',
      password: '',
      first_name: '',
      role: 'user',
      department: ''
    })
    
    await fetchUserList()
  } catch (error) {
    console.error('创建用户失败:', error)
    ElMessage.error('创建用户失败')
  } finally {
    submitting.value = false
  }
}

const createDoctor = async () => {
  submitting.value = true
  try {
    await api.post('/users/management/create-doctor/', doctorForm)
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
    
    await fetchUserList()
  } catch (error) {
    console.error('创建医生失败:', error)
    ElMessage.error('创建医生失败')
  } finally {
    submitting.value = false
  }
}

const submitMeasurement = async () => {
  submitting.value = true
  try {
    const data = {
      ...measurementForm,
      measured_at: measurementForm.measured_at.toISOString()
    }
    
    await api.post('/measurements/admin/measurements/', data)
    ElMessage.success('测量数据添加成功')
    showAddMeasurementDialog.value = false
    
    // 重置表单
    Object.assign(measurementForm, {
      user_id: null,
      weight_kg: 70,
      systolic: 120,
      diastolic: 80,
      heart_rate: 75,
      blood_glucose: 5.5,
      measured_at: new Date()
    })
    
    await fetchAllStats()
  } catch (error) {
    console.error('添加测量数据失败:', error)
    ElMessage.error('添加测量数据失败')
  } finally {
    submitting.value = false
  }
}

const exportData = () => {
  ElMessage.info('数据导出功能开发中...')
}

const updateCharts = () => {
  // 角色分布图
  if (roleChart.value) {
    const roleChartInstance = echarts.init(roleChart.value)
    const roleData = [
      { name: '管理员', value: userStats.value.admin_users },
      { name: '医生', value: userStats.value.doctor_users },
      { name: '普通用户', value: userStats.value.regular_users }
    ]
    
    roleChartInstance.setOption({
      title: { text: '用户角色分布', left: 'center' },
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        type: 'pie',
        radius: '50%',
        data: roleData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    })
  }

  // 健康状态分布图
  if (healthStatusChart.value) {
    const healthStatusChartInstance = echarts.init(healthStatusChart.value)
    const healthStatusData = [
      { name: '健康', value: allStats.value.users_stats?.filter(user => user.health_status === '健康').length || 0 },
      { name: '需关注', value: allStats.value.users_stats?.filter(user => user.health_status === '需关注').length || 0 },
      { name: '需改善', value: allStats.value.users_stats?.filter(user => user.health_status === '需改善').length || 0 },
      { name: '需就医', value: allStats.value.users_stats?.filter(user => user.health_status === '需就医').length || 0 }
    ]
    
    healthStatusChartInstance.setOption({
      title: { text: '健康状态分布', left: 'center' },
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        type: 'pie',
        radius: '50%',
        data: healthStatusData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    })
  }

  // 血压分布图
  if (bloodPressureChart.value) {
    const bloodPressureChartInstance = echarts.init(bloodPressureChart.value)
    const bloodPressureData = allStats.value.users_stats?.map(user => ({
      name: user.username,
      value: [user.blood_pressure?.latest_systolic || 0, user.blood_pressure?.latest_diastolic || 0]
    })) || []
    
    bloodPressureChartInstance.setOption({
      title: { text: '血压分布', left: 'center' },
      tooltip: { trigger: 'item' },
      xAxis: { type: 'value', name: '收缩压' },
      yAxis: { type: 'value', name: '舒张压' },
      series: [{
        type: 'scatter',
        data: bloodPressureData,
        symbolSize: 10
      }]
    })
  }

  // 体重分布图
  if (weightChart.value) {
    const weightChartInstance = echarts.init(weightChart.value)
    const weightData = allStats.value.users_stats?.map(user => ({
      name: user.username,
      value: user.weight?.latest || 0
    })) || []
    
    weightChartInstance.setOption({
      title: { text: '体重分布', left: 'center' },
      tooltip: { trigger: 'item' },
      xAxis: { type: 'category', data: weightData.map(item => item.name) },
      yAxis: { type: 'value', name: '体重(kg)' },
      series: [{
        type: 'bar',
        data: weightData.map(item => item.value)
      }]
    })
  }
}

onMounted(async () => {
  await refreshAllData()
})
</script>

<style scoped>
.enhanced-admin-dashboard {
  padding: 20px;
  max-width: 1600px;
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

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card h3 {
  margin: 0;
  color: #303133;
}

.actions-card,
.alerts-card,
.users-table-card {
  margin-bottom: 20px;
}

.actions-card h3,
.alerts-card h3,
.users-table-card h3 {
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

.table-actions {
  display: flex;
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

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }

  .table-actions {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
}
</style>

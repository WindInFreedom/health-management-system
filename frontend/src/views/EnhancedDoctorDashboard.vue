<template>
  <div class="enhanced-doctor-dashboard">
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

    <!-- Overall Statistics -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon total">👥</div>
          <div class="stat-info">
            <h4>总患者数</h4>
            <p class="stat-value">{{ allStats.total_users }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon health">💚</div>
          <div class="stat-info">
            <h4>健康患者</h4>
            <p class="stat-value">{{ getHealthStatusCount('健康') }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon warning">⚠️</div>
          <div class="stat-info">
            <h4>需关注</h4>
            <p class="stat-value">{{ getHealthStatusCount('需关注') }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon danger">🚨</div>
          <div class="stat-info">
            <h4>需改善</h4>
            <p class="stat-value">{{ getHealthStatusCount('需改善') }}</p>
            <span class="stat-label">人</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon alerts">📊</div>
          <div class="stat-info">
            <h4>健康预警</h4>
            <p class="stat-value">{{ healthAlerts.total_alerts }}</p>
            <span class="stat-label">条</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon high-priority">🔥</div>
          <div class="stat-info">
            <h4>高优先级</h4>
            <p class="stat-value">{{ healthAlerts.high_priority_alerts }}</p>
            <span class="stat-label">条</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
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

      <el-card class="chart-card">
        <template #header>
          <h3>血糖分布</h3>
        </template>
        <div ref="glucoseChart" style="width: 100%; height: 300px;"></div>
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

    <!-- Patient Data Table -->
    <el-card class="patients-table-card">
      <template #header>
        <div class="card-header">
          <h3>患者数据管理</h3>
          <div class="table-actions">
            <el-input
              v-model="searchText"
              placeholder="搜索患者..."
              style="width: 200px; margin-right: 10px;"
              clearable
            />
            <el-select v-model="selectedRole" placeholder="筛选角色" style="width: 120px; margin-right: 10px;">
              <el-option label="全部" value="" />
              <el-option label="管理员" value="admin" />
              <el-option label="医生" value="doctor" />
              <el-option label="普通用户" value="user" />
            </el-select>
            <el-button @click="addMeasurement" type="primary">
              <el-icon><Plus /></el-icon>
              添加测量数据
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="filteredPatients" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="user_role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.user_role)">{{ getRoleText(row.user_role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="health_status" label="健康状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getHealthStatusType(row.health_status)">{{ row.health_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最新体重" width="100">
          <template #default="{ row }">
            {{ row.weight?.latest?.toFixed(1) || '--' }} kg
          </template>
        </el-table-column>
        <el-table-column label="最新血压" width="120">
          <template #default="{ row }">
            {{ row.blood_pressure?.latest_systolic || '--' }}/{{ row.blood_pressure?.latest_diastolic || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="最新心率" width="100">
          <template #default="{ row }">
            {{ row.heart_rate?.latest || '--' }} bpm
          </template>
        </el-table-column>
        <el-table-column label="最新血糖" width="100">
          <template #default="{ row }">
            {{ row.blood_glucose?.latest?.toFixed(1) || '--' }} mmol/L
          </template>
        </el-table-column>
        <el-table-column prop="total_measurements" label="测量次数" width="100" />
        <el-table-column prop="latest_measurement" label="最近测量" width="180">
          <template #default="{ row }">
            {{ formatDate(row.latest_measurement) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewPatientDetails(row.user_id)">
              查看详情
            </el-button>
            <el-button size="small" type="primary" @click="editPatientData(row.user_id)">
              编辑数据
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add Measurement Dialog -->
    <el-dialog v-model="showAddMeasurementDialog" title="添加测量数据" width="500px">
      <el-form :model="measurementForm" label-width="100px">
        <el-form-item label="患者">
          <el-select v-model="measurementForm.user_id" placeholder="选择患者" style="width: 100%">
            <el-option
              v-for="patient in allStats.users_stats"
              :key="patient.user_id"
              :label="patient.username"
              :value="patient.user_id"
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
import { ElMessage } from 'element-plus'
import { Refresh, Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../utils/axios.js'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const userInfo = ref({})
const allStats = ref({ total_users: 0, users_stats: [] })
const healthAlerts = ref({ total_alerts: 0, high_priority_alerts: 0, alerts: [] })
const searchText = ref('')
const selectedRole = ref('')
const showAddMeasurementDialog = ref(false)
const submitting = ref(false)

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
const healthStatusChart = ref(null)
const bloodPressureChart = ref(null)
const weightChart = ref(null)
const glucoseChart = ref(null)

// Computed properties
const filteredPatients = computed(() => {
  let patients = allStats.value.users_stats || []
  
  if (searchText.value) {
    patients = patients.filter(patient => 
      patient.username.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }
  
  if (selectedRole.value) {
    patients = patients.filter(patient => patient.user_role === selectedRole.value)
  }
  
  return patients
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

const getHealthStatusType = (status) => {
  const types = {
    '健康': 'success',
    '需关注': 'warning',
    '需改善': 'danger',
    '需就医': 'danger'
  }
  return types[status] || 'info'
}

const getHealthStatusCount = (status) => {
  return allStats.value.users_stats?.filter(user => user.health_status === status).length || 0
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

const fetchAllStats = async () => {
  try {
    const response = await api.get('/measurements/admin/statistics-all/')
    allStats.value = response.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
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

const refreshAllData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchUserInfo(),
      fetchAllStats(),
      fetchHealthAlerts()
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

const viewPatientDetails = (userId) => {
  router.push(`/patient-details/${userId}`)
}

const editPatientData = (userId) => {
  router.push(`/edit-patient-data/${userId}`)
}

const sendRecommendation = (userId) => {
  ElMessage.info('发送建议功能开发中...')
}

const addMeasurement = () => {
  showAddMeasurementDialog.value = true
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
    
    // 刷新数据
    await fetchAllStats()
  } catch (error) {
    console.error('添加测量数据失败:', error)
    ElMessage.error('添加测量数据失败')
  } finally {
    submitting.value = false
  }
}

const updateCharts = () => {
  // 健康状态分布图
  if (healthStatusChart.value) {
    const healthStatusChartInstance = echarts.init(healthStatusChart.value)
    const healthStatusData = [
      { name: '健康', value: getHealthStatusCount('健康') },
      { name: '需关注', value: getHealthStatusCount('需关注') },
      { name: '需改善', value: getHealthStatusCount('需改善') },
      { name: '需就医', value: getHealthStatusCount('需就医') }
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

  // 血糖分布图
  if (glucoseChart.value) {
    const glucoseChartInstance = echarts.init(glucoseChart.value)
    const glucoseData = allStats.value.users_stats?.map(user => ({
      name: user.username,
      value: user.blood_glucose?.latest || 0
    })) || []
    
    glucoseChartInstance.setOption({
      title: { text: '血糖分布', left: 'center' },
      tooltip: { trigger: 'item' },
      xAxis: { type: 'category', data: glucoseData.map(item => item.name) },
      yAxis: { type: 'value', name: '血糖(mmol/L)' },
      series: [{
        type: 'line',
        data: glucoseData.map(item => item.value)
      }]
    })
  }
}

onMounted(async () => {
  await refreshAllData()
})
</script>

<style scoped>
.enhanced-doctor-dashboard {
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
.stat-icon.health { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.stat-icon.warning { background: linear-gradient(135deg, #fa709a, #fee140); }
.stat-icon.danger { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-icon.alerts { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.stat-icon.high-priority { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }

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

.alerts-card,
.patients-table-card {
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

  .table-actions {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
}
</style>

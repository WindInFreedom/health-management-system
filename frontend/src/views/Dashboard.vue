<template>
  <div class="dashboard-container">
    <!-- Header with user info and logout -->
    <el-card class="header-card">
      <div class="header-content">
        <div class="user-info">
          <el-avatar :size="50" />
          <div class="user-details">
            <h3>欢迎回来，{{ username }}</h3>
            <p>健康管理系统</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button @click="$router.push('/measurements')">
            健康记录
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
          <div class="stat-icon weight">
            ⚖️
          </div>
          <div class="stat-info">
            <h4>最新体重</h4>
            <p class="stat-value">{{ latestWeight }} kg</p>
            <span class="stat-change" :class="weightChangeClass">
              {{ weightChange }}
            </span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon pressure">
            ❤️
          </div>
          <div class="stat-info">
            <h4>最新血压</h4>
            <p class="stat-value">{{ latestPressure }}</p>
            <span class="stat-label">mmHg</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon glucose">
            🩸
          </div>
          <div class="stat-info">
            <h4>最新血糖</h4>
            <p class="stat-value">{{ latestGlucose }}</p>
            <span class="stat-label">mmol/L</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon heart">
            💓
          </div>
          <div class="stat-info">
            <h4>最新心率</h4>
            <p class="stat-value">{{ latestHeartRate }}</p>
            <span class="stat-label">bpm</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>体重趋势</h3>
            <el-select v-model="weightPeriod" @change="updateWeightChart" size="small">
              <el-option label="最近7天" value="7" />
              <el-option label="最近30天" value="30" />
              <el-option label="最近90天" value="90" />
            </el-select>
          </div>
        </template>
        <div ref="weightChartRef" class="chart-container"></div>
      </el-card>

      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>血压趋势</h3>
            <el-select v-model="pressurePeriod" @change="updatePressureChart" size="small">
              <el-option label="最近7天" value="7" />
              <el-option label="最近30天" value="30" />
              <el-option label="最近90天" value="90" />
            </el-select>
          </div>
        </template>
        <div ref="pressureChartRef" class="chart-container"></div>
      </el-card>
    </div>

    <!-- Recent Measurements -->
    <el-card class="recent-card">
      <template #header>
        <h3>最近测量记录</h3>
      </template>
      <el-table :data="recentMeasurements" stripe>
        <el-table-column prop="measured_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.measured_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="weight_kg" label="体重(kg)" width="100" />
        <el-table-column prop="systolic" label="收缩压" width="100" />
        <el-table-column prop="diastolic" label="舒张压" width="100" />
        <el-table-column prop="blood_glucose" label="血糖" width="100" />
        <el-table-column prop="heart_rate" label="心率" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push('/measurements')">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '../utils/axios.js'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

// Chart refs
const weightChartRef = ref()
const pressureChartRef = ref()

// Chart instances
let weightChart = null
let pressureChart = null

// Data
const username = ref('用户')
const userAvatar = ref('')
const recentMeasurements = ref([])
const latestWeight = ref('--')
const latestPressure = ref('--/--')
const latestGlucose = ref('--')
const latestHeartRate = ref('--')
const weightChange = ref('--')
const weightChangeClass = ref('')

// Chart periods
const weightPeriod = ref('7')
const pressurePeriod = ref('7')

// Normalize DRF list response - handle both raw arrays and paginated responses
function normalizeListResponse(data) {
  return Array.isArray(data) ? data : (data?.results ?? [])
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const handleLogout = () => {
  authStore.clearToken()
  ElMessage.success('已退出登录')
  router.push('/')
}

const fetchDashboardData = async () => {
  try {
    // Fetch recent measurements
    const measurementsRes = await api.get('/measurements/', {
      params: { page_size: 5, ordering: '-measured_at' }
    })
    recentMeasurements.value = measurementsRes.data.results || measurementsRes.data

    // Calculate latest values
    if (recentMeasurements.value.length > 0) {
      const latest = recentMeasurements.value[0]
      latestWeight.value = latest.weight_kg || '--'
      latestPressure.value = `${latest.systolic || '--'}/${latest.diastolic || '--'}`
      latestGlucose.value = latest.blood_glucose || '--'
      latestHeartRate.value = latest.heart_rate || '--'

      // Calculate weight change
      if (recentMeasurements.value.length > 1 && latest.weight_kg) {
        const previous = recentMeasurements.value[1]
        if (previous.weight_kg) {
          const change = (latest.weight_kg - previous.weight_kg).toFixed(1)
          weightChange.value = change > 0 ? `+${change} kg` : `${change} kg`
          weightChangeClass.value = change > 0 ? 'increase' : 'decrease'
        }
      }
    }

    // Fetch user info (you might need to add a user profile endpoint)
    username.value = '管理员' // This should come from user profile API

  } catch (err) {
    ElMessage.error('获取数据失败')
    console.error('Dashboard data error:', err)
  }
}

const initWeightChart = () => {
  if (!weightChartRef.value) return
  
  weightChart = echarts.init(weightChartRef.value)
  updateWeightChart()
}

const updateWeightChart = async () => {
  if (!weightChart) return

  try {
    const res = await api.get('/measurements/', {
      params: { 
        page_size: weightPeriod.value,
        ordering: 'measured_at'
      }
    })
    
    // Normalize, filter missing measured_at, and sort ascending by time
    const data = normalizeListResponse(res.data)
      .filter(item => item?.measured_at)
      .sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at))
    
    const dates = data.map(item => formatDate(item.measured_at).split(' ')[0])
    const weights = data.map(item => Number(item.weight_kg ?? NaN))

    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: '{b}<br />体重: {c} kg'
      },
      xAxis: {
        type: 'category',
        data: dates
      },
      yAxis: {
        type: 'value',
        name: '体重 (kg)'
      },
      series: [{
        data: weights,
        type: 'line',
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          opacity: 0.3
        }
      }]
    }

    weightChart.setOption(option)
  } catch (err) {
    console.error('Weight chart error:', err)
  }
}

const initPressureChart = () => {
  if (!pressureChartRef.value) return
  
  pressureChart = echarts.init(pressureChartRef.value)
  updatePressureChart()
}

const updatePressureChart = async () => {
  if (!pressureChart) return

  try {
    const res = await api.get('/measurements/', {
      params: { 
        page_size: pressurePeriod.value,
        ordering: 'measured_at'
      }
    })
    
    // Normalize, filter missing measured_at, and sort ascending by time
    const data = normalizeListResponse(res.data)
      .filter(item => item?.measured_at)
      .sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at))
    
    const dates = data.map(item => formatDate(item.measured_at).split(' ')[0])
    const systolic = data.map(item => Number(item.systolic ?? NaN))
    const diastolic = data.map(item => Number(item.diastolic ?? NaN))

    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: '{b}<br />收缩压: {c0} mmHg<br />舒张压: {c1} mmHg'
      },
      legend: {
        data: ['收缩压', '舒张压']
      },
      xAxis: {
        type: 'category',
        data: dates
      },
      yAxis: {
        type: 'value',
        name: '血压 (mmHg)'
      },
      series: [
        {
          name: '收缩压',
          data: systolic,
          type: 'line',
          smooth: true,
          itemStyle: {
            color: '#F56C6C'
          }
        },
        {
          name: '舒张压',
          data: diastolic,
          type: 'line',
          smooth: true,
          itemStyle: {
            color: '#67C23A'
          }
        }
      ]
    }

    pressureChart.setOption(option)
  } catch (err) {
    console.error('Pressure chart error:', err)
  }
}

onMounted(async () => {
  await fetchDashboardData()
  
  await nextTick()
  initWeightChart()
  initPressureChart()

  // Handle window resize
  window.addEventListener('resize', () => {
    weightChart?.resize()
    pressureChart?.resize()
  })
})
</script>

<style scoped>
.dashboard-container {
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

.stat-icon.weight { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-icon.pressure { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-icon.glucose { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.stat-icon.heart { background: linear-gradient(135deg, #43e97b, #38f9d7); }

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

.stat-change {
  font-size: 12px;
  font-weight: bold;
}

.stat-change.increase {
  color: #F56C6C;
}

.stat-change.decrease {
  color: #67C23A;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  min-height: 400px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-header h3 {
  margin: 0;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.recent-card {
  margin-bottom: 20px;
}

.recent-card h3 {
  margin: 0;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 15px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-container {
    height: 250px;
  }
}
</style>

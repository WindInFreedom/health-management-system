<template>
  <div class="advanced-dashboard">
    <!-- Header -->
    <el-card class="header-card">
      <div class="header-content">
        <div class="user-info">
          <el-avatar :size="50" />
          <div class="user-details">
            <h3>欢迎回来，{{ username }}</h3>
            <p>智能健康管理系统</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button @click="$router.push('/measurements')">
            健康记录
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

    <!-- Health Risk Alert -->
    <el-alert
      v-if="healthRisks.length > 0"
      :title="`健康风险提醒：${healthRisks.length}项需要注意`"
      type="warning"
      :closable="false"
      class="risk-alert"
    >
      <template #default>
        <div v-for="risk in healthRisks" :key="risk.type" class="risk-item">
          <el-tag :type="risk.level === 'high' ? 'danger' : 'warning'" size="small">
            {{ risk.message }}
          </el-tag>
        </div>
      </template>
    </el-alert>

    <!-- Statistics Cards -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon weight">⚖️</div>
          <div class="stat-info">
            <h4>最新体重</h4>
            <p class="stat-value">{{ stats.weight?.latest || '--' }} kg</p>
            <span class="stat-change" :class="getChangeClass(stats.weight?.trend)">
              {{ stats.weight?.trend || '--' }}
            </span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon pressure">❤️</div>
          <div class="stat-info">
            <h4>最新血压</h4>
            <p class="stat-value">{{ stats.blood_pressure?.latest_systolic || '--' }}/{{ stats.blood_pressure?.latest_diastolic || '--' }}</p>
            <span class="stat-label">mmHg</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon glucose">🩸</div>
          <div class="stat-info">
            <h4>最新血糖</h4>
            <p class="stat-value">{{ stats.blood_glucose?.latest || '--' }}</p>
            <span class="stat-label">mmol/L</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon heart">💓</div>
          <div class="stat-info">
            <h4>最新心率</h4>
            <p class="stat-value">{{ stats.heart_rate?.latest || '--' }}</p>
            <span class="stat-label">bpm</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <!-- Weight Chart with Prediction -->
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>体重趋势与预测</h3>
            <div class="chart-controls">
              <el-select v-model="weightPeriod" @change="updateWeightChart" size="small">
                <el-option label="最近7天" value="7" />
                <el-option label="最近30天" value="30" />
                <el-option label="最近90天" value="90" />
              </el-select>
              <el-button @click="togglePrediction('weight')" size="small" type="primary">
                {{ showWeightPrediction ? '隐藏预测' : '显示预测' }}
              </el-button>
            </div>
          </div>
        </template>
        <div ref="weightChartRef" class="chart-container"></div>
      </el-card>

      <!-- Blood Pressure Chart with Prediction -->
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>血压趋势与预测</h3>
            <div class="chart-controls">
              <el-select v-model="pressurePeriod" @change="updatePressureChart" size="small">
                <el-option label="最近7天" value="7" />
                <el-option label="最近30天" value="30" />
                <el-option label="最近90天" value="90" />
              </el-select>
              <el-button @click="togglePrediction('pressure')" size="small" type="primary">
                {{ showPressurePrediction ? '隐藏预测' : '显示预测' }}
              </el-button>
            </div>
          </div>
        </template>
        <div ref="pressureChartRef" class="chart-container"></div>
      </el-card>

      <!-- Heart Rate Chart with Prediction -->
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>心率趋势与预测</h3>
            <div class="chart-controls">
              <el-select v-model="heartRatePeriod" @change="updateHeartRateChart" size="small">
                <el-option label="最近7天" value="7" />
                <el-option label="最近30天" value="30" />
                <el-option label="最近90天" value="90" />
              </el-select>
              <el-button @click="togglePrediction('heartRate')" size="small" type="primary">
                {{ showHeartRatePrediction ? '隐藏预测' : '显示预测' }}
              </el-button>
            </div>
          </div>
        </template>
        <div ref="heartRateChartRef" class="chart-container"></div>
      </el-card>

      <!-- Blood Glucose Chart with Prediction -->
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>血糖趋势与预测</h3>
            <div class="chart-controls">
              <el-select v-model="glucosePeriod" @change="updateGlucoseChart" size="small">
                <el-option label="最近7天" value="7" />
                <el-option label="最近30天" value="30" />
                <el-option label="最近90天" value="90" />
              </el-select>
              <el-button @click="togglePrediction('glucose')" size="small" type="primary">
                {{ showGlucosePrediction ? '隐藏预测' : '显示预测' }}
              </el-button>
            </div>
          </div>
        </template>
        <div ref="glucoseChartRef" class="chart-container"></div>
      </el-card>
    </div>

    <!-- Health Recommendations -->
    <el-card class="recommendations-card">
      <template #header>
        <h3>个性化健康建议</h3>
      </template>
      <div class="recommendations-content">
        <div v-if="recommendations.length === 0" class="no-recommendations">
          <p>暂无特殊建议，请继续保持健康的生活方式！</p>
        </div>
        <div v-else>
          <div v-for="rec in recommendations" :key="rec.title" class="recommendation-item">
            <el-alert
              :title="rec.title"
              :type="rec.priority === 'high' ? 'error' : rec.priority === 'medium' ? 'warning' : 'info'"
              :closable="false"
              show-icon
            >
              <template #default>
                <pre>{{ rec.content }}</pre>
              </template>
            </el-alert>
          </div>
        </div>
      </div>
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
const heartRateChartRef = ref()
const glucoseChartRef = ref()

// Chart instances
let weightChart = null
let pressureChart = null
let heartRateChart = null
let glucoseChart = null

// Data
const username = ref('用户')
const stats = ref({})
const recommendations = ref([])
const healthRisks = ref([])
const predictions = ref({})

// Chart periods
const weightPeriod = ref('30')
const pressurePeriod = ref('30')
const heartRatePeriod = ref('30')
const glucosePeriod = ref('30')

// Prediction visibility
const showWeightPrediction = ref(false)
const showPressurePrediction = ref(false)
const showHeartRatePrediction = ref(false)
const showGlucosePrediction = ref(false)

// Normalize DRF list response - handle both raw arrays and paginated responses
function normalizeListResponse(data) {
  return Array.isArray(data) ? data : (data?.results ?? [])
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// Utility to normalize DRF list responses
function normalizeListResponse(data) {
  return Array.isArray(data) ? data : (data?.results ?? [])
}

const handleLogout = () => {
  authStore.clearToken()
  ElMessage.success('已退出登录')
  router.push('/')
}

const getChangeClass = (trend) => {
  if (!trend) return ''
  return trend.includes('上升') ? 'increase' : 'decrease'
}

const fetchHealthStats = async () => {
  try {
    const response = await api.get('/measurements/statistics/')
    stats.value = response.data
    
    // Extract health risks from stats
    const risks = []
    if (stats.value.blood_pressure?.latest_systolic > 140) {
      risks.push({
        type: 'blood_pressure',
        level: 'high',
        message: '血压偏高'
      })
    }
    if (stats.value.blood_glucose?.latest > 7.0) {
      risks.push({
        type: 'blood_glucose',
        level: 'high',
        message: '血糖偏高'
      })
    }
    healthRisks.value = risks
    
  } catch (err) {
    console.error('获取健康统计失败:', err)
  }
}

const fetchRecommendations = async () => {
  try {
    const response = await api.get('/measurements/recommendations/')
    recommendations.value = response.data.recommendations || []
  } catch (err) {
    console.error('获取健康建议失败:', err)
  }
}

const fetchPredictions = async () => {
  try {
    const response = await api.get('/measurements/predict/', {
      params: { days: 7 }
    })
    predictions.value = response.data
  } catch (err) {
    console.error('获取预测数据失败:', err)
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
    const res = await api.get('/measurements/my-measurements/', {
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
    const weights = data.map(item => {
      const val = item.weight_kg
      return val !== null && val !== undefined ? Number(val) : null
    })

    const series = [{
      name: '实际体重',
      data: weights,
      type: 'line',
      smooth: true,
      itemStyle: { color: '#409EFF' },
      areaStyle: { opacity: 0.3 }
    }]

    // Add prediction if enabled
    if (showWeightPrediction.value && predictions.value.weight) {
      const predDates = predictions.value.dates || []
      const predWeights = predictions.value.weight.predicted || []
      
      series.push({
        name: '预测体重',
        data: [...Array(weights.length - 1).fill(null), weights[weights.length - 1], ...predWeights],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#F56C6C' },
        lineStyle: { type: 'dashed' }
      })
    }

    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['实际体重', '预测体重'] },
      xAxis: {
        type: 'category',
        data: [...dates, ...(predictions.value.dates || [])]
      },
      yAxis: { type: 'value', name: '体重 (kg)' },
      series
    }

    weightChart.setOption(option)
  } catch (err) {
    console.error('获取体重数据失败:', err)
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
    const res = await api.get('/measurements/my-measurements/', {
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
    const systolic = data.map(item => {
      const val = item.systolic
      return val !== null && val !== undefined ? Number(val) : null
    })
    const diastolic = data.map(item => {
      const val = item.diastolic
      return val !== null && val !== undefined ? Number(val) : null
    })

    const series = [
      {
        name: '收缩压',
        data: systolic,
        type: 'line',
        smooth: true,
        itemStyle: { color: '#F56C6C' }
      },
      {
        name: '舒张压',
        data: diastolic,
        type: 'line',
        smooth: true,
        itemStyle: { color: '#67C23A' }
      }
    ]

    // Add prediction if enabled
    if (showPressurePrediction.value && predictions.value.blood_pressure) {
      const predDates = predictions.value.dates || []
      const predSystolic = predictions.value.blood_pressure.predicted.systolic || []
      const predDiastolic = predictions.value.blood_pressure.predicted.diastolic || []
      
      series.push({
        name: '预测收缩压',
        data: [...Array(systolic.length - 1).fill(null), systolic[systolic.length - 1], ...predSystolic],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#F56C6C' },
        lineStyle: { type: 'dashed' }
      })
      
      series.push({
        name: '预测舒张压',
        data: [...Array(diastolic.length - 1).fill(null), diastolic[diastolic.length - 1], ...predDiastolic],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#67C23A' },
        lineStyle: { type: 'dashed' }
      })
    }

    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['收缩压', '舒张压', '预测收缩压', '预测舒张压'] },
      xAxis: {
        type: 'category',
        data: [...dates, ...(predictions.value.dates || [])]
      },
      yAxis: { type: 'value', name: '血压 (mmHg)' },
      series
    }

    pressureChart.setOption(option)
  } catch (err) {
    console.error('血压图表错误:', err)
  }
}

const initHeartRateChart = () => {
  if (!heartRateChartRef.value) return
  heartRateChart = echarts.init(heartRateChartRef.value)
  updateHeartRateChart()
}

const updateHeartRateChart = async () => {
  if (!heartRateChart) return

  try {
    const res = await api.get('/measurements/my-measurements/', {
      params: { 
        page_size: heartRatePeriod.value,
        ordering: 'measured_at'
      }
    })
    
    // Normalize, filter missing measured_at, and sort ascending by time
    const data = normalizeListResponse(res.data)
      .filter(item => item?.measured_at)
      .sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at))
    
    const dates = data.map(item => formatDate(item.measured_at).split(' ')[0])
    const heartRates = data.map(item => {
      const val = item.heart_rate
      return val !== null && val !== undefined ? Number(val) : null
    })

    const series = [{
      name: '实际心率',
      data: heartRates,
      type: 'line',
      smooth: true,
      itemStyle: { color: '#E6A23C' }
    }]

    // Add prediction if enabled
    if (showHeartRatePrediction.value && predictions.value.heart_rate) {
      const predDates = predictions.value.dates || []
      const predHeartRates = predictions.value.heart_rate.predicted || []
      
      series.push({
        name: '预测心率',
        data: [...Array(heartRates.length - 1).fill(null), heartRates[heartRates.length - 1], ...predHeartRates],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#E6A23C' },
        lineStyle: { type: 'dashed' }
      })
    }

    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['实际心率', '预测心率'] },
      xAxis: {
        type: 'category',
        data: [...dates, ...(predictions.value.dates || [])]
      },
      yAxis: { type: 'value', name: '心率 (bpm)' },
      series
    }

    heartRateChart.setOption(option)
  } catch (err) {
    console.error('心率图表错误:', err)
  }
}

const initGlucoseChart = () => {
  if (!glucoseChartRef.value) return
  glucoseChart = echarts.init(glucoseChartRef.value)
  updateGlucoseChart()
}

const updateGlucoseChart = async () => {
  if (!glucoseChart) return

  try {
    const res = await api.get('/measurements/my-measurements/', {
      params: { 
        page_size: glucosePeriod.value,
        ordering: 'measured_at'
      }
    })
    
    // Normalize, filter missing measured_at, and sort ascending by time
    const data = normalizeListResponse(res.data)
      .filter(item => item?.measured_at)
      .sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at))
    
    const dates = data.map(item => formatDate(item.measured_at).split(' ')[0])
    const glucose = data.map(item => {
      const val = item.blood_glucose
      return val !== null && val !== undefined ? Number(val) : null
    })

    const series = [{
      name: '实际血糖',
      data: glucose,
      type: 'line',
      smooth: true,
      itemStyle: { color: '#909399' }
    }]

    // Add prediction if enabled
    if (showGlucosePrediction.value && predictions.value.blood_glucose) {
      const predDates = predictions.value.dates || []
      const predGlucose = predictions.value.blood_glucose.predicted || []
      
      series.push({
        name: '预测血糖',
        data: [...Array(glucose.length - 1).fill(null), glucose[glucose.length - 1], ...predGlucose],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#909399' },
        lineStyle: { type: 'dashed' }
      })
    }

    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['实际血糖', '预测血糖'] },
      xAxis: {
        type: 'category',
        data: [...dates, ...(predictions.value.dates || [])]
      },
      yAxis: { type: 'value', name: '血糖 (mmol/L)' },
      series
    }

    glucoseChart.setOption(option)
  } catch (err) {
    console.error('血糖图表错误:', err)
  }
}

const togglePrediction = (type) => {
  switch (type) {
    case 'weight':
      showWeightPrediction.value = !showWeightPrediction.value
      updateWeightChart()
      break
    case 'pressure':
      showPressurePrediction.value = !showPressurePrediction.value
      updatePressureChart()
      break
    case 'heartRate':
      showHeartRatePrediction.value = !showHeartRatePrediction.value
      updateHeartRateChart()
      break
    case 'glucose':
      showGlucosePrediction.value = !showGlucosePrediction.value
      updateGlucoseChart()
      break
  }
}

onMounted(async () => {
  await fetchHealthStats()
  await fetchRecommendations()
  await fetchPredictions()
  
  await nextTick()
  initWeightChart()
  initPressureChart()
  initHeartRateChart()
  initGlucoseChart()

  // Handle window resize
  window.addEventListener('resize', () => {
    weightChart?.resize()
    pressureChart?.resize()
    heartRateChart?.resize()
    glucoseChart?.resize()
  })
})
</script>

<style scoped>
.advanced-dashboard {
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

.risk-alert {
  margin-bottom: 20px;
}

.risk-item {
  margin: 5px 0;
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
  grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
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

.chart-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.recommendations-card {
  margin-bottom: 20px;
}

.recommendations-card h3 {
  margin: 0;
}

.recommendations-content {
  max-height: 400px;
  overflow-y: auto;
}

.recommendation-item {
  margin-bottom: 15px;
}

.recommendation-item pre {
  white-space: pre-wrap;
  font-family: inherit;
  margin: 0;
}

.no-recommendations {
  text-align: center;
  color: #909399;
  padding: 20px;
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

  .chart-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }

  .chart-controls {
    flex-direction: column;
    width: 100%;
  }
}
</style>

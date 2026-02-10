<template>
  <div class="health-report-page">
    <el-card class="header-card">
      <div class="header-content">
        <h2>个人健康报告</h2>
        <div class="header-actions">
          <el-select v-model="days" @change="loadReport" placeholder="选择时间范围" style="width: 150px; margin-right: 10px;">
            <el-option label="最近7天" :value="7" />
            <el-option label="最近30天" :value="30" />
            <el-option label="最近90天" :value="90" />
          </el-select>
          <el-button type="primary" @click="loadReport" :loading="loading">
            刷新报告
          </el-button>
        </div>
      </div>
    </el-card>

    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" size="large"><Loading /></el-icon>
      <p>正在生成健康报告...</p>
    </div>

    <div v-else-if="reportData" class="report-content">
      <!-- Overall Score Card -->
      <el-card class="overall-score-card">
        <h3>综合健康评分</h3>
        <div class="score-display">
          <div class="score-circle" :class="getScoreClass(reportData.overall_score)">
            <span class="score-value">{{ reportData.overall_score || '--' }}</span>
            <span class="score-label">/ 100</span>
          </div>
          <div class="score-details">
            <h4>{{ reportData.overall_message }}</h4>
            <el-tag :type="getStatusType(reportData.overall_status)" size="large">
              {{ getStatusText(reportData.overall_status) }}
            </el-tag>
            <div class="suggestions">
              <p v-for="(suggestion, index) in reportData.overall_suggestions" :key="index">
                {{ suggestion }}
              </p>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Radar Chart -->
      <el-card class="radar-chart-card">
        <h3>健康指标雷达图</h3>
        <div ref="radarChartRef" class="radar-chart"></div>
      </el-card>

      <!-- Dimension Details -->
      <div class="dimensions-grid">
        <el-card 
          v-for="(dimension, key) in reportData.dimensions" 
          :key="key"
          class="dimension-card"
          :class="getStatusClass(dimension.status)"
        >
          <div class="dimension-header">
            <h4>{{ getDimensionLabel(key) }}</h4>
            <el-tag :type="getStatusType(dimension.status)">
              {{ dimension.score || '--' }}分
            </el-tag>
          </div>
          <div class="dimension-body">
            <p class="dimension-value">{{ dimension.message }}</p>
            <div v-if="dimension.value" class="dimension-metric">
              当前值: <strong>{{ formatValue(key, dimension.value) }}</strong>
            </div>
            <div class="dimension-suggestions">
              <p v-for="(suggestion, index) in dimension.suggestions" :key="index" class="suggestion-item">
                • {{ suggestion }}
              </p>
            </div>
          </div>
        </el-card>
      </div>

      <!-- Report Info -->
      <el-card class="report-info">
        <p><strong>评估周期:</strong> {{ days }}天</p>
        <p><strong>生成时间:</strong> {{ formatDate(reportData.evaluated_at) }}</p>
      </el-card>
    </div>

    <el-empty v-else description="暂无数据，请先记录健康数据" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../utils/axios.js'

const loading = ref(false)
const reportData = ref(null)
const days = ref(30)
const radarChartRef = ref(null)
let radarChart = null

const dimensionLabels = {
  bmi: 'BMI指数',
  blood_pressure: '血压',
  heart_rate: '心率',
  blood_glucose: '血糖',
  sleep_quality: '睡眠质量',
  mood_index: '心情指数'
}

// 监听 reportData 变化，当数据更新时自动渲染图表
watch(reportData, async (newData) => {
  if (newData && newData.dimensions) {
    console.log('📊 检测到报告数据更新，准备渲染雷达图')
    // 等待 DOM 更新
    await nextTick()
    // 再等待一小段时间确保 DOM 完全渲染
    setTimeout(() => {
      renderRadarChart()
    }, 50)
  }
})

onMounted(() => {
  loadReport()
})

// 组件卸载时清理图表
onBeforeUnmount(() => {
  if (radarChart) {
    radarChart.dispose()
    radarChart = null
  }
  // 移除 resize 监听器（防止内存泄漏）
  window.removeEventListener('resize', handleResize)
})

// 定义 resize 处理函数
const handleResize = () => {
  radarChart?.resize()
}

async function loadReport() {
  loading.value = true
  try {
    const { data } = await api.get('/health-report/', {
      params: { days: days.value }
    })
    console.log('✅ 健康报告数据加载成功:', data)
    reportData.value = data
    // watch 会自动触发图表渲染
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '加载报告失败')
    console.error('❌ 加载报告失败:', error)
  } finally {
    loading.value = false
  }
}

function renderRadarChart() {
  console.log('🎨 开始渲染雷达图...')
  console.log('DOM元素存在:', !!radarChartRef.value)
  console.log('数据存在:', !!reportData.value)

  if (!radarChartRef.value) {
    console.error('❌ 雷达图DOM元素不存在')
    return
  }

  if (!reportData.value || !reportData.value.dimensions) {
    console.error('❌ 报告数据或维度数据不存在')
    return
  }

  // 销毁已存在的图表实例
  if (radarChart) {
    radarChart.dispose()
    radarChart = null
  }

  try {
    // 初始化图表
    radarChart = echarts.init(radarChartRef.value)
    console.log('✅ ECharts 实例初始化成功')

    const dimensions = reportData.value.dimensions
    const indicator = []
    const data = []

    console.log('📋 维度数据:', dimensions)

    // 构建雷达图数据
    Object.keys(dimensions).forEach(key => {
      const dim = dimensions[key]
      console.log(`  - ${key}:`, dim)

      if (dim && typeof dim.score === 'number' && !isNaN(dim.score)) {
        indicator.push({
          name: dimensionLabels[key] || key,
          max: 100
        })
        data.push(dim.score)
      }
    })

    console.log('📊 雷达图指标:', indicator)
    console.log('📊 雷达图数据:', data)

    if (indicator.length === 0) {
      console.warn('⚠️  没有可用的雷达图数据')
      ElMessage.warning('暂无足够的健康数据生成雷达图')
      return
    }

    const option = {
      tooltip: {
        trigger: 'item'
      },
      radar: {
        indicator: indicator,
        shape: 'polygon',
        splitNumber: 4,
        name: {
          textStyle: {
            color: '#333',
            fontSize: 14
          }
        },
        splitLine: {
          lineStyle: {
            color: '#e0e0e0'
          }
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: ['rgba(102, 126, 234, 0.05)', 'rgba(102, 126, 234, 0.1)']
          }
        },
        axisLine: {
          lineStyle: {
            color: '#ccc'
          }
        }
      },
      series: [
        {
          name: '健康指标',
          type: 'radar',
          data: [
            {
              value: data,
              name: '当前健康状况',
              areaStyle: {
                color: 'rgba(102, 126, 234, 0.3)'
              },
              lineStyle: {
                color: '#667eea',
                width: 2
              },
              itemStyle: {
                color: '#667eea'
              }
            }
          ]
        }
      ]
    }

    radarChart.setOption(option)
    console.log('✅ 雷达图渲染成功!')

    // 添加窗口大小变化监听
    window.addEventListener('resize', handleResize)

  } catch (error) {
    console.error('❌ 雷达图渲染错误:', error)
    ElMessage.error('雷达图渲染失败，请查看控制台')
  }
}

function getDimensionLabel(key) {
  return dimensionLabels[key] || key
}

function getScoreClass(score) {
  if (!score) return 'score-none'
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  return 'score-warning'
}

function getStatusClass(status) {
  const classes = {
    'good': 'status-good',
    'excellent': 'status-excellent',
    'moderate': 'status-moderate',
    'warning': 'status-warning',
    'needs_attention': 'status-warning',
    'insufficient_data': 'status-insufficient'
  }
  return classes[status] || ''
}

function getStatusType(status) {
  const types = {
    'good': 'success',
    'excellent': 'success',
    'moderate': 'warning',
    'warning': 'danger',
    'needs_attention': 'danger',
    'insufficient_data': 'info'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    'good': '良好',
    'excellent': '优秀',
    'moderate': '一般',
    'warning': '需要关注',
    'needs_attention': '需要关注',
    'insufficient_data': '数据不足'
  }
  return texts[status] || status
}

function formatValue(key, value) {
  if (key === 'blood_pressure' && typeof value === 'object') {
    return `${value.systolic}/${value.diastolic} mmHg`
  }
  return value
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.health-report-page {
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

.header-content h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
}

.loading-container {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.loading-container .el-icon {
  font-size: 48px;
  margin-bottom: 20px;
  color: #667eea;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.overall-score-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.overall-score-card h3 {
  margin-top: 0;
  color: white;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 40px;
}

.score-circle {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 4px solid rgba(255, 255, 255, 0.5);
}

.score-value {
  font-size: 48px;
  font-weight: bold;
}

.score-label {
  font-size: 16px;
  opacity: 0.9;
}

.score-details {
  flex: 1;
}

.score-details h4 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.suggestions {
  margin-top: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.suggestions p {
  margin: 8px 0;
  line-height: 1.6;
}

.radar-chart-card {
  min-height: 500px;
}

.radar-chart {
  width: 100%;
  height: 450px;
  min-height: 450px;
}

.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.dimension-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.dimension-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

.dimension-header h4 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.dimension-body {
  color: #666;
}

.dimension-value {
  font-size: 14px;
  margin-bottom: 10px;
  color: #333;
}

.dimension-metric {
  margin: 10px 0;
  padding: 8px;
  background: #f9f9f9;
  border-radius: 5px;
  font-size: 14px;
}

.dimension-suggestions {
  margin-top: 15px;
}

.suggestion-item {
  margin: 5px 0;
  font-size: 13px;
  line-height: 1.6;
  color: #666;
}

.report-info {
  margin-top: 10px;
  background: #f9f9f9;
}

.report-info p {
  margin: 8px 0;
  color: #666;
}

/* Status colors */
.status-good, .status-excellent {
  border-left: 4px solid #67c23a;
}

.status-moderate {
  border-left: 4px solid #e6a23c;
}

.status-warning {
  border-left: 4px solid #f56c6c;
}

.status-insufficient {
  border-left: 4px solid #909399;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .health-report-page {
    padding: 10px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .score-display {
    flex-direction: column;
    gap: 20px;
  }

  .dimensions-grid {
    grid-template-columns: 1fr;
  }

  .radar-chart {
    height: 350px;
  }
}
</style>
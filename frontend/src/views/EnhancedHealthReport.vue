<!-- 替换本地内容：增强的健康报告页面 - 雷达图可视化和多维度评分 -->
<template>
  <div class="enhanced-health-report">
    <!-- 头部 -->
    <el-card class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h2>个人健康报告</h2>
          <p>生成时间: {{ formatDate(reportData?.generated_at) }}</p>
        </div>
        <div class="actions">
          <el-button @click="loadReport" :loading="loading" type="primary" :icon="Refresh">
            刷新报告
          </el-button>
          <el-button @click="exportReport" :icon="Download">导出报告</el-button>
          <el-button @click="$router.push('/dashboard-user')">返回仪表板</el-button>
        </div>
      </div>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 报告内容 -->
    <div v-else-if="reportData" class="report-content">
      <!-- 总体评分卡片 -->
      <el-card class="overall-score-card">
        <h3>总体健康评分</h3>
        <div class="score-display">
          <div class="score-circle">
            <el-progress
              type="circle"
              :percentage="reportData.overall_score"
              :width="150"
              :stroke-width="12"
              :color="getScoreColor(reportData.overall_score)"
            >
              <template #default="{ percentage }">
                <span class="score-text">{{ percentage }}</span>
                <span class="score-label">分</span>
              </template>
            </el-progress>
          </div>
          <div class="score-advice">
            <el-alert
              :title="reportData.overall_advice"
              :type="getScoreAlertType(reportData.overall_score)"
              :closable="false"
              show-icon
            />
          </div>
        </div>
      </el-card>

      <!-- 雷达图 -->
      <el-card class="radar-chart-card">
        <template #header>
          <h3>多维度健康评估</h3>
        </template>
        <div ref="radarChartRef" class="radar-chart"></div>
      </el-card>

      <!-- 维度详细评分 -->
      <el-card class="dimensions-card">
        <template #header>
          <h3>各项指标详情</h3>
        </template>
        <div class="dimensions-grid">
          <div
            v-for="dimension in reportData.dimensions"
            :key="dimension.name"
            class="dimension-item"
          >
            <div class="dimension-header">
              <h4>{{ dimension.name }}</h4>
              <el-tag :type="getDimensionTagType(dimension.score)">
                {{ dimension.score }} 分
              </el-tag>
            </div>
            <div class="dimension-value">
              <span class="value-label">当前值:</span>
              <span class="value-text">{{ dimension.value }}</span>
            </div>
            <el-progress
              :percentage="dimension.score"
              :color="getScoreColor(dimension.score)"
              :stroke-width="8"
            />
            <div class="dimension-advice">
              <el-icon class="advice-icon"><InfoFilled /></el-icon>
              <span>{{ dimension.advice }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 健康趋势 -->
      <el-card v-if="forecastData" class="forecast-card">
        <template #header>
          <h3>健康趋势预测</h3>
        </template>
        <div class="forecast-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="趋势">
              <el-tag :type="getTrendType(forecastData.trend)">
                {{ getTrendText(forecastData.trend) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="历史平均">
              {{ forecastData.historical_average }}
            </el-descriptions-item>
            <el-descriptions-item label="最近平均">
              {{ forecastData.recent_average }}
            </el-descriptions-item>
            <el-descriptions-item label="预测周期">
              {{ forecastData.horizon_days }} 天
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="暂无健康报告数据">
        <el-button type="primary" @click="loadReport">生成健康报告</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Download, InfoFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../utils/axios'

const router = useRouter()
const loading = ref(false)
const reportData = ref(null)
const forecastData = ref(null)
const radarChartRef = ref(null)
let radarChart = null

// 加载健康报告
const loadReport = async () => {
  loading.value = true
  try {
    // 获取健康报告
    const reportResponse = await api.get('/measurements/health-report/')
    reportData.value = reportResponse.data
    
    // 获取预测数据
    try {
      const forecastResponse = await api.get('/measurements/health-forecast/', {
        params: { metric: 'weight', horizon: 7 }
      })
      forecastData.value = forecastResponse.data
    } catch (error) {
      console.log('预测数据加载失败:', error)
    }
    
    // 渲染雷达图
    await nextTick()
    renderRadarChart()
    
    ElMessage.success('健康报告生成成功')
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error(error.response?.data?.error || '加载报告失败')
  } finally {
    loading.value = false
  }
}

// 渲染雷达图
const renderRadarChart = () => {
  if (!radarChartRef.value || !reportData.value) return

  if (radarChart) {
    radarChart.dispose()
  }

  radarChart = echarts.init(radarChartRef.value)

  const dimensions = reportData.value.dimensions
  const indicator = dimensions.map(d => ({
    name: d.name,
    max: 100
  }))

  const values = dimensions.map(d => d.score)

  const option = {
    title: {
      text: '健康维度评分雷达图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: indicator,
      shape: 'polygon',
      splitNumber: 5,
      name: {
        textStyle: {
          color: '#303133',
          fontSize: 12
        }
      },
      splitLine: {
        lineStyle: {
          color: ['#E4E7ED', '#E4E7ED', '#E4E7ED', '#E4E7ED', '#E4E7ED']
        }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(64, 158, 255, 0.1)', 'rgba(255, 255, 255, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: '#DCDFE6'
        }
      }
    },
    series: [
      {
        name: '健康评分',
        type: 'radar',
        data: [
          {
            value: values,
            name: '当前评分',
            areaStyle: {
              color: 'rgba(64, 158, 255, 0.3)'
            },
            lineStyle: {
              color: '#409EFF',
              width: 2
            },
            itemStyle: {
              color: '#409EFF'
            }
          }
        ]
      }
    ]
  }

  radarChart.setOption(option)

  // 响应式
  window.addEventListener('resize', () => {
    radarChart?.resize()
  })
}

// 导出报告
const exportReport = () => {
  if (!radarChart) {
    ElMessage.warning('请先生成报告')
    return
  }
  
  // 导出雷达图为图片
  const url = radarChart.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  
  const link = document.createElement('a')
  link.href = url
  link.download = `健康报告_${new Date().toLocaleDateString()}.png`
  link.click()
  
  ElMessage.success('报告已导出')
}

// 获取评分颜色
const getScoreColor = (score) => {
  if (score >= 85) return '#67C23A'
  if (score >= 70) return '#409EFF'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 获取评分警告类型
const getScoreAlertType = (score) => {
  if (score >= 85) return 'success'
  if (score >= 70) return 'info'
  if (score >= 60) return 'warning'
  return 'error'
}

// 获取维度标签类型
const getDimensionTagType = (score) => {
  if (score >= 85) return 'success'
  if (score >= 70) return ''
  if (score >= 60) return 'warning'
  return 'danger'
}

// 获取趋势类型
const getTrendType = (trend) => {
  const typeMap = {
    'increasing': 'warning',
    'decreasing': 'info',
    'stable': 'success'
  }
  return typeMap[trend] || 'info'
}

// 获取趋势文本
const getTrendText = (trend) => {
  const textMap = {
    'increasing': '上升趋势',
    'decreasing': '下降趋势',
    'stable': '保持稳定'
  }
  return textMap[trend] || '未知'
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.enhanced-health-report {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.title-section p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 12px;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.overall-score-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.overall-score-card h3 {
  margin: 0 0 24px 0;
  font-size: 20px;
  text-align: center;
}

.score-display {
  display: flex;
  align-items: center;
  justify-content: space-around;
  gap: 32px;
}

.score-circle {
  flex-shrink: 0;
}

.score-text {
  font-size: 32px;
  font-weight: bold;
}

.score-label {
  font-size: 16px;
  margin-left: 4px;
}

.score-advice {
  flex: 1;
}

.radar-chart-card {
  min-height: 500px;
}

.radar-chart {
  height: 450px;
  width: 100%;
}

.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.dimension-item {
  padding: 20px;
  border: 1px solid #EBEEF5;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s;
}

.dimension-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dimension-header h4 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.dimension-value {
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.value-label {
  color: #909399;
  margin-right: 8px;
}

.value-text {
  font-weight: 600;
}

.dimension-advice {
  margin-top: 12px;
  padding: 8px;
  background: #F5F7FA;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.advice-icon {
  color: #409EFF;
  margin-top: 2px;
  flex-shrink: 0;
}

.forecast-card {
  margin-bottom: 24px;
}

.forecast-info {
  padding: 16px 0;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .actions {
    flex-direction: column;
    width: 100%;
  }

  .score-display {
    flex-direction: column;
  }

  .dimensions-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<template>
  <div class="health-report">
    <!-- Header -->
    <el-card class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h2>健康档案报告</h2>
          <p>生成时间: {{ formatDate(new Date()) }}</p>
        </div>
        <div class="actions">
          <el-button @click="generateReport" :loading="loading" type="primary">
            生成报告
          </el-button>
          <el-button @click="$router.push('/dashboard')">
            返回仪表板
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Report Content -->
    <div v-if="reportData" class="report-content">
      <!-- Basic Information -->
      <el-card class="report-section">
        <template #header>
          <h3>基本信息</h3>
        </template>
        <div class="info-grid">
          <div class="info-item">
            <label>姓名:</label>
            <span>{{ reportData.user_info?.username || '用户' }}</span>
          </div>
          <div class="info-item">
            <label>数据周期:</label>
            <span>{{ formatDate(reportData.date_range?.start) }} 至 {{ formatDate(reportData.date_range?.end) }}</span>
          </div>
          <div class="info-item">
            <label>测量次数:</label>
            <span>{{ reportData.total_measurements }} 次</span>
          </div>
          <div class="info-item">
            <label>健康评级:</label>
            <el-tag :type="getHealthRatingType(reportData.overall_health_rating)">
              {{ reportData.overall_health_rating }}
            </el-tag>
          </div>
        </div>
      </el-card>

      <!-- Health Statistics -->
      <el-card class="report-section">
        <template #header>
          <h3>健康数据统计</h3>
        </template>
        <div class="stats-table">
          <table>
            <thead>
              <tr>
                <th>指标</th>
                <th>最新值</th>
                <th>平均值</th>
                <th>最高值</th>
                <th>最低值</th>
                <th>标准差</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>体重 (kg)</td>
                <td>{{ reportData.statistics?.weight?.latest?.toFixed(1) || '--' }}</td>
                <td>{{ reportData.statistics?.weight?.average?.toFixed(1) || '--' }}</td>
                <td>{{ reportData.statistics?.weight?.max?.toFixed(1) || '--' }}</td>
                <td>{{ reportData.statistics?.weight?.min?.toFixed(1) || '--' }}</td>
                <td>{{ reportData.statistics?.weight?.std_dev?.toFixed(2) || '--' }}</td>
                <td>
                  <el-tag :type="getWeightStatus(reportData.statistics?.weight?.latest)">
                    {{ getWeightStatusText(reportData.statistics?.weight?.latest) }}
                  </el-tag>
                </td>
              </tr>
              <tr>
                <td>收缩压 (mmHg)</td>
                <td>{{ reportData.statistics?.blood_pressure?.latest_systolic || '--' }}</td>
                <td>{{ Math.round(reportData.statistics?.blood_pressure?.avg_systolic) || '--' }}</td>
                <td>{{ reportData.statistics?.blood_pressure?.max_systolic || '--' }}</td>
                <td>{{ reportData.statistics?.blood_pressure?.min_systolic || '--' }}</td>
                <td>--</td>
                <td>
                  <el-tag :type="getBloodPressureStatus(reportData.statistics?.blood_pressure?.latest_systolic, reportData.statistics?.blood_pressure?.latest_diastolic)">
                    {{ getBloodPressureStatusText(reportData.statistics?.blood_pressure?.latest_systolic, reportData.statistics?.blood_pressure?.latest_diastolic) }}
                  </el-tag>
                </td>
              </tr>
              <tr>
                <td>舒张压 (mmHg)</td>
                <td>{{ reportData.statistics?.blood_pressure?.latest_diastolic || '--' }}</td>
                <td>{{ Math.round(reportData.statistics?.blood_pressure?.avg_diastolic) || '--' }}</td>
                <td>{{ reportData.statistics?.blood_pressure?.max_diastolic || '--' }}</td>
                <td>{{ reportData.statistics?.blood_pressure?.min_diastolic || '--' }}</td>
                <td>--</td>
                <td>--</td>
              </tr>
              <tr>
                <td>心率 (bpm)</td>
                <td>{{ reportData.statistics?.heart_rate?.latest || '--' }}</td>
                <td>{{ Math.round(reportData.statistics?.heart_rate?.average) || '--' }}</td>
                <td>{{ reportData.statistics?.heart_rate?.max || '--' }}</td>
                <td>{{ reportData.statistics?.heart_rate?.min || '--' }}</td>
                <td>{{ reportData.statistics?.heart_rate?.std_dev?.toFixed(2) || '--' }}</td>
                <td>
                  <el-tag :type="getHeartRateStatus(reportData.statistics?.heart_rate?.latest)">
                    {{ getHeartRateStatusText(reportData.statistics?.heart_rate?.latest) }}
                  </el-tag>
                </td>
              </tr>
              <tr>
                <td>血糖 (mmol/L)</td>
                <td>{{ reportData.statistics?.blood_glucose?.latest?.toFixed(1) || '--' }}</td>
                <td>{{ reportData.statistics?.blood_glucose?.average?.toFixed(1) || '--' }}</td>
                <td>{{ reportData.statistics?.blood_glucose?.max?.toFixed(1) || '--' }}</td>
                <td>{{ reportData.statistics?.blood_glucose?.min?.toFixed(1) || '--' }}</td>
                <td>{{ reportData.statistics?.blood_glucose?.std_dev?.toFixed(2) || '--' }}</td>
                <td>
                  <el-tag :type="getGlucoseStatus(reportData.statistics?.blood_glucose?.latest)">
                    {{ getGlucoseStatusText(reportData.statistics?.blood_glucose?.latest) }}
                  </el-tag>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </el-card>

      <!-- Health Trends -->
      <el-card class="report-section">
        <template #header>
          <h3>健康趋势分析</h3>
        </template>
        <div class="trends-content">
          <div v-for="trend in reportData.trends" :key="trend.metric" class="trend-item">
            <h4>{{ getMetricName(trend.metric) }}</h4>
            <p><strong>趋势:</strong> {{ trend.trend }}</p>
            <p><strong>变化率:</strong> {{ trend.change_rate?.toFixed(2) || '--' }}%</p>
            <p><strong>分析:</strong> {{ trend.analysis }}</p>
          </div>
        </div>
      </el-card>

      <!-- Risk Assessment -->
      <el-card class="report-section">
        <template #header>
          <h3>风险评估</h3>
        </template>
        <div class="risk-content">
          <div class="overall-risk">
            <h4>总体风险评估: {{ reportData.risk_assessment?.overall_risk }}</h4>
            <el-progress 
              :percentage="getRiskPercentage(reportData.risk_assessment?.overall_risk)"
              :status="getRiskStatus(reportData.risk_assessment?.overall_risk)"
              :stroke-width="20"
            />
          </div>
          
          <div v-if="reportData.risk_assessment?.risks?.length > 0" class="risk-list">
            <h4>具体风险项:</h4>
            <div v-for="risk in reportData.risk_assessment.risks" :key="risk.type" class="risk-item">
              <el-alert
                :title="risk.message"
                :type="risk.level === 'high' ? 'error' : risk.level === 'medium' ? 'warning' : 'info'"
                :closable="false"
              />
            </div>
          </div>
        </div>
      </el-card>

      <!-- Recommendations -->
      <el-card class="report-section">
        <template #header>
          <h3>健康建议</h3>
        </template>
        <div class="recommendations-content">
          <div v-if="reportData.risk_assessment?.recommendations?.length > 0">
            <div v-for="rec in reportData.risk_assessment.recommendations" :key="rec.category" class="recommendation-category">
              <h4>{{ rec.category }}</h4>
              <ul>
                <li v-for="suggestion in rec.suggestions" :key="suggestion">{{ suggestion }}</li>
              </ul>
            </div>
          </div>
          <div v-else class="no-recommendations">
            <p>您的健康状况良好，请继续保持健康的生活方式！</p>
          </div>
        </div>
      </el-card>

      <!-- Predictions -->
      <el-card class="report-section">
        <template #header>
          <h3>未来7天预测</h3>
        </template>
        <div class="predictions-content">
          <div v-if="reportData.predictions" class="prediction-grid">
            <div class="prediction-item">
              <h4>体重预测</h4>
              <p>当前: {{ reportData.predictions.weight?.current?.toFixed(1) }} kg</p>
              <p>预测: {{ reportData.predictions.weight?.predicted?.[6]?.toFixed(1) }} kg</p>
              <p>趋势: {{ reportData.predictions.weight?.trend }}</p>
            </div>
            <div class="prediction-item">
              <h4>血压预测</h4>
              <p>当前: {{ reportData.predictions.blood_pressure?.current?.systolic }}/{{ reportData.predictions.blood_pressure?.current?.diastolic }} mmHg</p>
              <p>预测: {{ reportData.predictions.blood_pressure?.predicted?.systolic?.[6] }}/{{ reportData.predictions.blood_pressure?.predicted?.diastolic?.[6] }} mmHg</p>
              <p>趋势: {{ reportData.predictions.blood_pressure?.trend }}</p>
            </div>
            <div class="prediction-item">
              <h4>心率预测</h4>
              <p>当前: {{ reportData.predictions.heart_rate?.current }} bpm</p>
              <p>预测: {{ reportData.predictions.heart_rate?.predicted?.[6] }} bpm</p>
              <p>趋势: {{ reportData.predictions.heart_rate?.trend }}</p>
            </div>
            <div class="prediction-item">
              <h4>血糖预测</h4>
              <p>当前: {{ reportData.predictions.blood_glucose?.current?.toFixed(1) }} mmol/L</p>
              <p>预测: {{ reportData.predictions.blood_glucose?.predicted?.[6]?.toFixed(1) }} mmol/L</p>
              <p>趋势: {{ reportData.predictions.blood_glucose?.trend }}</p>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <el-empty description="暂无健康报告数据">
        <el-button type="primary" @click="generateReport">生成健康报告</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../utils/axios.js'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const reportData = ref(null)

const formatDate = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleDateString('zh-CN')
}

const generateReport = async () => {
  loading.value = true
  try {
    console.log('开始生成健康报告...')
    
    // 获取统计数据
    const statsResponse = await api.get('/measurements/statistics/')
    console.log('统计数据:', statsResponse.data)
    
    // 获取预测数据
    const predictResponse = await api.get('/measurements/predict/', {
      params: { days: 7 }
    })
    console.log('预测数据:', predictResponse.data)
    
    // 获取建议数据
    const recommendationsResponse = await api.get('/measurements/recommendations/')
    console.log('建议数据:', recommendationsResponse.data)
    
    // 生成趋势分析
    const trends = generateTrends(statsResponse.data)
    
    // 计算总体健康评级
    const overallHealthRating = calculateHealthRating(statsResponse.data, predictResponse.data)
    
    reportData.value = {
      user_info: {
        username: '用户', // 这里应该从用户API获取
        email: 'user@example.com'
      },
      date_range: statsResponse.data.date_range,
      total_measurements: statsResponse.data.total_measurements,
      overall_health_rating,
      statistics: statsResponse.data,
      trends,
      risk_assessment: predictResponse.data.risk_assessment,
      predictions: predictResponse.data,
      recommendations: recommendationsResponse.data.recommendations
    }
    
    console.log('报告数据生成完成:', reportData.value)
    ElMessage.success('健康报告生成成功！')
  } catch (error) {
    console.error('生成报告失败:', error)
    ElMessage.error('生成报告失败：' + (error.response?.data?.error || error.message))
  } finally {
    loading.value = false
  }
}

const generateTrends = (stats) => {
  const trends = []
  
  // 体重趋势
  if (stats.weight) {
    const weightChange = ((stats.weight.latest - stats.weight.average) / stats.weight.average * 100).toFixed(2)
    trends.push({
      metric: 'weight',
      trend: weightChange > 0 ? '上升' : weightChange < 0 ? '下降' : '稳定',
      change_rate: parseFloat(weightChange),
      analysis: weightChange > 5 ? '体重有明显上升趋势，建议控制饮食' : weightChange < -5 ? '体重有明显下降趋势，注意营养均衡' : '体重保持稳定'
    })
  }
  
  // 血压趋势
  if (stats.blood_pressure) {
    const systolicChange = ((stats.blood_pressure.latest_systolic - stats.blood_pressure.avg_systolic) / stats.blood_pressure.avg_systolic * 100).toFixed(2)
    trends.push({
      metric: 'blood_pressure',
      trend: systolicChange > 0 ? '上升' : systolicChange < 0 ? '下降' : '稳定',
      change_rate: parseFloat(systolicChange),
      analysis: systolicChange > 10 ? '血压有明显上升趋势，建议咨询医生' : systolicChange < -10 ? '血压有明显下降趋势，注意监测' : '血压保持稳定'
    })
  }
  
  // 心率趋势
  if (stats.heart_rate) {
    const heartRateChange = ((stats.heart_rate.latest - stats.heart_rate.average) / stats.heart_rate.average * 100).toFixed(2)
    trends.push({
      metric: 'heart_rate',
      trend: heartRateChange > 0 ? '上升' : heartRateChange < 0 ? '下降' : '稳定',
      change_rate: parseFloat(heartRateChange),
      analysis: heartRateChange > 15 ? '心率有明显上升趋势，建议减少压力' : heartRateChange < -15 ? '心率有明显下降趋势，如有不适请咨询医生' : '心率保持稳定'
    })
  }
  
  // 血糖趋势
  if (stats.blood_glucose) {
    const glucoseChange = ((stats.blood_glucose.latest - stats.blood_glucose.average) / stats.blood_glucose.average * 100).toFixed(2)
    trends.push({
      metric: 'blood_glucose',
      trend: glucoseChange > 0 ? '上升' : glucoseChange < 0 ? '下降' : '稳定',
      change_rate: parseFloat(glucoseChange),
      analysis: glucoseChange > 10 ? '血糖有明显上升趋势，建议控制糖分摄入' : glucoseChange < -10 ? '血糖有明显下降趋势，注意监测' : '血糖保持稳定'
    })
  }
  
  return trends
}

const calculateHealthRating = (stats, predictions) => {
  let score = 100
  
  // 根据各项指标扣分
  if (stats.blood_pressure?.latest_systolic > 140 || stats.blood_pressure?.latest_diastolic > 90) {
    score -= 20
  } else if (stats.blood_pressure?.latest_systolic > 130 || stats.blood_pressure?.latest_diastolic > 85) {
    score -= 10
  }
  
  if (stats.blood_glucose?.latest > 7.0) {
    score -= 20
  } else if (stats.blood_glucose?.latest > 6.1) {
    score -= 10
  }
  
  if (stats.heart_rate?.latest > 100 || stats.heart_rate?.latest < 60) {
    score -= 10
  }
  
  if (predictions.risk_assessment?.overall_risk === 'high') {
    score -= 15
  } else if (predictions.risk_assessment?.overall_risk === 'medium') {
    score -= 5
  }
  
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '一般'
  if (score >= 60) return '需改善'
  return '需关注'
}

const getHealthRatingType = (rating) => {
  const types = {
    '优秀': 'success',
    '良好': 'success',
    '一般': 'warning',
    '需改善': 'warning',
    '需关注': 'danger'
  }
  return types[rating] || 'info'
}

const getWeightStatus = (weight) => {
  if (!weight) return 'info'
  if (weight > 90) return 'danger'
  if (weight > 80) return 'warning'
  return 'success'
}

const getWeightStatusText = (weight) => {
  if (!weight) return '未知'
  if (weight > 90) return '超重'
  if (weight > 80) return '偏重'
  return '正常'
}

const getBloodPressureStatus = (systolic, diastolic) => {
  if (!systolic || !diastolic) return 'info'
  if (systolic > 140 || diastolic > 90) return 'danger'
  if (systolic > 130 || diastolic > 85) return 'warning'
  return 'success'
}

const getBloodPressureStatusText = (systolic, diastolic) => {
  if (!systolic || !diastolic) return '未知'
  if (systolic > 140 || diastolic > 90) return '高血压'
  if (systolic > 130 || diastolic > 85) return '血压偏高'
  return '正常'
}

const getHeartRateStatus = (heartRate) => {
  if (!heartRate) return 'info'
  if (heartRate > 100 || heartRate < 60) return 'warning'
  return 'success'
}

const getHeartRateStatusText = (heartRate) => {
  if (!heartRate) return '未知'
  if (heartRate > 100) return '心率偏快'
  if (heartRate < 60) return '心率偏慢'
  return '正常'
}

const getGlucoseStatus = (glucose) => {
  if (!glucose) return 'info'
  if (glucose > 7.0) return 'danger'
  if (glucose > 6.1) return 'warning'
  return 'success'
}

const getGlucoseStatusText = (glucose) => {
  if (!glucose) return '未知'
  if (glucose > 7.0) return '血糖偏高'
  if (glucose > 6.1) return '血糖略高'
  return '正常'
}

const getRiskPercentage = (risk) => {
  const percentages = {
    'low': 20,
    'medium': 50,
    'high': 80
  }
  return percentages[risk] || 0
}

const getRiskStatus = (risk) => {
  const statuses = {
    'low': 'success',
    'medium': 'warning',
    'high': 'exception'
  }
  return statuses[risk] || 'info'
}

const getMetricName = (metric) => {
  const names = {
    'weight': '体重',
    'blood_pressure': '血压',
    'heart_rate': '心率',
    'blood_glucose': '血糖'
  }
  return names[metric] || metric
}

onMounted(() => {
  // 自动生成报告
  generateReport()
})
</script>

<style scoped>
.health-report {
  padding: 20px;
  max-width: 1200px;
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

.title-section h2 {
  margin: 0 0 5px 0;
  color: #303133;
}

.title-section p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 10px;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.report-section {
  margin-bottom: 20px;
}

.report-section h3 {
  margin: 0;
  color: #303133;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item label {
  font-weight: bold;
  color: #606266;
}

.stats-table {
  overflow-x: auto;
}

.stats-table table {
  width: 100%;
  border-collapse: collapse;
}

.stats-table th,
.stats-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #EBEEF5;
}

.stats-table th {
  background-color: #F5F7FA;
  font-weight: bold;
  color: #303133;
}

.trends-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.trend-item {
  padding: 15px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}

.trend-item h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.trend-item p {
  margin: 5px 0;
  color: #606266;
}

.risk-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.overall-risk {
  text-align: center;
}

.overall-risk h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.risk-list h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.risk-item {
  margin-bottom: 10px;
}

.recommendations-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.recommendation-category h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.recommendation-category ul {
  margin: 0;
  padding-left: 20px;
}

.recommendation-category li {
  margin-bottom: 5px;
  color: #606266;
}

.no-recommendations {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.predictions-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.prediction-item {
  padding: 15px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  text-align: center;
}

.prediction-item h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.prediction-item p {
  margin: 5px 0;
  color: #606266;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .actions {
    flex-direction: column;
    width: 100%;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .trends-content {
    grid-template-columns: 1fr;
  }

  .predictions-content {
    grid-template-columns: 1fr;
  }

  .stats-table {
    font-size: 14px;
  }

  .stats-table th,
  .stats-table td {
    padding: 8px;
  }
}
</style>

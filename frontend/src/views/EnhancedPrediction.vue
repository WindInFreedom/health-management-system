<template>
  <div class="enhanced-prediction">
    <el-card class="header-card" shadow="never">
      <h1>智能健康预测</h1>
      <p>基于深度学习的健康指标预测与风险评估</p>
    </el-card>

    <!-- 控制面板 -->
    <el-card class="control-panel" shadow="hover">
      <el-form :inline="true" :model="formData" label-width="80px">
        <el-form-item label="指标">
          <el-select v-model="formData.metric" placeholder="选择指标" style="width: 150px">
            <el-option label="血糖" value="blood_glucose" />
            <el-option label="心率" value="heart_rate" />
            <el-option label="收缩压" value="systolic" />
            <el-option label="舒张压" value="diastolic" />
            <el-option label="体重" value="weight_kg" />
          </el-select>
        </el-form-item>

        <el-form-item label="预测天数">
          <el-select v-model="formData.days" placeholder="选择天数" style="width: 120px">
            <el-option label="7天" :value="7" />
            <el-option label="14天" :value="14" />
            <el-option label="30天" :value="30" />
          </el-select>
        </el-form-item>

        <el-form-item label="模型">
          <el-select v-model="formData.modelType" placeholder="选择模型" style="width: 150px">
            <el-option label="LSTM" value="lstm" />
            <el-option label="Transformer" value="transformer" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handlePredict" :loading="loading">
            开始预测
          </el-button>
          <el-button @click="handleTrain" :loading="trainingLoading">
            训练模型
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 主要内容区 -->
    <div v-if="predictionData" class="content-grid">
      <!-- 趋势图 -->
      <el-card class="chart-card" shadow="hover">
        <AdvancedTrendChart
          :historical-data="historicalData"
          :predictions="predictionData.predictions"
          :confidence-interval="predictionData.confidence_interval"
          :historical-backtest="predictionData.historical_backtest"
          :future-dates="predictionData.future_dates"
          :metric="formData.metric"
          :threshold-line="getThresholdLine(formData.metric)"
        />
      </el-card>

      <!-- 模型指标卡片 -->
      <el-card class="metrics-card" shadow="hover">
        <ModelMetricsCard
          v-if="predictionData.metrics"
          :metrics="predictionData.metrics"
          :show-details="true"
        />
      </el-card>

      <!-- 风险评估面板 -->
      <el-card class="risk-card" shadow="hover" v-if="riskData">
        <template #header>
          <span style="font-weight: bold">风险评估</span>
        </template>
        <el-result
          :icon="getRiskIcon(riskData.risk_level)"
          :title="riskData.risk_level"
          :sub-title="`风险评分: ${(riskData.risk_score * 100).toFixed(0)}%`"
        >
          <template #extra>
            <div class="risk-factors">
              <h4>主要风险因素</h4>
              <el-tag
                v-for="(factor, index) in riskData.key_factors"
                :key="index"
                :type="getFactorType(factor.importance)"
                style="margin: 4px"
              >
                {{ factor.description }}
              </el-tag>
            </div>
          </template>
        </el-result>
      </el-card>

      <!-- 雷达图 -->
      <el-card class="radar-card" shadow="hover">
        <RadarHealthScore :scores="radarScores" />
      </el-card>

      <!-- AI 建议面板 -->
      <el-card class="advice-card" shadow="hover" v-if="aiAdvice">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-weight: bold">🤖 AI 健康建议</span>
            <el-tag :type="aiAdvice.source === 'api' ? 'success' : 'info'" size="small">
              {{ aiAdvice.source === 'api' ? 'AI生成' : '智能建议' }}
            </el-tag>
          </div>
        </template>

        <div class="advice-content">
          <h3>健康状况分析</h3>
          <p>{{ aiAdvice.analysis }}</p>

          <h3>具体建议</h3>
          <ul>
            <li v-for="(rec, index) in aiAdvice.recommendations" :key="index">
              {{ rec }}
            </li>
          </ul>

          <h3>生活方式计划</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="饮食">{{ aiAdvice.lifestyle_plan?.diet }}</el-descriptions-item>
            <el-descriptions-item label="运动">{{ aiAdvice.lifestyle_plan?.exercise }}</el-descriptions-item>
            <el-descriptions-item label="作息">{{ aiAdvice.lifestyle_plan?.sleep }}</el-descriptions-item>
          </el-descriptions>

          <h3>就医建议</h3>
          <el-alert
            :title="aiAdvice.medical_advice"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="请选择指标并点击「开始预测」" :image-size="200" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AdvancedTrendChart from '@/components/charts/AdvancedTrendChart.vue'
import ModelMetricsCard from '@/components/charts/ModelMetricsCard.vue'
import RadarHealthScore from '@/components/charts/RadarHealthScore.vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8001/api/v2'

const formData = ref({
  metric: 'blood_glucose',
  days: 7,
  modelType: 'lstm'
})

const loading = ref(false)
const trainingLoading = ref(false)
const predictionData = ref(null)
const riskData = ref(null)
const aiAdvice = ref(null)
const historicalData = ref([])

const radarScores = computed(() => ({
  blood_glucose: 80,
  heart_rate: 85,
  systolic: 75,
  diastolic: 80,
  weight_kg: 90
}))

const getThresholdLine = (metric) => {
  const thresholds = {
    blood_glucose: 6.1,
    heart_rate: 100,
    systolic: 120,
    diastolic: 80,
    weight_kg: null
  }
  return thresholds[metric]
}

const getRiskIcon = (level) => {
  if (level === '低风险') return 'success'
  if (level === '中风险') return 'warning'
  return 'error'
}

const getFactorType = (importance) => {
  if (importance > 0.3) return 'danger'
  if (importance > 0.2) return 'warning'
  return 'info'
}

const handlePredict = async () => {
  loading.value = true
  try {
    const response = await axios.post(`${API_BASE}/predict`, {
      user_id: 1, // 从登录状态获取
      metric: formData.value.metric,
      days: formData.value.days,
      model_type: formData.value.modelType,
      confidence_level: 0.95
    })

    if (response.data.success) {
      predictionData.value = response.data
      ElMessage.success('预测完成！')
      
      // 同时获取风险评估
      await getRiskAssessment()
      
      // 获取 AI 建议
      await getAIAdvice()
    } else {
      ElMessage.error('预测失败，请先训练模型')
    }
  } catch (error) {
    console.error('Prediction error:', error)
    ElMessage.error(error.response?.data?.detail || '预测失败')
  } finally {
    loading.value = false
  }
}

const handleTrain = async () => {
  trainingLoading.value = true
  try {
    const response = await axios.post(`${API_BASE}/train`, {
      user_id: 1,
      metric: formData.value.metric,
      model_type: formData.value.modelType,
      epochs: 100,
      batch_size: 32,
      seq_length: 14
    })

    if (response.data.success) {
      ElMessage.success(response.data.message)
    }
  } catch (error) {
    console.error('Training error:', error)
    ElMessage.error(error.response?.data?.detail || '训练失败')
  } finally {
    trainingLoading.value = false
  }
}

const getRiskAssessment = async () => {
  try {
    const response = await axios.post(`${API_BASE}/risk-assessment`, {
      user_id: 1,
      metrics: ['blood_glucose', 'heart_rate', 'systolic', 'diastolic', 'weight_kg'],
      time_window: 30
    })

    if (response.data.success) {
      riskData.value = response.data
    }
  } catch (error) {
    console.error('Risk assessment error:', error)
  }
}

const getAIAdvice = async () => {
  try {
    const response = await axios.post(`${API_BASE}/ai-advice`, {
      user_id: 1,
      user_profile: {
        age: 35,
        gender: 'M',
        height_cm: 175,
        weight_kg: 78,
        conditions: []
      },
      recent_data: {
        blood_glucose: [5.6, 5.8, 6.1, 5.9],
        heart_rate: [72, 75, 78, 76],
        systolic: [135, 138, 140, 136],
        diastolic: [85, 87, 90, 86]
      },
      risk_assessment: riskData.value
    })

    if (response.data.success) {
      aiAdvice.value = response.data
    }
  } catch (error) {
    console.error('AI advice error:', error)
  }
}

onMounted(() => {
  // 可以在这里加载初始数据
})
</script>

<style scoped>
.enhanced-prediction {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
  text-align: center;
}

.header-card h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #303133;
}

.header-card p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.control-panel {
  margin-bottom: 20px;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-card {
  grid-column: 1 / -1;
}

.advice-card {
  grid-column: 1 / -1;
}

.advice-content h3 {
  font-size: 16px;
  margin: 16px 0 8px 0;
  color: #303133;
}

.advice-content p {
  line-height: 1.6;
  color: #606266;
  margin-bottom: 16px;
}

.advice-content ul {
  padding-left: 20px;
  margin-bottom: 16px;
}

.advice-content li {
  line-height: 1.8;
  color: #606266;
}

.risk-factors h4 {
  font-size: 14px;
  margin-bottom: 8px;
  color: #606266;
}

@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-card,
  .advice-card {
    grid-column: 1;
  }
}
</style>

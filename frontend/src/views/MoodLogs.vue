<template>
  <div class="mood-logs-container">
    <!-- Data Processing Card -->
    <el-card class="data-processing-card">
      <template #header>
        <div class="card-header">
          <span>数据处理</span>
          <el-button type="info" @click="handleValidateData" :loading="validating">
            <el-icon><CircleCheck /></el-icon>
            验证数据
          </el-button>
        </div>
      </template>

      <div class="data-processing-sections">
        <div class="data-processing-section">
          <h4 class="section-title">数据预处理</h4>
          <el-button type="primary" @click="handlePreprocessData" :loading="preprocessing">
            <el-icon><DataAnalysis /></el-icon>
            数据预处理
          </el-button>
        </div>

        <div class="data-processing-section">
          <h4 class="section-title">数据清洗</h4>
          <el-button type="danger" @click="handleCleanAllData" :loading="cleaningAll">
            <el-icon><Delete /></el-icon>
            一键清洗
          </el-button>
        </div>

        <div class="data-processing-section">
          <h4 class="section-title">模型训练</h4>
          <el-button type="success" @click="handleTrainModel" :loading="trainingModel">
            <el-icon><DataAnalysis /></el-icon>
            训练GRU模型
          </el-button>
        </div>

        <div class="data-processing-section">
          <h4 class="section-title">单独操作</h4>
          <div class="data-processing-buttons">
            <el-button type="primary" @click="handleCleanData" :loading="cleaning">
              <el-icon><Delete /></el-icon>
              清洗无效数据
            </el-button>
            <el-button type="warning" @click="handleRemoveDuplicates" :loading="removingDuplicates">
              <el-icon><DocumentCopy /></el-icon>
              删除重复记录
            </el-button>
            <el-button type="success" @click="handleFixMissingValues" :loading="fixing">
              <el-icon><Edit /></el-icon>
              修复缺失值
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="operationResults.length > 0" class="operation-results">
        <div v-for="(result, index) in operationResults" :key="index" class="result-item">
          <el-alert
            :title="result.message"
            :type="result.type"
            :closable="false"
            show-icon
          >
            <div v-if="result.details && result.details.length > 0" class="result-details">
              <el-scrollbar max-height="150px">
                <ul>
                  <li v-for="(detail, idx) in result.details" :key="idx">
                    {{ detail }}
                  </li>
                </ul>
              </el-scrollbar>
            </div>
          </el-alert>
        </div>
      </div>

      <div v-if="preprocessingResults" class="preprocessing-results">
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="数据分析" name="analysis">
            <div v-if="preprocessingResults.analysis">
              <p><strong>总记录数:</strong> {{ preprocessingResults.analysis.total_records }}</p>
              <el-row :gutter="20">
                <el-col :span="24">
                  <p><strong>心情评分:</strong> {{ preprocessingResults.analysis.rating?.min }} - {{ preprocessingResults.analysis.rating?.max }} (平均: {{ preprocessingResults.analysis.rating?.avg }})</p>
                </el-col>
              </el-row>
            </div>
          </el-collapse-item>
          <el-collapse-item title="异常检测" name="anomalies">
            <div v-if="preprocessingResults.anomalies && preprocessingResults.anomalies.length > 0">
              <el-table :data="preprocessingResults.anomalies" max-height="200">
                <el-table-column prop="type" label="类型" width="100" />
                <el-table-column prop="value" label="值" width="150" />
                <el-table-column prop="time" label="时间" />
              </el-table>
            </div>
            <div v-else>
              <el-empty description="未发现异常值" />
            </div>
          </el-collapse-item>
          <el-collapse-item title="健康评分" name="health_scores">
            <div v-if="preprocessingResults.health_scores">
              <p><strong>综合评分:</strong> {{ preprocessingResults.health_scores.overall_score }}/100</p>
              <el-row :gutter="20">
                <el-col :span="24" v-for="(score, idx) in preprocessingResults.health_scores.individual_scores" :key="idx">
                  <el-card>
                    <div class="score-item">
                      <div class="score-name">{{ score.name }}</div>
                      <div class="score-value">{{ score.score }}</div>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <div v-if="validationResults" class="validation-results">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="validation-item passed">
              <div class="validation-count">{{ validationResults.passed }}</div>
              <div class="validation-label">通过</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="validation-item failed">
              <div class="validation-count">{{ validationResults.failed }}</div>
              <div class="validation-label">失败</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="validation-item warning">
              <div class="validation-count">{{ validationResults.warnings }}</div>
              <div class="validation-label">警告</div>
            </div>
          </el-col>
        </el-row>
        <div v-if="validationResults.details && validationResults.details.length > 0" class="validation-details">
          <el-scrollbar max-height="200px">
            <ul>
              <li v-for="(detail, idx) in validationResults.details" :key="idx" :class="getDetailClass(detail)">
                {{ detail }}
              </li>
            </ul>
          </el-scrollbar>
        </div>
      </div>

      <div v-if="modelMetrics" class="model-metrics">
        <h4 class="metrics-title">模型准确度指标</h4>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="metric-card">
              <div class="metric-value">{{ modelMetrics.MAE.toFixed(4) }}</div>
              <div class="metric-label">MAE (平均绝对误差)</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card">
              <div class="metric-value">{{ modelMetrics.RMSE.toFixed(4) }}</div>
              <div class="metric-label">RMSE (均方根误差)</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card">
              <div class="metric-value">{{ modelMetrics.R2.toFixed(4) }}</div>
              <div class="metric-label">R2 (决定系数)</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card">
              <div class="metric-value">{{ modelMetrics.MAPE.toFixed(2) }}%</div>
              <div class="metric-label">MAPE (平均绝对百分比误差)</div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <el-card class="main-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h2 class="page-title">情绪日志</h2>
          <div class="header-actions">
            <el-button type="info" @click="fetchMoodLogs" :loading="loading">
              <el-icon><Refresh /></el-icon>
              拉取数据
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              添加记录
            </el-button>
          </div>
        </div>
      </template>

      <div class="content">
        <!-- No Data Section -->
        <div v-if="!hasData" class="no-data-section">
          <el-empty description="No Data" />
        </div>

        <!-- Chart Section -->
        <div v-else class="chart-section">
          <div class="chart-header">
            <h3 class="section-title">情绪趋势</h3>
            <div class="chart-controls">
              <el-checkbox v-model="showPrediction" @change="togglePrediction">显示预测</el-checkbox>
              <el-input-number
                v-model="predictionHorizon"
                :min="1"
                :max="30"
                size="small"
                @change="loadPrediction"
              />
            </div>
          </div>
          <div ref="chartRef" class="chart-container"></div>
        </div>

        <!-- Cards Section -->
        <div v-if="hasData" class="cards-section">
          <div class="mood-cards">
            <el-card
              v-for="log in moodLogs"
              :key="log.id"
              class="mood-card"
              shadow="hover"
            >
              <div class="mood-card-header">
                <div class="mood-date">
                  <el-icon class="date-icon"><Calendar /></el-icon>
                  {{ log.log_date }}
                </div>
                <div class="mood-actions">
                  <el-button size="small" text @click="showEditDialog(log)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button size="small" text type="danger" @click="deleteMoodLog(log.id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              
              <div class="mood-rating">
                <div class="rating-label">心情指数</div>
                <div class="rating-value" :class="getMoodClass(log.mood_rating)">
                  {{ log.mood_rating }}/10
                </div>
                <el-progress
                  :percentage="log.mood_rating * 10"
                  :color="getMoodColor(log.mood_rating)"
                  :show-text="false"
                />
              </div>
              
              <div class="mood-notes" v-if="log.notes">
                <div class="notes-label">备注:</div>
                <div class="notes-content">{{ log.notes }}</div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '添加情绪记录' : '编辑情绪记录'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="日期" prop="log_date">
          <el-date-picker
            v-model="form.log_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="心情指数" prop="mood_rating">
          <div class="mood-rating-input">
            <el-slider
              v-model="form.mood_rating"
              :min="1"
              :max="10"
              :marks="{ 1: '1', 5: '5', 10: '10' }"
              show-stops
              style="width: 100%"
            />
            <div class="mood-rating-display" :class="getMoodClass(form.mood_rating)">
              {{ form.mood_rating }}/10 - {{ getMoodText(form.mood_rating) }}
            </div>
          </div>
        </el-form-item>

        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="4"
            placeholder="记录今天的心情和想法..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Calendar, Edit, Delete, Refresh, DataAnalysis, CircleCheck, DocumentCopy } from '@element-plus/icons-vue'
import api from '../utils/axios.js'
import * as echarts from 'echarts'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('add')
const formRef = ref(null)
const chartRef = ref(null)
const moodLogs = ref([])
const currentId = ref(null)
const hasData = ref(false)
const preprocessing = ref(false)
const cleaningAll = ref(false)
const cleaning = ref(false)
const removingDuplicates = ref(false)
const fixing = ref(false)
const validating = ref(false)
const activeCollapse = ref(['analysis', 'anomalies', 'health_scores'])
const operationResults = ref([])
const preprocessingResults = ref(null)
const validationResults = ref(null)
const showPrediction = ref(false)
const predictionHorizon = ref(7)
const predictionData = ref(null)
const modelMetrics = ref(null)
const trainingModel = ref(false)
let chartInstance = null

const form = reactive({
  log_date: '',
  mood_rating: 5,
  notes: ''
})

const rules = {
  log_date: [
    { required: true, message: '请选择日期', trigger: 'change' }
  ],
  mood_rating: [
    { required: true, type: 'number', message: '请评分心情指数', trigger: 'change' }
  ]
}

const getMoodColor = (rating) => {
  if (rating >= 8) return '#67c23a'
  if (rating >= 6) return '#409eff'
  if (rating >= 4) return '#e6a23c'
  return '#f56c6c'
}

const getMoodClass = (rating) => {
  if (rating >= 8) return 'mood-great'
  if (rating >= 6) return 'mood-good'
  if (rating >= 4) return 'mood-okay'
  return 'mood-bad'
}

const getMoodText = (rating) => {
  if (rating >= 9) return '非常开心'
  if (rating >= 7) return '心情不错'
  if (rating >= 5) return '还可以'
  if (rating >= 3) return '有点低落'
  return '很不好'
}

const fetchMoodLogs = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/mood-logs/')
    moodLogs.value = (data.results || data || []).sort((a, b) => 
      new Date(b.log_date) - new Date(a.log_date)
    )
    hasData.value = moodLogs.value.length > 0
    await nextTick()
    renderChart()
  } catch (error) {
    ElMessage.error('获取情绪记录失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value || moodLogs.value.length === 0) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)

  const sortedData = [...moodLogs.value].sort((a, b) => 
    new Date(a.log_date) - new Date(b.log_date)
  ).slice(-30) // Last 30 days

  const dates = sortedData.map(item => item.log_date)
  const ratings = sortedData.map(item => item.mood_rating)

  const series = [
    {
      data: ratings,
      type: 'line',
      smooth: true,
      itemStyle: {
        color: '#667eea'
      },
      lineStyle: {
        width: 3
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.5)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.1)' }
        ])
      },
      markLine: {
        silent: true,
        lineStyle: {
          color: '#999',
          type: 'dashed'
        },
        data: [
          { yAxis: 5, label: { formatter: '中性' } }
        ]
      }
    }
  ]

  let allDates = [...dates]
  if (showPrediction.value && predictionData.value?.dates && predictionData.value?.values) {
    allDates = [...allDates, ...predictionData.value.dates]
    series.push({
      data: [...Array(dates.length).fill(null), ...predictionData.value.values],
      type: 'line',
      smooth: true,
      itemStyle: {
        color: '#E6A23C'
      },
      lineStyle: {
        type: 'dashed',
        width: 3
      }
    })
  }

  const option = {
    title: {
      text: '近期情绪趋势',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const value = params[0].value
        return `${params[0].name}<br/>心情指数: ${value}/10`
      }
    },
    xAxis: {
      type: 'category',
      data: allDates,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(allDates.length / 10) || 0
      }
    },
    yAxis: {
      type: 'value',
      name: '心情指数',
      min: 0,
      max: 10
    },
    series,
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '15%'
    }
  }

  chartInstance.setOption(option)

  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
}

const showAddDialog = () => {
  dialogMode.value = 'add'
  dialogVisible.value = true
  resetForm()
}

const showEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentId.value = row.id
  form.log_date = row.log_date
  form.mood_rating = row.mood_rating
  form.notes = row.notes
  dialogVisible.value = true
}

const resetForm = () => {
  form.log_date = ''
  form.mood_rating = 5
  form.notes = ''
  currentId.value = null
  formRef.value?.clearValidate()
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    const moodData = {
      log_date: form.log_date,
      mood_rating: form.mood_rating,
      notes: form.notes
    }

    if (dialogMode.value === 'add') {
      await api.post('/mood-logs/', moodData)
      ElMessage.success('添加成功')
    } else {
      await api.put(`/mood-logs/${currentId.value}/`, moodData)
      ElMessage.success('更新成功')
    }

    dialogVisible.value = false
    await fetchMoodLogs()
  } catch (error) {
    if (error.response) {
      const errorMsg = error.response?.data?.detail || 
                      error.response?.data?.log_date?.[0] || 
                      JSON.stringify(error.response?.data)
      ElMessage.error('操作失败: ' + errorMsg)
    }
  } finally {
    submitting.value = false
  }
}

const deleteMoodLog = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条情绪记录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    await api.delete(`/mood-logs/${id}/`)
    ElMessage.success('删除成功')
    await fetchMoodLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    loading.value = false
  }
}

const API_BASE = '/api'

// 数据预处理
async function handlePreprocessData() {
  try {
    await ElMessageBox.confirm(
      '确定要进行数据预处理吗？此操作将分析心情数据并检测异常。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    preprocessing.value = true
    const response = await fetch(`${API_BASE}/mood-data-processing/preprocess_mood_data/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    const data = await response.json()
    
    preprocessingResults.value = data.results
    operationResults.value.unshift({
      message: data.message,
      type: data.anomalies_count > 0 ? 'warning' : 'success',
      details: []
    })
    
    if (data.anomalies_count > 0) {
      ElMessage.warning(`预处理完成，发现 ${data.anomalies_count} 个异常值`)
    } else {
      ElMessage.success('预处理完成，数据质量良好')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('数据预处理失败')
    }
  } finally {
    preprocessing.value = false
  }
}

// 训练GRU模型
async function handleTrainModel() {
  try {
    await ElMessageBox.confirm(
      '确定要训练GRU模型吗？此操作将使用历史心情数据训练预测模型，可能需要几分钟时间。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    trainingModel.value = true
    const { data } = await api.post('/gru-model/train/', {
      metrics: ['mood_rating']
    })
    
    ElMessage.success('模型训练完成')
    
    operationResults.value.unshift({
      message: '心情模型训练完成',
      type: 'success',
      details: []
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('模型训练失败：' + (error.response?.data?.error || error.message))
    }
  } finally {
    trainingModel.value = false
  }
}

// 加载预测
async function loadPrediction() {
  if (!showPrediction.value) return
  try {
    const { data } = await api.post('/gru-model/predict/', {
      metric: 'mood_rating',
      days: predictionHorizon.value
    })
    predictionData.value = {
      dates: data.predictions.map((_, i) => `预测第${i+1}天`),
      values: data.predictions
    }
    modelMetrics.value = data.metrics
    await nextTick()
    renderChart()
  } catch (error) {
    predictionData.value = null
    modelMetrics.value = null
    console.warn('预测数据获取失败：', error)
    ElMessage.error('预测失败：' + (error.response?.data?.error || error.message))
  }
}

function togglePrediction() {
  if (showPrediction.value) {
    loadPrediction()
  } else {
    predictionData.value = null
    renderChart()
  }
}

// 一键清洗
async function handleCleanAllData() {
  try {
    await ElMessageBox.confirm(
      '确定要进行一键清洗吗？此操作将清洗无效心情数据、删除重复记录并修复缺失值。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleaningAll.value = true
    const response = await fetch(`${API_BASE}/mood-data-processing/clean_all_mood_data/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await fetchMoodLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('一键清洗失败')
    }
  } finally {
    cleaningAll.value = false
  }
}

// 清洗无效数据
async function handleCleanData() {
  try {
    await ElMessageBox.confirm(
      '确定要清洗无效数据吗？此操作将删除超出正常范围的心情数据。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleaning.value = true
    const response = await fetch(`${API_BASE}/data-processing/clean_invalid_data/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ action: 'mood' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await fetchMoodLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清洗数据失败')
    }
  } finally {
    cleaning.value = false
  }
}

// 删除重复记录
async function handleRemoveDuplicates() {
  try {
    await ElMessageBox.confirm(
      '确定要删除重复记录吗？',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    removingDuplicates.value = true
    const response = await fetch(`${API_BASE}/data-processing/remove_duplicates/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ type: 'mood' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await fetchMoodLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除重复记录失败')
    }
  } finally {
    removingDuplicates.value = false
  }
}

// 修复缺失值
async function handleFixMissingValues() {
  try {
    await ElMessageBox.confirm(
      '确定要修复缺失值吗？此操作将使用最近的非空值填充缺失数据。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    fixing.value = true
    const response = await fetch(`${API_BASE}/data-processing/fix_missing_values/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ type: 'mood' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await fetchMoodLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('修复缺失值失败')
    }
  } finally {
    fixing.value = false
  }
}

// 验证数据质量
async function handleValidateData() {
  validating.value = true
  try {
    const response = await fetch(`${API_BASE}/mood-data-processing/validate_mood_data/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    const data = await response.json()
    validationResults.value = data
    
    if (data.failed > 0) {
      ElMessage.warning(`验证完成：发现 ${data.failed} 个问题`)
    } else {
      ElMessage.success('验证完成：数据质量良好')
    }
  } catch (error) {
    ElMessage.error('验证数据失败')
  } finally {
    validating.value = false
  }
}

function getDetailClass(detail) {
  if (detail.includes('✓')) return 'passed'
  if (detail.includes('✗')) return 'failed'
  return 'warning'
}

onMounted(() => {
  fetchMoodLogs()
})
</script>

<style scoped>
.mood-logs-container {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.main-card {
  max-width: 1400px;
  margin: 0 auto;
  border-radius: 15px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.content {
  padding: 10px 0;
}

.no-data-section {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  margin: 10px 0 20px;
  color: #333;
}

.chart-container {
  width: 100%;
  height: 350px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.chart-controls {
  display: flex;
  gap: 15px;
  align-items: center;
}

.model-metrics {
  margin-top: 20px;
}

.metrics-title {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.metric-card {
  text-align: center;
  padding: 15px;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  color: #667eea;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 14px;
  color: #606266;
}

.cards-section {
  margin-top: 20px;
}

.mood-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.mood-card {
  border-radius: 12px;
  transition: transform 0.3s;
}

.mood-card:hover {
  transform: translateY(-5px);
}

.mood-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.mood-date {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.date-icon {
  color: #667eea;
  font-size: 18px;
}

.mood-actions {
  display: flex;
  gap: 5px;
}

.mood-rating {
  margin-bottom: 15px;
}

.rating-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.rating-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 10px;
}

.mood-great {
  color: #67c23a;
}

.mood-good {
  color: #409eff;
}

.mood-okay {
  color: #e6a23c;
}

.mood-bad {
  color: #f56c6c;
}

.mood-notes {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  margin-top: 10px;
}

.notes-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 5px;
}

.notes-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}

.mood-rating-input {
  width: 100%;
}

.mood-rating-display {
  margin-top: 15px;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  padding: 10px;
  border-radius: 8px;
  background: #f5f7fa;
}

:deep(.el-dialog) {
  border-radius: 15px;
}

:deep(.el-progress__text) {
  display: none;
}

@media (max-width: 768px) {
  .mood-logs-container {
    padding: 10px;
  }

  .main-card {
    margin: 10px;
  }

  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }

  .chart-container {
    height: 250px;
  }

  .mood-cards {
    grid-template-columns: 1fr;
  }

  :deep(.el-dialog) {
    width: 95% !important;
  }
}
</style>

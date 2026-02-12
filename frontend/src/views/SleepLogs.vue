<template>
  <div class="sleep-logs-container">
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
                <el-col :span="12">
                  <p><strong>睡眠时长:</strong> {{ preprocessingResults.analysis.duration?.min }} - {{ preprocessingResults.analysis.duration?.max }} 小时 (平均: {{ preprocessingResults.analysis.duration?.avg }})</p>
                </el-col>
                <el-col :span="12">
                  <p><strong>睡眠质量:</strong> {{ preprocessingResults.analysis.quality?.min }} - {{ preprocessingResults.analysis.quality?.max }} (平均: {{ preprocessingResults.analysis.quality?.avg }})</p>
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
                <el-col :span="12" v-for="(score, idx) in preprocessingResults.health_scores.individual_scores" :key="idx">
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
          <h2 class="page-title">睡眠记录</h2>
          <div class="header-actions">
            <el-button type="info" @click="fetchSleepLogs" :loading="loading">
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
            <h3 class="section-title">睡眠时长趋势</h3>
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

        <!-- Table Section -->
        <div v-if="hasData" class="table-content">
          <el-table
            :data="sleepLogs"
            v-loading="loading"
            stripe
            style="width: 100%"
            :empty-text="'暂无数据'"
          >
            <el-table-column prop="sleep_date" label="日期" min-width="110" />
            <el-table-column label="入睡时间" min-width="100">
              <template #default="{ row }">
                {{ row.start_time ? row.start_time.substring(11, 16) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="起床时间" min-width="100">
              <template #default="{ row }">
                {{ row.end_time ? row.end_time.substring(11, 16) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="睡眠时长" min-width="100">
              <template #default="{ row }">
                {{ calculateDuration(row.start_time, row.end_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="quality_rating" label="睡眠质量" min-width="100">
              <template #default="{ row }">
                <el-rate v-model="row.quality_rating" disabled :max="10" />
                <span class="rating-text">{{ row.quality_rating }}/10</span>
              </template>
            </el-table-column>
            <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteSleepLog(row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '添加睡眠记录' : '编辑睡眠记录'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="日期" prop="sleep_date">
          <el-date-picker
            v-model="form.sleep_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="入睡时间" prop="start_time">
          <el-time-picker
            v-model="form.start_time"
            placeholder="选择入睡时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="起床时间" prop="end_time">
          <el-time-picker
            v-model="form.end_time"
            placeholder="选择起床时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="睡眠质量" prop="quality_rating">
          <el-slider
            v-model="form.quality_rating"
            :min="1"
            :max="10"
            :marks="{ 1: '1', 5: '5', 10: '10' }"
            show-stops
            style="width: 100%"
          />
          <div class="quality-label">当前评分: {{ form.quality_rating }}/10</div>
        </el-form-item>

        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
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
import { Plus, Refresh, Delete, DocumentCopy, Edit, DataAnalysis, CircleCheck } from '@element-plus/icons-vue'
import api from '../utils/axios.js'
import * as echarts from 'echarts'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('add')
const formRef = ref(null)
const chartRef = ref(null)
const sleepLogs = ref([])
const currentId = ref(null)
const hasData = ref(false)
const preprocessing = ref(false)
const cleaningAll = ref(false)
const cleaning = ref(false)
const removingDuplicates = ref(false)
const fixing = ref(false)
const validating = ref(false)
const activeCollapse = ref(['analysis', 'normalization', 'anomalies', 'health_scores'])
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
  sleep_date: '',
  start_time: '',
  end_time: '',
  quality_rating: 5,
  notes: ''
})

const rules = {
  sleep_date: [
    { required: true, message: '请选择日期', trigger: 'change' }
  ],
  start_time: [
    { required: true, message: '请选择入睡时间', trigger: 'change' }
  ],
  end_time: [
    { required: true, message: '请选择起床时间', trigger: 'change' }
  ],
  quality_rating: [
    { required: true, type: 'number', message: '请评分睡眠质量', trigger: 'change' }
  ]
}

const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return '-'
  
  const start = new Date(startTime)
  const end = new Date(endTime)
  
  const diff = (end - start) / 1000 / 60 / 60 // hours
  const hours = Math.floor(diff)
  const minutes = Math.round((diff - hours) * 60)
  
  return `${hours}小时${minutes}分钟`
}

const fetchSleepLogs = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/sleep-logs/')
    sleepLogs.value = (data.results || data || []).sort((a, b) => 
      new Date(b.sleep_date) - new Date(a.sleep_date)
    )
    hasData.value = sleepLogs.value.length > 0
    await nextTick()
    renderChart()
  } catch (error) {
    ElMessage.error('获取睡眠记录失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value || sleepLogs.value.length === 0) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)

  const sortedData = [...sleepLogs.value].sort((a, b) => 
    new Date(a.sleep_date) - new Date(b.sleep_date)
  ).slice(-30) // Last 30 days

  const dates = sortedData.map(item => item.sleep_date)
  const durations = sortedData.map(item => {
    const start = new Date(item.start_time)
    const end = new Date(item.end_time)
    return ((end - start) / 1000 / 60 / 60).toFixed(1) // hours
  })

  const series = [
    {
      data: durations,
      type: 'line',
      smooth: true,
      itemStyle: {
        color: '#667eea'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.5)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.1)' }
        ])
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
        type: 'dashed'
      }
    })
  }

  const option = {
    title: {
      text: '近期睡眠时长',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>睡眠时长: {c} 小时'
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
      name: '小时',
      min: 0,
      max: 12
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
  form.sleep_date = row.sleep_date
  // Extract time from datetime (format: "HH:mm")
  form.start_time = row.start_time ? row.start_time.substring(11, 16) : ''
  form.end_time = row.end_time ? row.end_time.substring(11, 16) : ''
  form.quality_rating = row.quality_rating
  form.notes = row.notes
  dialogVisible.value = true
}

const resetForm = () => {
  form.sleep_date = ''
  form.start_time = ''
  form.end_time = ''
  form.quality_rating = 5
  form.notes = ''
  currentId.value = null
  formRef.value?.clearValidate()
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    // Combine date with time to create datetime strings
    const startDateTime = `${form.sleep_date}T${form.start_time}:00`
    let endDateTime = `${form.sleep_date}T${form.end_time}:00`
    
    // If end time is earlier than start time, assume it's the next day
    if (form.end_time < form.start_time) {
      const nextDate = new Date(form.sleep_date)
      nextDate.setDate(nextDate.getDate() + 1)
      const nextDateStr = nextDate.toISOString().split('T')[0]
      endDateTime = `${nextDateStr}T${form.end_time}:00`
    }

    const sleepData = {
      sleep_date: form.sleep_date,
      start_time: startDateTime,
      end_time: endDateTime,
      quality_rating: form.quality_rating,
      notes: form.notes
    }

    if (dialogMode.value === 'add') {
      await api.post('/sleep-logs/', sleepData)
      ElMessage.success('添加成功')
    } else {
      await api.put(`/sleep-logs/${currentId.value}/`, sleepData)
      ElMessage.success('更新成功')
    }

    dialogVisible.value = false
    await fetchSleepLogs()
  } catch (error) {
    if (error.response) {
      ElMessage.error('操作失败: ' + (error.response?.data?.detail || JSON.stringify(error.response?.data)))
    }
  } finally {
    submitting.value = false
  }
}

const deleteSleepLog = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条睡眠记录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    await api.delete(`/sleep-logs/${id}/`)
    ElMessage.success('删除成功')
    await fetchSleepLogs()
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
      '确定要进行数据预处理吗？此操作将分析睡眠数据并检测异常。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    preprocessing.value = true
    const response = await fetch(`${API_BASE}/sleep-data-processing/preprocess_sleep_data/`, {
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
      '确定要训练GRU模型吗？此操作将使用历史睡眠数据训练预测模型，可能需要几分钟时间。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    trainingModel.value = true
    const { data } = await api.post('/gru-model/train/', {
      metrics: ['sleep_duration', 'sleep_quality']
    })
    
    ElMessage.success('模型训练完成')
    
    operationResults.value.unshift({
      message: '睡眠模型训练完成',
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
      metric: 'sleep_duration',
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
      '确定要进行一键清洗吗？此操作将清洗无效睡眠数据、删除重复记录并修复缺失值。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleaningAll.value = true
    const response = await fetch(`${API_BASE}/sleep-data-processing/clean_all_sleep_data/`, {
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
    await fetchSleepLogs()
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
      '确定要清洗无效数据吗？此操作将删除超出正常范围的睡眠数据。',
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
      body: JSON.stringify({ action: 'sleep' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await fetchSleepLogs()
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
      body: JSON.stringify({ type: 'sleep' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await fetchSleepLogs()
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
      body: JSON.stringify({ type: 'sleep' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await fetchSleepLogs()
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
    const response = await fetch(`${API_BASE}/sleep-data-processing/validate_sleep_data/`, {
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
  fetchSleepLogs()
})
</script>

<style scoped>
.sleep-logs-container {
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

.table-content {
  margin-top: 20px;
}

.rating-text {
  margin-left: 10px;
  font-size: 14px;
  color: #666;
}

.quality-label {
  margin-top: 10px;
  text-align: center;
  color: #666;
  font-size: 14px;
}

:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

:deep(.el-dialog) {
  border-radius: 15px;
}

:deep(.el-rate) {
  display: inline-flex;
}

@media (max-width: 768px) {
  .sleep-logs-container {
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

  :deep(.el-dialog) {
    width: 95% !important;
  }

  :deep(.el-table) {
    font-size: 12px;
  }
  
  :deep(.el-table .el-button) {
    padding: 5px 8px;
    font-size: 12px;
  }

  :deep(.el-rate) {
    transform: scale(0.8);
  }
}
</style>

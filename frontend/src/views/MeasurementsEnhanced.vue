<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, DocumentCopy, Edit, CircleCheck, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../utils/axios.js'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const API_BASE = 'http://127.0.0.1:8000/api'

// UI/状态
const loading = ref(false)
const saving = ref(false)
const cleaning = ref(false)
const removingDuplicates = ref(false)
const fixing = ref(false)
const validating = ref(false)
const hasData = ref(false)
const measurements = ref([])
const selectedMetric = ref('systolic')

// 预测控制
const showPrediction = ref(false)
const predictionHorizon = ref(30)
const predictionData = ref(null)

// 数据处理结果
const operationResults = ref([])
const validationResults = ref(null)

const chartRef = ref(null)
let chart = null

// 添加/编辑对话框
const showAddDialog = ref(false)
const editingId = ref(null)
const formData = ref({
  measured_at: new Date(),
  weight_kg: null,
  systolic: null,
  diastolic: null,
  heart_rate: null,
  blood_glucose: null,
  notes: ''
})

// 文案 & 单位
const metricLabels = {
  weight_kg: '体重',
  systolic: '收缩压',
  diastolic: '舒张压',
  heart_rate: '心率',
  blood_glucose: '血糖'
}
const metricUnits = {
  weight_kg: 'kg',
  systolic: 'mmHg',
  diastolic: 'mmHg',
  heart_rate: 'bpm',
  blood_glucose: 'mmol/L'
}

// DRF 列表响应规范化
function normalizeListResponse(data) {
  return Array.isArray(data) ? data : (data?.results ?? [])
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 加载列表数据
async function loadData() {
  loading.value = true
  try {
    const { data } = await api.get('/measurements/', {
      params: { ordering: 'measured_at' }
    })
    measurements.value = normalizeListResponse(data)
      .filter(m => m?.measured_at)
      .sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at))
    
    hasData.value = measurements.value.length > 0

    await nextTick()
    renderChart()
  } catch (error) {
    ElMessage.error('获取测量数据失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 加载预测
async function loadPrediction() {
  if (!showPrediction.value) return
  try {
    const { data } = await api.get('/forecast/', {
      params: { metric: selectedMetric.value, horizon: predictionHorizon.value }
    })
    predictionData.value = data
    await nextTick()
    renderChart()
  } catch (error) {
    predictionData.value = null
    console.warn('预测数据获取失败：', error)
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

// 渲染趋势图
function renderChart() {
  if (!chartRef.value) return
  if (chart) chart.dispose()
  chart = echarts.init(chartRef.value)

  const list = measurements.value
    .filter(m => m[selectedMetric.value] !== null && m[selectedMetric.value] !== undefined)

  const dates = list.map(m => new Date(m.measured_at).toLocaleDateString('zh-CN'))
  const values = list.map(m => Number(m[selectedMetric.value]))

  const series = [{
    name: metricLabels[selectedMetric.value],
    data: values,
    type: 'line',
    smooth: true,
    itemStyle: { color: '#409EFF' },
    areaStyle: selectedMetric.value === 'weight_kg' ? { opacity: 0.3 } : undefined
  }]

  if (showPrediction.value && predictionData.value?.dates && predictionData.value?.values) {
    series.push({
      name: '预测',
      data: predictionData.value.values.map(v => Number(v)),
      type: 'line',
      smooth: true,
      itemStyle: { color: '#E6A23C' },
      lineStyle: { type: 'dashed' }
    })
  }

  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: metricUnits[selectedMetric.value] },
    legend: { data: series.map(s => s.name) },
    series
  })
}

// 清洗无效数据
async function handleCleanData() {
  try {
    await ElMessageBox.confirm(
      '确定要清洗无效数据吗？此操作将删除超出正常范围的数据。',
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
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ action: 'measurements' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await loadData()
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
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ type: 'measurements' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await loadData()
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
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ type: 'measurements' })
    })
    const data = await response.json()
    
    operationResults.value.unshift({
      message: data.message,
      type: 'success',
      details: data.details
    })
    
    ElMessage.success(data.message)
    await loadData()
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
    const response = await fetch(`${API_BASE}/data-processing/validate_data/`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
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

// 保存/编辑记录
async function saveMeasurement() {
  saving.value = true
  try {
    const payload = {
      measured_at: new Date(formData.value.measured_at).toISOString(),
      weight_kg: formData.value.weight_kg ?? null,
      systolic: formData.value.systolic ?? null,
      diastolic: formData.value.diastolic ?? null,
      heart_rate: formData.value.heart_rate ?? null,
      blood_glucose: formData.value.blood_glucose ?? null,
      notes: formData.value.notes
    }
    ;['weight_kg','systolic','diastolic','heart_rate','blood_glucose'].forEach(k => {
      if (payload[k] !== null) payload[k] = Number(payload[k])
    })

    if (editingId.value) {
      await api.put(`/measurements/${editingId.value}/`, payload)
      ElMessage.success('记录已更新')
    } else {
      await api.post('/measurements/', payload)
      ElMessage.success('记录已添加')
    }
    showAddDialog.value = false
    editingId.value = null
    await loadData()
  } catch (error) {
    ElMessage.error('保存失败：' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

// 编辑 & 删除
function editMeasurement(row) {
  editingId.value = row.id
  showAddDialog.value = true
  formData.value = {
    measured_at: new Date(row.measured_at),
    weight_kg: row.weight_kg ?? null,
    systolic: row.systolic ?? null,
    diastolic: row.diastolic ?? null,
    heart_rate: row.heart_rate ?? null,
    blood_glucose: row.blood_glucose ?? null,
    notes: row.notes ?? ''
  }
}

async function deleteMeasurement(id) {
  try {
    await api.delete(`/measurements/${id}/`)
    ElMessage.success('记录已删除')
    await loadData()
  } catch (error) {
    ElMessage.error('删除失败：' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadData()
  if (showPrediction.value) loadPrediction()
})

onUnmounted(() => {
  chart?.dispose()
  radarChart?.dispose()
})
</script>

<template>
  <div class="page-container">
    <el-card class="controls-card">
      <div class="controls">
        <div class="metric-selector">
          <label>选择指标:</label>
          <el-select v-model="selectedMetric" @change="renderChart" placeholder="请选择指标">
            <el-option label="体重" value="weight_kg" />
            <el-option label="收缩压" value="systolic" />
            <el-option label="舒张压" value="diastolic" />
            <el-option label="心率" value="heart_rate" />
            <el-option label="血糖" value="blood_glucose" />
          </el-select>
        </div>

        <div class="prediction-controls">
          <el-checkbox v-model="showPrediction" @change="togglePrediction">显示预测</el-checkbox>
          <el-select
            v-if="showPrediction"
            v-model="predictionHorizon"
            @change="loadPrediction"
            placeholder="预测天数"
            style="width: 120px; margin-left: 10px;"
          >
            <el-option label="7天" :value="7" />
            <el-option label="14天" :value="14" />
            <el-option label="30天" :value="30" />
          </el-select>
        </div>

        <el-button type="primary" @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          拉取数据
        </el-button>
      </div>
    </el-card>

    <el-card class="chart-card">
      <template #header>
        <span>趋势图</span>
      </template>
      <div v-if="!hasData" class="no-data">
        <el-empty description="No Data" />
      </div>
      <div v-else ref="chartRef" class="chart-container" v-loading="loading"></div>
    </el-card>

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
    </el-card>

    <el-card class="table-card">
      <div class="table-header">
        <h3>历史记录</h3>
        <el-button type="primary" @click="showAddDialog = true">添加记录</el-button>
      </div>

      <el-table :data="measurements" style="width: 100%" :empty-text="'暂无数据'">
        <el-table-column prop="measured_at" label="测量时间" width="180">
          <template #default="{ row }">{{ formatDate(row.measured_at) }}</template>
        </el-table-column>
        <el-table-column prop="weight_kg" label="体重(kg)" width="100" />
        <el-table-column prop="systolic" label="收缩压" width="100" />
        <el-table-column prop="diastolic" label="舒张压" width="100" />
        <el-table-column prop="heart_rate" label="心率(bpm)" width="100" />
        <el-table-column prop="blood_glucose" label="血糖(mmol/L)" width="120" />
        <el-table-column prop="notes" label="备注" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editMeasurement(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteMeasurement(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" :title="editingId ? '编辑记录' : '添加记录'" width="500px">
      <el-form :model="formData" label-width="120px">
        <el-form-item label="测量时间">
          <el-date-picker v-model="formData.measured_at" type="datetime" placeholder="选择时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="体重(kg)">
          <el-input-number v-model="formData.weight_kg" :min="0" :max="300" :precision="1" />
        </el-form-item>
        <el-form-item label="收缩压">
          <el-input-number v-model="formData.systolic" :min="0" :max="300" />
        </el-form-item>
        <el-form-item label="舒张压">
          <el-input-number v-model="formData.diastolic" :min="0" :max="200" />
        </el-form-item>
        <el-form-item label="心率(bpm)">
          <el-input-number v-model="formData.heart_rate" :min="0" :max="250" />
        </el-form-item>
        <el-form-item label="血糖(mmol/L)">
          <el-input-number v-model="formData.blood_glucose" :min="0" :max="30" :precision="1" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.notes" type="textarea" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMeasurement" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.controls { display: flex; gap: 12px; align-items: center; }
.chart-card { margin-top: 16px; }
.chart-container { height: 360px; }
.no-data { height: 360px; display: flex; align-items: center; justify-content: center; }
.radar-card { margin-top: 16px; }
.radar-container { height: 360px; }
.table-card { margin-top: 16px; }
.table-header { display: flex; justify-content: space-between; align-items: center; }

.data-processing-card { margin-top: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.data-processing-buttons { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }

.operation-results { margin-top: 20px; }
.result-item { margin-bottom: 15px; }
.result-details ul { margin: 10px 0 0; padding-left: 20px; }
.result-details li { margin: 5px 0; color: #606266; font-size: 12px; }

.validation-results { margin-top: 20px; }
.validation-item { padding: 20px; border-radius: 8px; text-align: center; }
.validation-item.passed { background-color: #f0f9ff; border: 2px solid #67C23A; }
.validation-item.failed { background-color: #fef0f0; border: 2px solid #F56C6C; }
.validation-item.warning { background-color: #fdf6ec; border: 2px solid #E6A23C; }
.validation-count { font-size: 32px; font-weight: bold; color: #303133; }
.validation-label { font-size: 14px; color: #606266; margin-top: 5px; }

.validation-details { margin-top: 15px; }
.validation-details ul { margin: 0; padding-left: 20px; }
.validation-details li { margin: 8px 0; padding: 8px; border-radius: 4px; }
.validation-details li.passed { color: #67C23A; background-color: #f0f9ff; }
.validation-details li.failed { color: #F56C6C; background-color: #fef0f0; }
.validation-details li.warning { color: #E6A23C; background-color: #fdf6ec; }
</style>

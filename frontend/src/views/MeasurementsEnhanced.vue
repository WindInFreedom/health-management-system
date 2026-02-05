<template>
  <div class="measurements-page">
    <el-card class="controls-card">
      <div class="controls">
        <div class="metric-selector">
          <label>选择指标:</label>
          <el-select v-model="selectedMetric" @change="loadData" placeholder="请选择指标">
            <el-option label="体重" value="weight_kg" />
            <el-option label="收缩压" value="systolic" />
            <el-option label="舒张压" value="diastolic" />
            <el-option label="心率" value="heart_rate" />
            <el-option label="血糖" value="blood_glucose" />
          </el-select>
        </div>
        
        <div class="prediction-controls">
          <el-checkbox v-model="showPrediction" @change="togglePrediction">
            显示预测
          </el-checkbox>
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
        
        <el-button type="primary" @click="loadData">
          刷新数据
        </el-button>
      </div>
    </el-card>

    <el-card class="chart-card">
      <div ref="chartRef" class="chart-container" v-loading="loading"></div>
    </el-card>

    <el-card class="table-card">
      <div class="table-header">
        <h3>历史记录</h3>
        <el-button type="primary" @click="showAddDialog = true">
          添加记录
        </el-button>
      </div>
      
      <el-table :data="measurements" style="width: 100%" :empty-text="'暂无数据'">
        <el-table-column prop="measured_at" label="测量时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.measured_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="weight_kg" label="体重(kg)" width="100" />
        <el-table-column prop="systolic" label="收缩压" width="100" />
        <el-table-column prop="diastolic" label="舒张压" width="100" />
        <el-table-column prop="heart_rate" label="心率(bpm)" width="100" />
        <el-table-column prop="blood_glucose" label="血糖(mmol/L)" width="120" />
        <el-table-column prop="notes" label="备注" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editMeasurement(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteMeasurement(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog 
      v-model="showAddDialog" 
      :title="editingId ? '编辑记录' : '添加记录'"
      width="500px"
    >
      <el-form :model="formData" label-width="120px">
        <el-form-item label="测量时间">
          <el-date-picker 
            v-model="formData.measured_at" 
            type="datetime"
            placeholder="选择时间"
            style="width: 100%"
          />
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
          <el-input v-model="formData.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMeasurement" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import api from '../utils/axios.js'

const loading = ref(false)
const saving = ref(false)
const measurements = ref([])
const selectedMetric = ref('systolic')
const showPrediction = ref(false)
const predictionHorizon = ref(30)
const predictionData = ref(null)
const chartRef = ref(null)
const showAddDialog = ref(false)
const editingId = ref(null)

let chart = null

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

// Normalize DRF list response - handle both raw arrays and paginated responses
function normalizeListResponse(data) {
  return Array.isArray(data) ? data : (data?.results ?? [])
}

const formData = ref({
  measured_at: new Date(),
  weight_kg: null,
  systolic: null,
  diastolic: null,
  heart_rate: null,
  blood_glucose: null,
  notes: ''
})

// Utility to normalize DRF list responses
function normalizeListResponse(data) {
  return Array.isArray(data) ? data : (data?.results ?? [])
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
  }
})

async function loadData() {
  loading.value = true
  try {
    const { data } = await api.get('/measurements/', {
      params: { ordering: 'measured_at' }
    })
    // Normalize, filter missing measured_at, and sort ascending by time
    measurements.value = normalizeListResponse(data)
      .filter(m => m?.measured_at)
      .sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at))
    
    await nextTick()
    if (showPrediction.value) {
      await loadPrediction()
    } else {
      renderChart()
    }
  } catch (error) {
    ElMessage.error('获取测量数据失败：' + (error.response?.data?.detail || error.message))
    console.error('Load measurements error:', error)
  } finally {
    loading.value = false
  }
}

async function loadPrediction() {
  if (!showPrediction.value) return
  
  loading.value = true
  try {
    const { data } = await api.get('/forecast/', {
      params: {
        metric: selectedMetric.value,
        horizon: predictionHorizon.value
      }
    })
    predictionData.value = data
    renderChart()
  } catch (error) {
    ElMessage.warning(error.response?.data?.error || '预测失败')
    console.error('Load prediction error:', error)
    predictionData.value = null
    renderChart()
  } finally {
    loading.value = false
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

function renderChart() {
  if (!chartRef.value) return
  
  // Dispose existing chart instance to avoid stale state
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value)
  
  const metric = selectedMetric.value
  const label = metricLabels[metric]
  const unit = metricUnits[metric]
  
  // Historical data - enforce numeric conversion
  const historicalData = measurements.value
    .filter(m => m[metric] !== null && m[metric] !== undefined)
    .map(m => [new Date(m.measured_at), Number(m[metric])])
  
  const series = [
    {
      name: `历史${label}`,
      type: 'line',
      data: historicalData,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        color: '#667eea',
        width: 2
      },
      itemStyle: {
        color: '#667eea'
      }
    }
  ]
  
  // Prediction data
  if (showPrediction.value && predictionData.value) {
    const forecastData = predictionData.value.dates.map((date, i) => [
      new Date(date),
      Number(predictionData.value.forecast[i])
    ])
    
    const upperData = predictionData.value.dates.map((date, i) => [
      new Date(date),
      Number(predictionData.value.confidence_upper[i])
    ])
    
    const lowerData = predictionData.value.dates.map((date, i) => [
      new Date(date),
      Number(predictionData.value.confidence_lower[i])
    ])
    
    series.push({
      name: `预测${label}`,
      type: 'line',
      data: forecastData,
      smooth: true,
      lineStyle: {
        color: '#f56c6c',
        width: 2,
        type: 'dashed'
      },
      itemStyle: {
        color: '#f56c6c'
      }
    })
    
    series.push({
      name: '置信区间上限',
      type: 'line',
      data: upperData,
      smooth: true,
      lineStyle: {
        color: '#f56c6c',
        width: 1,
        type: 'dotted',
        opacity: 0.5
      },
      itemStyle: {
        opacity: 0
      },
      symbol: 'none'
    })
    
    series.push({
      name: '置信区间下限',
      type: 'line',
      data: lowerData,
      smooth: true,
      lineStyle: {
        color: '#f56c6c',
        width: 1,
        type: 'dotted',
        opacity: 0.5
      },
      itemStyle: {
        opacity: 0
      },
      symbol: 'none',
      areaStyle: {
        color: 'rgba(245, 108, 108, 0.1)'
      }
    })
  }
  
  const option = {
    title: {
      text: `${label}趋势图`,
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 40
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 80,
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: unit,
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: series
  }
  
  chart.setOption(option)
}

function handleResize() {
  chart?.resize()
}

function editMeasurement(row) {
  editingId.value = row.id
  formData.value = {
    measured_at: new Date(row.measured_at),
    weight_kg: row.weight_kg,
    systolic: row.systolic,
    diastolic: row.diastolic,
    heart_rate: row.heart_rate,
    blood_glucose: row.blood_glucose,
    notes: row.notes || ''
  }
  showAddDialog.value = true
}

async function saveMeasurement() {
  saving.value = true
  try {
    // Sanitize payload: ISO timestamp and numeric values
    const payload = {
      measured_at: new Date(formData.value.measured_at).toISOString(),
      weight_kg: formData.value.weight_kg ?? null,
      systolic: formData.value.systolic ?? null,
      diastolic: formData.value.diastolic ?? null,
      heart_rate: formData.value.heart_rate ?? null,
      blood_glucose: formData.value.blood_glucose ?? null,
      notes: formData.value.notes
    }
    
    // Ensure numeric fields are numbers
    ;['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose'].forEach(k => {
      if (payload[k] !== null) {
        payload[k] = Number(payload[k])
      }
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
    resetForm()
    await loadData()
  } catch (error) {
    ElMessage.error('保存失败：' + (error.response?.data?.error || error.message))
    console.error('Save measurement error:', error)
  } finally {
    saving.value = false
  }
}

async function deleteMeasurement(id) {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/measurements/${id}/`)
    ElMessage.success('删除成功')
    await loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete measurement error:', error)
    }
  }
}

function resetForm() {
  formData.value = {
    measured_at: new Date(),
    weight_kg: null,
    systolic: null,
    diastolic: null,
    heart_rate: null,
    blood_glucose: null,
    notes: ''
  }
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.measurements-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.controls-card {
  margin-bottom: 20px;
}

.controls {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.metric-selector,
.prediction-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.metric-selector label {
  font-weight: 500;
  color: #333;
}

.chart-card {
  margin-bottom: 20px;
  min-height: 500px;
}

.chart-container {
  width: 100%;
  height: 450px;
}

.table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-header h3 {
  margin: 0;
  color: #333;
}

@media (max-width: 768px) {
  .measurements-page {
    padding: 10px;
  }
  
  .controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .chart-container {
    height: 300px;
  }
}
</style>

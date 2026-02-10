<template>
  <div class="sleep-logs-container">
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
          <h3 class="section-title">睡眠时长趋势</h3>
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
import { Plus, Refresh } from '@element-plus/icons-vue'
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
      data: dates,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(dates.length / 10) || 0
      }
    },
    yAxis: {
      type: 'value',
      name: '小时',
      min: 0,
      max: 12
    },
    series: [
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
    ],
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

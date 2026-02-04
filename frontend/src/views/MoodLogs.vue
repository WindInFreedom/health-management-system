<template>
  <div class="mood-logs-container">
    <el-card class="main-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h2 class="page-title">情绪日志</h2>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加记录
          </el-button>
        </div>
      </template>

      <div class="content">
        <!-- Chart Section -->
        <div class="chart-section" v-if="moodLogs.length > 0">
          <h3 class="section-title">情绪趋势</h3>
          <div ref="chartRef" class="chart-container"></div>
        </div>

        <!-- Cards Section -->
        <div class="cards-section">
          <el-empty v-if="moodLogs.length === 0" description="暂无情绪记录" />
          <div v-else class="mood-cards">
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
import { Plus, Calendar, Edit, Delete } from '@element-plus/icons-vue'
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
      data: dates,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(dates.length / 10) || 0
      }
    },
    yAxis: {
      type: 'value',
      name: '心情指数',
      min: 0,
      max: 10
    },
    series: [
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

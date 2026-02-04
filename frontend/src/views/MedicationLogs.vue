<template>
  <div class="medication-logs-container">
    <el-card class="main-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h2 class="page-title">用药记录</h2>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加用药
          </el-button>
        </div>
      </template>

      <div class="table-content">
        <el-table
          :data="medications"
          v-loading="loading"
          stripe
          style="width: 100%"
          :empty-text="'暂无数据'"
        >
          <el-table-column prop="medication_name" label="药品名称" min-width="120" />
          <el-table-column prop="dosage" label="剂量" min-width="100" />
          <el-table-column prop="frequency" label="频率" min-width="100" />
          <el-table-column prop="start_date" label="开始日期" min-width="110" />
          <el-table-column prop="end_date" label="结束日期" min-width="110">
            <template #default="{ row }">
              {{ row.end_date || '持续中' }}
            </template>
          </el-table-column>
          <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteMedication(row.id)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '添加用药记录' : '编辑用药记录'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="药品名称" prop="medication_name">
          <el-input v-model="form.medication_name" placeholder="请输入药品名称" />
        </el-form-item>

        <el-form-item label="剂量" prop="dosage">
          <el-input v-model="form.dosage" placeholder="例如: 100mg, 2片" />
        </el-form-item>

        <el-form-item label="频率" prop="frequency">
          <el-input v-model="form.frequency" placeholder="例如: 每日3次, 饭后服用" />
        </el-form-item>

        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker
            v-model="form.start_date"
            type="date"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="选择结束日期（可选）"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../utils/axios.js'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('add')
const formRef = ref(null)
const medications = ref([])
const currentId = ref(null)

const form = reactive({
  medication_name: '',
  dosage: '',
  frequency: '',
  start_date: '',
  end_date: '',
  notes: ''
})

const rules = {
  medication_name: [
    { required: true, message: '请输入药品名称', trigger: 'blur' }
  ],
  dosage: [
    { required: true, message: '请输入剂量', trigger: 'blur' }
  ],
  frequency: [
    { required: true, message: '请输入用药频率', trigger: 'blur' }
  ],
  start_date: [
    { required: true, message: '请选择开始日期', trigger: 'change' }
  ]
}

const fetchMedications = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/medications/')
    medications.value = data.results || data || []
  } catch (error) {
    ElMessage.error('获取用药记录失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogMode.value = 'add'
  dialogVisible.value = true
  resetForm()
}

const showEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentId.value = row.id
  form.medication_name = row.medication_name
  form.dosage = row.dosage
  form.frequency = row.frequency
  form.start_date = row.start_date
  form.end_date = row.end_date
  form.notes = row.notes
  dialogVisible.value = true
}

const resetForm = () => {
  form.medication_name = ''
  form.dosage = ''
  form.frequency = ''
  form.start_date = ''
  form.end_date = ''
  form.notes = ''
  currentId.value = null
  formRef.value?.clearValidate()
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    const medicationData = {
      medication_name: form.medication_name,
      dosage: form.dosage,
      frequency: form.frequency,
      start_date: form.start_date,
      end_date: form.end_date || null,
      notes: form.notes
    }

    if (dialogMode.value === 'add') {
      await api.post('/medications/', medicationData)
      ElMessage.success('添加成功')
    } else {
      await api.put(`/medications/${currentId.value}/`, medicationData)
      ElMessage.success('更新成功')
    }

    dialogVisible.value = false
    await fetchMedications()
  } catch (error) {
    if (error.response) {
      ElMessage.error('操作失败: ' + (error.response?.data?.detail || JSON.stringify(error.response?.data)))
    }
  } finally {
    submitting.value = false
  }
}

const deleteMedication = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条用药记录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    await api.delete(`/medications/${id}/`)
    ElMessage.success('删除成功')
    await fetchMedications()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMedications()
})
</script>

<style scoped>
.medication-logs-container {
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

.table-content {
  padding: 10px 0;
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

@media (max-width: 768px) {
  .medication-logs-container {
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
}
</style>

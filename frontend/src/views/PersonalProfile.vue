<template>
  <div class="personal-profile-container">
    <el-card class="main-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h2 class="page-title">基本档案</h2>
          <el-button v-if="!isEditing" type="primary" @click="startEdit">
            编辑
          </el-button>
          <div v-else>
            <el-button @click="cancelEdit">取消</el-button>
            <el-button type="primary" @click="saveProfile" :loading="loading">
              保存
            </el-button>
          </div>
        </div>
      </template>

      <div class="profile-content">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="120px"
          :disabled="!isEditing"
          class="profile-form"
        >
          <el-form-item label="年龄" prop="age">
            <el-input-number
              v-model="form.age"
              :min="0"
              :max="150"
              placeholder="请输入年龄"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="性别" prop="gender">
            <el-select v-model="form.gender" placeholder="请选择性别" style="width: 100%">
              <el-option label="男" value="M" />
              <el-option label="女" value="F" />
              <el-option label="其他" value="O" />
            </el-select>
          </el-form-item>

          <el-form-item label="血型" prop="blood_type">
            <el-select v-model="form.blood_type" placeholder="请选择血型" style="width: 100%">
              <el-option label="A型" value="A" />
              <el-option label="B型" value="B" />
              <el-option label="AB型" value="AB" />
              <el-option label="O型" value="O" />
              <el-option label="未知" value="Unknown" />
            </el-select>
          </el-form-item>

          <el-form-item label="身高 (cm)" prop="height_cm">
            <el-input-number
              v-model="form.height_cm"
              :min="0"
              :max="300"
              :precision="1"
              placeholder="请输入身高"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="基准体重 (kg)" prop="weight_baseline_kg">
            <el-input-number
              v-model="form.weight_baseline_kg"
              :min="0"
              :max="500"
              :precision="1"
              placeholder="请输入体重"
              style="width: 100%"
            />
          </el-form-item>
        </el-form>

        <el-empty v-if="!profileExists && !isEditing" description="尚未创建档案，请点击编辑开始填写" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/axios.js'

const loading = ref(false)
const isEditing = ref(false)
const profileExists = ref(false)
const formRef = ref(null)
const originalForm = ref({})

const form = reactive({
  age: null,
  gender: '',
  blood_type: '',
  height_cm: null,
  weight_baseline_kg: null
})

const rules = {
  age: [
    { type: 'number', message: '年龄必须为数字', trigger: 'blur' }
  ],
  height_cm: [
    { type: 'number', message: '身高必须为数字', trigger: 'blur' }
  ],
  weight_baseline_kg: [
    { type: 'number', message: '体重必须为数字', trigger: 'blur' }
  ]
}

const fetchProfile = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/profile/me/')
    if (data) {
      form.age = data.age
      form.gender = data.gender
      form.blood_type = data.blood_type
      form.height_cm = data.height_cm
      form.weight_baseline_kg = data.weight_baseline_kg
      profileExists.value = true
      originalForm.value = { ...form }
    }
  } catch (error) {
    if (error.response?.status === 404) {
      profileExists.value = false
      ElMessage.info('尚未创建档案，请点击编辑开始填写')
    } else {
      ElMessage.error('获取档案失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    loading.value = false
  }
}

const startEdit = () => {
  isEditing.value = true
  originalForm.value = { ...form }
}

const cancelEdit = () => {
  isEditing.value = false
  Object.assign(form, originalForm.value)
  formRef.value?.clearValidate()
}

const saveProfile = async () => {
  try {
    await formRef.value.validate()
    loading.value = true

    const profileData = {
      age: form.age,
      gender: form.gender,
      blood_type: form.blood_type,
      height_cm: form.height_cm,
      weight_baseline_kg: form.weight_baseline_kg
    }

    if (profileExists.value) {
      await api.put('/profile/me/', profileData)
    } else {
      await api.post('/profile/me/', profileData)
      profileExists.value = true
    }

    ElMessage.success('档案保存成功')
    isEditing.value = false
    originalForm.value = { ...form }
  } catch (error) {
    if (error.response) {
      ElMessage.error('保存失败: ' + (error.response?.data?.detail || JSON.stringify(error.response?.data)))
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProfile()
})
</script>

<style scoped>
.personal-profile-container {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.main-card {
  max-width: 800px;
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

.profile-content {
  padding: 20px 0;
  min-height: 300px;
}

.profile-form {
  max-width: 600px;
  margin: 0 auto;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: left;
}

@media (max-width: 768px) {
  .personal-profile-container {
    padding: 10px;
  }

  .main-card {
    margin: 10px;
  }

  .profile-form {
    max-width: 100%;
  }

  :deep(.el-form-item__label) {
    width: 100px !important;
  }

  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
}
</style>

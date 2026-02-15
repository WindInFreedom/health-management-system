<template>
  <div class="model-metrics-card">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="title">模型评估指标</span>
          <el-tag :type="getModelQualityType(metrics.R2)">
            {{ getModelQualityLabel(metrics.R2) }}
          </el-tag>
        </div>
      </template>

      <div class="metrics-grid">
        <div class="metric-item">
          <div class="metric-label">MAE</div>
          <div class="metric-value">{{ metrics.MAE?.toFixed(4) || 'N/A' }}</div>
          <div class="metric-desc">平均绝对误差</div>
        </div>

        <div class="metric-item">
          <div class="metric-label">RMSE</div>
          <div class="metric-value">{{ metrics.RMSE?.toFixed(4) || 'N/A' }}</div>
          <div class="metric-desc">均方根误差</div>
        </div>

        <div class="metric-item">
          <div class="metric-label">R²</div>
          <div 
            class="metric-value" 
            :style="{ color: getR2Color(metrics.R2) }"
          >
            {{ metrics.R2?.toFixed(4) || 'N/A' }}
          </div>
          <div class="metric-desc">决定系数</div>
        </div>

        <div class="metric-item">
          <div class="metric-label">MAPE</div>
          <div class="metric-value">{{ metrics.MAPE?.toFixed(2) || 'N/A' }}%</div>
          <div class="metric-desc">平均绝对百分比误差</div>
        </div>
      </div>

      <div class="expand-section" v-if="showDetails">
        <el-divider />
        <el-button 
          text 
          @click="toggleDetails"
          style="width: 100%"
        >
          <span>{{ detailsExpanded ? '收起' : '展开' }}详细信息</span>
          <el-icon :class="{ 'is-rotated': detailsExpanded }">
            <ArrowDown />
          </el-icon>
        </el-button>

        <el-collapse-transition>
          <div v-show="detailsExpanded" class="details-content">
            <h4>性能说明</h4>
            <ul class="performance-tips">
              <li v-if="metrics.R2 > 0.5">
                <el-icon color="#52c41a"><SuccessFilled /></el-icon>
                模型拟合效果良好，R² > 0.5
              </li>
              <li v-else-if="metrics.R2 > 0.2">
                <el-icon color="#faad14"><WarningFilled /></el-icon>
                模型拟合一般，建议增加训练数据
              </li>
              <li v-else>
                <el-icon color="#f5222d"><CircleCloseFilled /></el-icon>
                模型拟合较差，建议重新训练
              </li>
              
              <li v-if="metrics.MAPE < 10">
                <el-icon color="#52c41a"><SuccessFilled /></el-icon>
                预测误差率较低 (MAPE < 10%)
              </li>
              <li v-else-if="metrics.MAPE < 20">
                <el-icon color="#faad14"><WarningFilled /></el-icon>
                预测误差率中等 (MAPE 10-20%)
              </li>
            </ul>

            <h4 style="margin-top: 16px">指标解释</h4>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="MAE">
                平均绝对误差，值越小表示预测越准确
              </el-descriptions-item>
              <el-descriptions-item label="RMSE">
                均方根误差，对大误差更敏感
              </el-descriptions-item>
              <el-descriptions-item label="R²">
                决定系数，取值0-1，越接近1表示模型拟合越好
              </el-descriptions-item>
              <el-descriptions-item label="MAPE">
                平均绝对百分比误差，以百分比表示误差
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-collapse-transition>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { 
  ArrowDown, 
  SuccessFilled, 
  WarningFilled, 
  CircleCloseFilled 
} from '@element-plus/icons-vue'

const props = defineProps({
  metrics: {
    type: Object,
    required: true,
    default: () => ({
      MAE: 0,
      RMSE: 0,
      R2: 0,
      MAPE: 0
    })
  },
  showDetails: {
    type: Boolean,
    default: true
  }
})

const detailsExpanded = ref(false)

const toggleDetails = () => {
  detailsExpanded.value = !detailsExpanded.value
}

const getModelQualityType = (r2) => {
  if (r2 > 0.5) return 'success'
  if (r2 > 0.2) return 'warning'
  return 'danger'
}

const getModelQualityLabel = (r2) => {
  if (r2 > 0.5) return '优秀'
  if (r2 > 0.2) return '良好'
  return '需改进'
}

const getR2Color = (r2) => {
  if (r2 > 0.5) return '#52c41a'
  if (r2 > 0.2) return '#faad14'
  return '#f5222d'
}
</script>

<style scoped>
.model-metrics-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: bold;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.metric-item {
  text-align: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.metric-desc {
  font-size: 12px;
  color: #909399;
}

.expand-section {
  margin-top: 16px;
}

.is-rotated {
  transform: rotate(180deg);
  transition: transform 0.3s;
}

.details-content {
  padding: 16px 0;
}

.performance-tips {
  list-style: none;
  padding: 0;
  margin: 8px 0;
}

.performance-tips li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 14px;
}

h4 {
  font-size: 14px;
  font-weight: bold;
  margin: 12px 0 8px 0;
  color: #303133;
}
</style>

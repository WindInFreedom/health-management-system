<template>
  <div>
    <el-card>
      <div style="height:360px;" ref="chart"></div>
    </el-card>

    <el-table :data="measurements" style="margin-top:20px;">
      <el-table-column prop="measured_at" label="测量时间" :formatter="formatDate" />
      <el-table-column prop="weight_kg" label="体重(kg)" />
      <el-table-column prop="systolic" label="收缩压" />
      <el-table-column prop="diastolic" label="舒张压" />
      <el-table-column prop="heart_rate" label="心率" />
      <el-table-column prop="blood_glucose" label="血糖" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button size="mini" @click="edit(row)">编辑</el-button>
          <el-button type="danger" size="mini" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

import api from '../utils/api'
export default {
  name: 'MeasurementsList',
  data() {
    return {
      measurements: []
    }
  },
  mounted() {
    this.loadMeasurements()
    window.addEventListener('resize', this.resizeChart)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeChart)
  },
  methods: {
    async loadMeasurements() {
      try {
        // ordering=measured_at (后端 MeasurementViewSet 支持 ordering)
        const resp = await api.get('/api/measurements/', { params: { ordering: 'measured_at' } })
        // DRF 默认 list 返回的是数组
        this.measurements = resp.data
        this.renderChart()
      } catch (err) {
        console.error(err)
        ElMessage.error('获取测量数据失败')
      }
    },
    renderChart() {
      if (!this.$refs.chart) return
      const chart = echarts.init(this.$refs.chart)
      const times = this.measurements.map(m => new Date(m.measured_at))
      const weightSeries = this.measurements.map(m => m.weight_kg)
      const sysSeries = this.measurements.map(m => m.systolic)
      const diaSeries = this.measurements.map(m => m.diastolic)

      const option = {
        tooltip: { trigger: 'axis', formatter: params => {
          // 简单格式化
          return params.map(p => `${p.seriesName}: ${p.data[1]}`).join('<br/>')
        }},
        legend: { data: ['体重','收缩压','舒张压'] },
        xAxis: { type: 'time' },
        yAxis: [{ type: 'value' }],
        series: [
          { name: '体重', type: 'line', showSymbol: false, data: this.measurements.map(m => [new Date(m.measured_at), m.weight_kg]) },
          { name: '收缩压', type: 'line', showSymbol: false, data: this.measurements.map(m => [new Date(m.measured_at), m.systolic]) },
          { name: '舒张压', type: 'line', showSymbol: false, data: this.measurements.map(m => [new Date(m.measured_at), m.diastolic]) },
        ]
      }
      chart.setOption(option)
      this._chart = chart
    },
    resizeChart() {
      if (this._chart) this._chart.resize()
    },
    formatDate(row, column, cellValue) {
      return new Date(cellValue).toLocaleString('zh-CN')
    },
    edit(row) {
      // 跳转到编辑对话框或页面，依据项目已有代码风格
      this.$router.push({ name: 'EditMeasurement', params: { id: row.id }})
    },
    async remove(id) {
      try {
        await api.delete(`/api/measurements/${id}/`)
        ElMessage.success('删除成功')
        this.loadMeasurements()
      } catch (err) {
        ElMessage.error('删除失败')
      }
    }
  }
}
</script>

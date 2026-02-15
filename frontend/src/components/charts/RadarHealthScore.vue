<template>
  <div class="radar-health-score">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  scores: {
    type: Object,
    required: true,
    default: () => ({
      blood_glucose: 80,
      heart_rate: 85,
      systolic: 75,
      diastolic: 80,
      weight_kg: 90
    })
  }
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  const option = {
    title: {
      text: '综合健康评分',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: [
        { name: '血糖', max: 100 },
        { name: '心率', max: 100 },
        { name: '收缩压', max: 100 },
        { name: '舒张压', max: 100 },
        { name: '体重', max: 100 }
      ],
      radius: '65%',
      splitNumber: 4,
      axisName: {
        color: '#666',
        fontSize: 14
      },
      splitLine: {
        lineStyle: {
          color: ['#ddd', '#ddd', '#ddd', '#ddd']
        }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(82, 196, 26, 0.05)', 'rgba(82, 196, 26, 0.1)']
        }
      }
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: [
              props.scores.blood_glucose || 0,
              props.scores.heart_rate || 0,
              props.scores.systolic || 0,
              props.scores.diastolic || 0,
              props.scores.weight_kg || 0
            ],
            name: '健康评分',
            areaStyle: {
              color: 'rgba(24, 144, 255, 0.3)'
            },
            lineStyle: {
              color: '#1890ff',
              width: 2
            },
            itemStyle: {
              color: '#1890ff'
            }
          }
        ]
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  chartInstance?.resize()
}

watch(() => props.scores, () => {
  initChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.radar-health-score {
  width: 100%;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 350px;
}
</style>

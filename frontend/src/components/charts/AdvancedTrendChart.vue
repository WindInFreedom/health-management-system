<template>
  <div class="advanced-trend-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  historicalData: {
    type: Array,
    default: () => []
  },
  predictions: {
    type: Array,
    default: () => []
  },
  confidenceInterval: {
    type: Object,
    default: () => ({ lower: [], upper: [] })
  },
  historicalBacktest: {
    type: Object,
    default: () => ({ actual: [], predicted: [] })
  },
  futureDates: {
    type: Array,
    default: () => []
  },
  metric: {
    type: String,
    default: 'blood_glucose'
  },
  thresholdLine: {
    type: Number,
    default: null
  }
})

const chartRef = ref(null)
let chartInstance = null

const metricNames = {
  blood_glucose: '血糖',
  heart_rate: '心率',
  systolic: '收缩压',
  diastolic: '舒张压',
  weight_kg: '体重'
}

const metricUnits = {
  blood_glucose: 'mmol/L',
  heart_rate: 'bpm',
  systolic: 'mmHg',
  diastolic: 'mmHg',
  weight_kg: 'kg'
}

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  // 准备数据
  const historicalDates = props.historicalData.map(item => item.date)
  const historicalValues = props.historicalData.map(item => item.value)
  
  // 历史回测数据（取最后50个点用于显示）
  const backtest = props.historicalBacktest
  const backtestLength = Math.min(50, backtest.actual?.length || 0)
  const backtestDates = historicalDates.slice(-backtestLength)
  const backtestActual = backtest.actual?.slice(-backtestLength) || []
  const backtestPredicted = backtest.predicted?.slice(-backtestLength) || []

  // 置信区间数据
  const ciUpper = props.futureDates.map((date, i) => [date, props.confidenceInterval.upper[i]])
  const ciLower = props.futureDates.map((date, i) => [date, props.confidenceInterval.lower[i]])

  const option = {
    title: {
      text: `${metricNames[props.metric]}预测趋势`,
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
      },
      formatter: (params) => {
        let html = `<div style="font-weight: bold">${params[0].axisValue}</div>`
        params.forEach(param => {
          html += `<div>${param.marker} ${param.seriesName}: ${param.value[1]?.toFixed(2) || param.value?.toFixed(2)} ${metricUnits[props.metric]}</div>`
        })
        return html
      }
    },
    legend: {
      data: ['历史实际值', '历史预测值（回测）', '未来预测值', '95%置信区间', '用户阈值'],
      top: 40,
      selected: {
        '历史实际值': true,
        '历史预测值（回测）': true,
        '未来预测值': true,
        '95%置信区间': true,
        '用户阈值': props.thresholdLine !== null
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: metricUnits[props.metric],
      axisLabel: {
        formatter: '{value}'
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100,
        height: 20,
        bottom: 10
      }
    ],
    series: [
      // 1. 历史实际值 - 绿色实心圆点
      {
        name: '历史实际值',
        type: 'scatter',
        data: backtestDates.map((date, i) => [date, backtestActual[i]]),
        symbolSize: 6,
        itemStyle: {
          color: '#52c41a'
        },
        z: 3
      },
      // 2. 历史预测值（回测）- 红色虚线
      {
        name: '历史预测值（回测）',
        type: 'line',
        data: backtestDates.map((date, i) => [date, backtestPredicted[i]]),
        lineStyle: {
          type: 'dashed',
          color: '#f5222d',
          width: 2
        },
        itemStyle: {
          color: '#f5222d'
        },
        symbol: 'circle',
        symbolSize: 4,
        z: 2
      },
      // 3. 未来预测值 - 蓝色虚线
      {
        name: '未来预测值',
        type: 'line',
        data: props.futureDates.map((date, i) => [date, props.predictions[i]]),
        lineStyle: {
          type: 'dashed',
          color: '#1890ff',
          width: 3
        },
        itemStyle: {
          color: '#1890ff'
        },
        symbol: 'diamond',
        symbolSize: 8,
        z: 4
      },
      // 4. 置信区间上界（不显示在图例中）
      {
        name: '置信区间上界',
        type: 'line',
        data: ciUpper,
        lineStyle: {
          opacity: 0
        },
        stack: 'confidence',
        symbol: 'none',
        showSymbol: false,
        legendHoverLink: false
      },
      // 5. 置信区间 - 灰色半透明区域
      {
        name: '95%置信区间',
        type: 'line',
        data: ciLower,
        lineStyle: {
          opacity: 0
        },
        areaStyle: {
          color: 'rgba(128, 128, 128, 0.2)'
        },
        stack: 'confidence',
        symbol: 'none',
        showSymbol: false
      }
    ]
  }

  // 添加用户阈值线
  if (props.thresholdLine !== null) {
    option.series.push({
      name: '用户阈值',
      type: 'line',
      markLine: {
        silent: true,
        lineStyle: {
          type: 'dashed',
          color: '#fa8c16',
          width: 2
        },
        data: [
          {
            yAxis: props.thresholdLine,
            label: {
              formatter: `阈值: ${props.thresholdLine}`,
              position: 'end'
            }
          }
        ]
      }
    })
  }

  chartInstance.setOption(option)
}

// 响应式调整
const handleResize = () => {
  chartInstance?.resize()
}

watch(() => [props.historicalData, props.predictions], () => {
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
.advanced-trend-chart {
  width: 100%;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 500px;
}
</style>

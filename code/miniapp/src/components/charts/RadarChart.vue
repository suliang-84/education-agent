<template>
  <canvas
    :canvas-id="canvasId"
    :style="{ width: size + 'px', height: size + 'px', display: 'block' }"
  />
</template>

<script setup lang="ts">
import { getCurrentInstance, onMounted, watch } from 'vue'
import { useThemeStore } from '@/store/theme'
// @ts-ignore
import uCharts from '@qiun/ucharts/u-charts.js'

const props = withDefaults(defineProps<{
  canvasId?: string
  scores: number[]
  labels: string[]
  colors?: string[]
  size?: number
}>(), {
  canvasId: 'radarChart',
  colors: () => ['#5E8DF9', '#7C3AED', '#0EA5E9', '#10B981', '#F59E0B'],
  size: 300,
})

// getCurrentInstance() is needed so uni.createCanvasContext() can locate the
// canvas element that lives inside this component's scope. Without passing the
// component instance as the second argument, WeChat miniprogram cannot find
// the canvas and the context is invalid (silently fails to draw).
const instance = getCurrentInstance()
const theme = useThemeStore()

function draw() {
  // uCharts v2.0+ requires context to be passed explicitly.
  // For legacy canvas (canvas2d: false) we use uni.createCanvasContext().
  // The second argument is the component instance — required when the <canvas>
  // lives inside a component rather than directly on a page.
  const ctx = uni.createCanvasContext(props.canvasId, instance?.proxy)

  new uCharts({
    type: 'radar',
    canvasId: props.canvasId,
    context: ctx,
    canvas2d: false,
    width: props.size,
    height: props.size,
    pixelRatio: 1,
    background: theme.isDark ? '#0E1116' : '#FFFFFF',
    categories: props.labels,
    series: [{
      name: '五力',
      data: props.scores,
      color: theme.isDark ? '#A9BEFF' : '#5E8DF9',
    }],
    extra: {
      radar: {
        gridColor: theme.isDark ? '#2A3140' : '#E2E8F0',
        gridCount: 3,
        labelColor: theme.isDark ? '#9CA3AF' : '#64748B',
        opacity: 0.15,
        max: 100,
        labelPointShow: true,
        labelPointRadius: 3,
        labelPointColor: theme.isDark ? '#A9BEFF' : '#5E8DF9',
      },
    },
    legend: { show: false },
    padding: [20, 20, 20, 20],
  })
}

onMounted(() => {
  // Delay to ensure the canvas element has been rendered to the DOM.
  setTimeout(draw, 300)
})

watch(
  () => [props.scores, theme.isDark],
  () => {
    setTimeout(draw, 50)
  },
  { deep: true }
)
</script>

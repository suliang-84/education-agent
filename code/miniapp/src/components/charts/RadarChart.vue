<template>
  <canvas
    type="2d"
    :id="canvasId"
    :style="{ width: size + 'px', height: size + 'px', display: 'block' }"
  />
</template>

<script setup lang="ts">
/**
 * 五力雷达图 —— 外观对齐后台「训练题管理 → 详情 → 五力训练权重」的 ECharts 雷达图：
 *   · 5 圈同心多边形，相邻两圈交替淡填充（主色 2% / 6%），网格线主色 22%，轴线主色 30%
 *   · 数据区：主色 2px 描边 + 主色 25% 填充，顶点实心圆点（直径 6）
 *   · 轴标签：主色文字，前面是该维度颜色的小圆点，后面带分数（“洞察力  82”）
 * 用 2D canvas 自绘（按设备像素比放大，保证清晰），不依赖 uCharts。
 */
import { getCurrentInstance, onMounted, watch } from 'vue'
import { useThemeStore } from '@/store/theme'

const props = withDefaults(defineProps<{
  canvasId?: string
  scores: number[]      // 0–100
  labels: string[]
  colors?: string[]     // 各维度颜色（标签前的小圆点）
  size?: number
}>(), {
  canvasId: 'radarChart',
  colors: () => ['#0D9488', '#E11D48', '#0EA5E9', '#D97706', '#7C3AED'],
  size: 300,
})

const instance = getCurrentInstance()
const theme = useThemeStore()

const MAX = 100            // 分数上限
const RINGS = 5            // 同心圈数（同后台 splitNumber: 5）
const FONT = 12            // 轴标签字号（px）
const DOT = 6              // 标签前小圆点直径（同后台）
const DOT_GAP = 6          // 小圆点与文字的间距

function alpha(hex: string, a: number): string {
  const m = /^#([0-9a-f]{6})$/i.exec(hex)
  if (!m) return hex
  const n = parseInt(m[1], 16)
  return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function paint(ctx: any, w: number, h: number) {
  const primary = theme.isDark ? '#A9BEFF' : '#5E8DF9'
  const n = props.scores.length
  const cx = w / 2
  const cy = h / 2
  const ang = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / n   // 第 1 维在正上方，顺时针

  ctx.clearRect(0, 0, w, h)
  ctx.font = `${FONT}px sans-serif`
  ctx.textBaseline = 'middle'

  // 每个标签：文字 = “名称  分数”，总宽 = 圆点 + 间距 + 文字
  const texts = props.labels.map((l, i) => `${l}  ${props.scores[i] ?? 0}`)
  const textW = texts.map((t) => ctx.measureText(t).width as number)
  const labelW = textW.map((tw) => DOT + DOT_GAP + tw)

  // 半径：从大到小试，直到所有标签都完整落在画布内（左右两侧的标签最容易溢出）
  const LABEL_OFFSET = 12
  let R = Math.min(w, h) * 0.34
  for (; R > 30; R -= 2) {
    let fit = true
    for (let i = 0; i < n && fit; i++) {
      const c = Math.cos(ang(i))
      const lx = cx + (R + LABEL_OFFSET) * c
      if (c > 0.2 && lx + labelW[i] > w - 4) fit = false
      else if (c < -0.2 && lx - labelW[i] < 4) fit = false
      else if (Math.abs(c) <= 0.2 && Math.abs(lx - cx) + labelW[i] / 2 > w / 2 - 4) fit = false
    }
    if (fit) break
  }

  const pt = (i: number, r: number): [number, number] => [cx + r * Math.cos(ang(i)), cy + r * Math.sin(ang(i))]
  const polygon = (r: number) => {
    ctx.beginPath()
    for (let i = 0; i < n; i++) {
      const [x, y] = pt(i, r)
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
    }
    ctx.closePath()
  }

  // 1) 同心圈：由外向内填充，相邻圈交替 2% / 6%（最内圈 2%）
  for (let k = RINGS; k >= 1; k--) {
    polygon((R * k) / RINGS)
    ctx.fillStyle = alpha(primary, k % 2 === 1 ? 0.02 : 0.06)
    ctx.fill()
  }
  // 2) 网格线
  ctx.lineWidth = 1
  ctx.strokeStyle = alpha(primary, 0.22)
  for (let k = 1; k <= RINGS; k++) {
    polygon((R * k) / RINGS)
    ctx.stroke()
  }
  // 3) 轴线
  ctx.strokeStyle = alpha(primary, 0.3)
  for (let i = 0; i < n; i++) {
    const [x, y] = pt(i, R)
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.lineTo(x, y)
    ctx.stroke()
  }

  // 4) 数据区：填充 + 描边
  const vals = props.scores.map((s) => Math.max(0, Math.min(MAX, s ?? 0)))
  ctx.beginPath()
  vals.forEach((v, i) => {
    const [x, y] = pt(i, (R * v) / MAX)
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.closePath()
  ctx.fillStyle = alpha(primary, 0.25)
  ctx.fill()
  ctx.lineWidth = 2
  ctx.lineJoin = 'round'
  ctx.strokeStyle = primary
  ctx.stroke()

  // 5) 顶点圆点
  ctx.fillStyle = primary
  vals.forEach((v, i) => {
    const [x, y] = pt(i, (R * v) / MAX)
    ctx.beginPath()
    ctx.arc(x, y, 3, 0, Math.PI * 2)
    ctx.fill()
  })

  // 6) 轴标签：[彩色小圆点] + 主色文字
  for (let i = 0; i < n; i++) {
    const c = Math.cos(ang(i))
    const s = Math.sin(ang(i))
    const lx = cx + (R + LABEL_OFFSET) * c
    let ly = cy + (R + LABEL_OFFSET) * s
    if (s < -0.9) ly -= 4        // 正上方的标签再抬高一点，避免压到顶点
    if (s > 0.6) ly += 4         // 下方两个标签再放低一点

    // 标签整体的起点 x
    let startX: number
    if (c > 0.2) startX = lx
    else if (c < -0.2) startX = lx - labelW[i]
    else startX = lx - labelW[i] / 2

    ctx.fillStyle = props.colors[i] ?? primary
    ctx.beginPath()
    ctx.arc(startX + DOT / 2, ly, DOT / 2, 0, Math.PI * 2)
    ctx.fill()

    ctx.fillStyle = primary
    ctx.textAlign = 'left'
    ctx.fillText(texts[i], startX + DOT + DOT_GAP, ly)
  }
}

function draw() {
  uni.createSelectorQuery()
    .in(instance?.proxy)
    .select('#' + props.canvasId)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    .fields({ node: true, size: true }, (r: any) => {
      if (!r?.node) return
      const canvas = r.node
      const dpr = uni.getSystemInfoSync().pixelRatio || 1
      const w = r.width || props.size
      const h = r.height || props.size
      canvas.width = w * dpr      // 重设宽高会清空画布，同时按设备像素比放大保证清晰
      canvas.height = h * dpr
      const ctx = canvas.getContext('2d')
      ctx.scale(dpr, dpr)
      paint(ctx, w, h)
    })
    .exec()
}

onMounted(() => {
  // 等 canvas 节点渲染完成
  setTimeout(draw, 300)
})

watch(
  () => [props.scores, props.labels, theme.isDark],
  () => { setTimeout(draw, 50) },
  { deep: true },
)
</script>

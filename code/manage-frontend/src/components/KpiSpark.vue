<template>
  <svg class="spark" :viewBox="kind === 'ring' ? '0 0 60 60' : `0 0 100 ${H}`" :preserveAspectRatio="PAR[kind] ?? 'none'" aria-hidden="true">
    <defs>
      <linearGradient :id="gid" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="currentColor" stop-opacity="0.38" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
      </linearGradient>
      <linearGradient :id="`${gid}-cap`" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" style="stop-color: var(--spark-hi, #fff)" stop-opacity="0.95" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0.55" />
      </linearGradient>
      <linearGradient :id="`${gid}-ring`" gradientUnits="userSpaceOnUse" x1="14" y1="14" x2="46" y2="46">
        <stop offset="0%" style="stop-color: var(--spark-hi, #fff)" stop-opacity="1" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0.75" />
      </linearGradient>
      <linearGradient :id="`${gid}-gauge`" gradientUnits="userSpaceOnUse" x1="9" y1="0" x2="91" y2="0">
        <stop offset="0%" stop-color="currentColor" stop-opacity="0.55" />
        <stop offset="100%" style="stop-color: var(--spark-accent, var(--spark-hi, #fff))" stop-opacity="1" />
      </linearGradient>
      <linearGradient :id="`${gid}-ln`" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="100" y2="0">
        <stop offset="0%" style="stop-color: var(--spark-ln, var(--spark-hi, #fff))" stop-opacity="1" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0.85" />
      </linearGradient>
      <radialGradient :id="`${gid}-orb`" cx="0.35" cy="0.3" r="0.8">
        <stop offset="0%" style="stop-color: var(--spark-accent, var(--spark-hi, #fff))" stop-opacity="1" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0.6" />
      </radialGradient>
      <filter :id="`${gid}-sh`" x="-30%" y="-30%" width="160%" height="160%">
        <feDropShadow dx="0.6" dy="1.6" stdDeviation="1.5" style="flood-color: var(--spark-shadow, #000); flood-opacity: var(--spark-shadow-o, 0.5)" />
      </filter>
    </defs>
    <!-- 圆环：暗轨道 + 左下一段粗的圆头亮弧（白到灰渐变，带投影，像一颗胶囊） -->
    <template v-if="kind === 'ring'">
      <circle cx="30" cy="30" r="20" class="spark__track" />
      <path :d="ringArc" class="spark__arc" :stroke="`url(#${gid}-ring)`" :filter="`url(#${gid}-sh)`" />
    </template>
    <!-- 锯齿面积：折线不平滑，渐隐面积 + 白色折线 + 末点高亮 -->
    <template v-else-if="kind === 'jagged'">
      <path v-if="jaggedArea" :d="jaggedArea" :fill="`url(#${gid})`" />
      <path v-if="jaggedLine" :d="jaggedLine" class="spark__line spark__line--hi" :style="{ stroke: `url(#${gid}-ln)` }" />
      <circle v-if="pts.length" :cx="pts[pts.length - 1].x" :cy="pts[pts.length - 1].y" r="2.4" class="spark__dot" />
    </template>
    <!-- 半圆仪表盘：暗轨道 + 圆头亮弧（和圆环同款的立体质感），弧端一个亮球 -->
    <template v-else-if="kind === 'gauge'">
      <path :d="gaugeTrack" class="spark__gtrack" />
      <path :d="gaugeArc" class="spark__garc" :stroke="`url(#${gid}-gauge)`" :filter="`url(#${gid}-sh)`" />
      <circle :cx="gaugeEnd.x" :cy="gaugeEnd.y" r="4.6" class="spark__dot" />
    </template>
    <!-- 单峰面积：一座尖峰，峰顶白点 + 竖线 -->
    <template v-else-if="kind === 'peak'">
      <path v-if="area" :d="area" :fill="`url(#${gid})`" />
      <path v-if="line" :d="line" class="spark__line spark__line--hi" :style="{ stroke: `url(#${gid}-ln)` }" />
      <line v-if="pts.length" :x1="pts[hiIdx].x" :x2="pts[hiIdx].x" :y1="pts[hiIdx].y" :y2="H" class="spark__stem" />
      <circle v-if="pts.length" :cx="pts[hiIdx].x" :cy="pts[hiIdx].y" r="2.6" class="spark__dot" />
    </template>
    <!-- 一周 7 个球：周六、周日（右 2 个）又大又亮，工作日小而暗 -->
    <template v-else-if="kind === 'bubbles'">
      <circle v-for="(c, i) in bubbles" :key="i" :cx="c.x" :cy="c.y" :r="c.r"
        :fill="c.weekend ? `url(#${gid}-orb)` : 'currentColor'" :opacity="c.weekend ? 1 : 0.26 + 0.05 * i"
        :filter="c.weekend ? `url(#${gid}-sh)` : undefined" />
    </template>
    <!-- 起伏面积：带竖边的渐隐面积块，上沿是平滑起伏的 W 形，沿线一条粗而亮的白线 -->
    <template v-else-if="kind === 'swing'">
      <path v-if="area" :d="area" :fill="`url(#${gid})`" />
      <path v-if="line" :d="line" class="spark__line spark__line--hi spark__line--thick" :style="{ stroke: `url(#${gid}-ln)` }" :filter="`url(#${gid}-sh)`" />
    </template>
    <!-- 面积折线 -->
    <template v-else-if="kind === 'line'">
      <path v-if="area" :d="area" :fill="`url(#${gid})`" />
      <path v-if="line" :d="line" class="spark__line" />
    </template>
    <!-- 柱 / 对称波形 / 点阵：每个点一根 -->
    <template v-else>
      <template v-for="(b, i) in bars" :key="i">
        <!-- 点阵柱：圆角小方块一列一列往上码成阶梯，越靠右越亮；值为 0 的列只留底部一格淡色；最后一列顶上一颗白色高光 -->
        <template v-if="kind === 'dots'">
          <rect v-for="r in Math.max(1, b.dots)" :key="r" :x="b.x" :y="H - 4 - r * b.cell" :width="b.w" :height="b.w" :rx="b.w * 0.3"
            :fill="i === hiIdx && r === b.dots ? `url(#${gid}-cap)` : 'currentColor'"
            :opacity="b.v <= 0 ? 0.14 : (i === hiIdx && r === b.dots ? 1 : 0.36 + 0.5 * (i / Math.max(1, bars.length - 1)))" />
        </template>
        <template v-else-if="kind === 'bars'">
          <!-- 蜡烛：细影线 + 胶囊实体，高亮一根；值为 0 的画成一小段横线 -->
          <line v-if="b.v > 0" :x1="b.x + b.w / 2" :x2="b.x + b.w / 2" :y1="b.y - 5" :y2="b.y + b.h + 5" class="spark__wick" />
          <rect v-if="b.v > 0" :x="b.x" :y="b.y" :width="b.w" :height="b.h" :rx="b.w / 2" :fill="i === hiIdx ? 'var(--spark-hi, #fff)' : `url(#${gid}-cap)`" :opacity="i === hiIdx ? 0.95 : 0.85" />
          <rect v-else :x="b.x" :y="H - 12" :width="b.w" height="1.6" rx="0.8" class="spark__fill" opacity="0.4" />
        </template>
        <rect v-else :x="b.x" :y="b.y" :width="b.w" :height="b.h" :rx="Math.min(1.2, b.w / 2)" :opacity="b.v > 0 ? 0.3 + 0.7 * b.k : 0.12" class="spark__fill" :class="{ 'spark__last': i === hiIdx }" />
      </template>
    </template>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 统计卡右侧的装饰图：固定形状，不随统计数据变化（参考设计稿）。
// kind：gauge = 半圆仪表盘；peak = 单峰面积；bubbles = 一周 7 个球；swing = 起伏面积（W 形）；line = 平滑面积折线；jagged = 锯齿面积折线；bars = 蜡烛柱；wave = 上下对称的柱（像声波）；dots = 点阵柱（阶梯）；ring = 圆环
const props = defineProps<{ kind: 'line' | 'jagged' | 'bars' | 'wave' | 'dots' | 'ring' | 'gauge' | 'peak' | 'bubbles' | 'swing'; gid: string }>()

// 点阵柱要更高的画布，方块才能放大、间隙才放得下
const W = 100, H = props.kind === 'dots' ? 72 : 60
// 各图案的画布缩放方式：需要保持正圆 / 正方的用 meet，其余拉伸铺满
const PAR: Record<string, string> = { ring: 'xMidYMid meet', dots: 'xMaxYMax meet', gauge: 'xMidYMid meet', bubbles: 'xMaxYMid meet' }
const PRESET: Record<string, number[]> = {
  swing:  [9, 8, 4, 1, 3, 6, 6, 4, 5, 8, 10],
  peak:   Array.from({ length: 41 }, (_, i) => 1 + 9 * Math.exp(-(((i - 26) / 6.4) ** 2))),
  line:   [8, 6, 3, 2, 4, 7, 5, 3, 5, 8],
  jagged: [2, 3.5, 2.5, 5, 4, 6.5, 5.5, 8, 6.5, 9],
  bars:   [3, 6, 10, 7, 0],
  wave:   [2, 4, 6, 8, 10, 8, 6, 4, 2],
  dots:   [0, 1, 1, 2, 3, 4],
  ring:   [],
}
// 圆环亮弧：从 5 点钟方向顺时针转到 10 点钟方向（经过 6、7、8、9 点），约占四成；角度从 12 点起顺时针计
const RING_FROM = 150, RING_SPAN = 150
const ringArc = (() => {
  const pt = (deg: number) => { const r = Math.PI * deg / 180; return `${(30 + 20 * Math.sin(r)).toFixed(2)} ${(30 - 20 * Math.cos(r)).toFixed(2)}` }
  return `M${pt(RING_FROM)} A20 20 0 ${RING_SPAN > 180 ? 1 : 0} 1 ${pt(RING_FROM + RING_SPAN)}`
})()
const nums = computed(() => PRESET[props.kind] ?? [])
const max = computed(() => Math.max(1, ...nums.value))
// 高亮的那一个：声波取最高的一根，蜡烛取最后一根有值的，点阵取最后一列
const hiIdx = computed(() => {
  const a = nums.value
  if (props.kind === 'wave' || props.kind === 'peak') return a.indexOf(Math.max(...a))
  if (props.kind === 'bars') { for (let i = a.length - 1; i >= 0; i--) if (a[i] > 0) return i }
  return a.length - 1
})

const pts = computed(() => {
  const vals = nums.value
  const n = vals.length
  if (n < 2) return []
  const lo = Math.min(...vals), hi = Math.max(...vals)
  const span = hi - lo || 1
  return vals.map((v, i) => ({ x: (i / (n - 1)) * W, y: H - 6 - ((v - lo) / span) * (H - 14) }))
})
// 折线用中点二次贝塞尔做平滑
const line = computed(() => {
  const p = pts.value
  if (p.length < 2) return ''
  let d = `M${p[0].x},${p[0].y}`
  for (let i = 1; i < p.length; i++) { const mx = (p[i - 1].x + p[i].x) / 2; d += ` C${mx},${p[i - 1].y} ${mx},${p[i].y} ${p[i].x},${p[i].y}` }
  return d
})
// 锯齿折线：直线段连接
const jaggedLine = computed(() => (pts.value.length < 2 ? '' : 'M' + pts.value.map(q => `${q.x},${q.y}`).join(' L')))
const jaggedArea = computed(() => (jaggedLine.value ? `${jaggedLine.value} L${pts.value[pts.value.length - 1].x},${H} L${pts.value[0].x},${H} Z` : ''))
const area = computed(() => (line.value ? `${line.value} L${pts.value[pts.value.length - 1].x},${H} L${pts.value[0].x},${H} Z` : ''))

// 半圆仪表盘（圆心 50,54 半径 41，线宽 12）：从左端沿上半圆走到 t（0-1）
const GAUGE_T = 0.62
const gp = (t: number, r = 41) => ({ x: 50 + r * Math.cos(Math.PI * (1 - t)), y: 54 - r * Math.sin(Math.PI * (1 - t)) })
const gaugeEnd = gp(GAUGE_T)
const gaugeTrack = `M${gp(0).x} ${gp(0).y} A41 41 0 0 1 ${gp(1).x} ${gp(1).y}`
const gaugeArc = `M${gp(0).x} ${gp(0).y} A41 41 0 0 1 ${gaugeEnd.x.toFixed(2)} ${gaugeEnd.y.toFixed(2)}`
// 一周 7 个球：左 5 个是工作日（小、暗），右 2 个是周六、周日（大、亮）
const bubbles = [
  { x: 6, y: 38, r: 4.5, weekend: false }, { x: 18, y: 33, r: 5.5, weekend: false }, { x: 30, y: 37, r: 5, weekend: false },
  { x: 42, y: 30, r: 6.5, weekend: false }, { x: 54, y: 34, r: 6, weekend: false },
  { x: 73, y: 29, r: 14.5, weekend: true }, { x: 93, y: 35, r: 9.5, weekend: true },
]
const bars = computed(() => {
  const n = nums.value.length
  if (!n) return []
  const slot = W / n
  const w = props.kind === 'dots' ? Math.max(3, Math.min(12, slot * 0.72)) : props.kind === 'bars' ? Math.max(3, Math.min(7, slot * 0.5)) : Math.max(1.6, Math.min(7, slot * 0.55))
  return nums.value.map((v, i) => {
    const k = v / max.value
    const x = i * slot + (slot - w) / 2
    if (props.kind === 'wave') { const h = Math.max(3, k * (H - 4)); return { x, y: (H - h) / 2, w, h, v, k } }
    if (props.kind === 'dots') { const cell = w + 4.6; return { x, y: 0, w, h: 0, v, k, cell, dots: v } }
    // 蜡烛：高度随数值，位置也随数值上移，错落有致
    const h = 9 + k * 12; return { x, y: H - 16 - k * (H - 40) - h / 2, w, h, v, k }
  })
})
</script>

<style scoped lang="scss">
.spark { display: block; width: 100%; height: 100%; color: var(--spark, #8b9bff); overflow: visible;
  &__track { fill: none; stroke: currentColor; stroke-width: 8; opacity: 0.16; }
  &__arc { fill: none; stroke-width: 11; stroke-linecap: round; }
  &__dot { fill: var(--spark-accent, var(--spark-hi, #fff)); }
  &__gtrack { fill: none; stroke: currentColor; stroke-width: 12; stroke-linecap: round; opacity: 0.14; }
  &__garc { fill: none; stroke-width: 12; stroke-linecap: round; }
  &__stem { stroke: var(--spark-accent, var(--spark-hi, #fff)); stroke-width: 1; stroke-dasharray: 2 2; opacity: 0.5; vector-effect: non-scaling-stroke; }
  &__line--thick { stroke-width: 2.4 !important; }
  &__line--hi { stroke-width: 1.8; stroke-linejoin: round; opacity: 1; }
  &__line { fill: none; stroke: currentColor; stroke-width: 1.6; vector-effect: non-scaling-stroke; stroke-linecap: round; opacity: 0.9; }
  &__fill { fill: currentColor; }
  &__wick { stroke: currentColor; stroke-width: 1; vector-effect: non-scaling-stroke; opacity: 0.55; }
  &__last { fill: var(--spark-hi, #fff); opacity: 1 !important; } }
</style>

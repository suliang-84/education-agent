<template>
  <svg class="spark" :viewBox="kind === 'ring' || kind === 'dial' ? '0 0 60 60' : `0 0 100 ${H}`" :preserveAspectRatio="PAR[kind] ?? 'none'" aria-hidden="true">
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
      <linearGradient :id="`${gid}-ln`" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="100" y2="0">
        <stop offset="0%" style="stop-color: var(--spark-ln, var(--spark-hi, #fff))" stop-opacity="1" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0.85" />
      </linearGradient>
      <!-- 秒表扫过的扇形：从 12 点方向的透明，渐变到指针处的高亮 -->
      <linearGradient :id="`${gid}-sweep`" gradientUnits="userSpaceOnUse" :x1="30" :y1="30 - DIAL_R" :x2="dialEnd.x" :y2="dialEnd.y">
        <stop offset="0%" stop-color="currentColor" stop-opacity="0" />
        <stop offset="100%" style="stop-color: var(--spark-accent, var(--spark-hi, #fff))" stop-opacity="0.55" />
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
      <circle cx="30" cy="30" :r="RING_R" class="spark__track" />
      <path :d="ringArc" class="spark__arc" :stroke="`url(#${gid}-ring)`" :filter="`url(#${gid}-sh)`" />
    </template>
    <!-- 秒表：外圈 + 12 个刻度 + 一道扫过的扇形 + 指针，指针末端一颗亮球 -->
    <template v-else-if="kind === 'dial'">
      <circle cx="30" cy="30" r="27.5" class="spark__rim" />
      <line v-for="(t, i) in dialTicks" :key="i" :x1="t.x1" :y1="t.y1" :x2="t.x2" :y2="t.y2" class="spark__tick" :style="{ opacity: t.major ? 0.6 : 0.28 }" />
      <path :d="dialWedge" :fill="`url(#${gid}-sweep)`" />
      <line x1="30" y1="30" :x2="dialEnd.x" :y2="dialEnd.y" class="spark__hand" />
      <circle :cx="dialEnd.x" :cy="dialEnd.y" r="3.6" :fill="`url(#${gid}-orb)`" :filter="`url(#${gid}-sh)`" />
      <circle cx="30" cy="30" r="2.2" class="spark__dot" />
    </template>
    <!-- 层叠山峰：后层暗、前层亮，最高峰顶一个带光晕的亮点 + 虚线 -->
    <template v-else-if="kind === 'ridge'">
      <path :d="ridgeBack" :fill="`url(#${gid})`" opacity="0.55" />
      <path :d="ridgeBackLine" class="spark__ridge-back" />
      <path :d="ridgeFront" :fill="`url(#${gid})`" />
      <line :x1="RIDGE_PEAK.x" :x2="RIDGE_PEAK.x" :y1="RIDGE_PEAK.y" :y2="H" class="spark__stem" />
      <path :d="ridgeFrontLine" class="spark__line spark__line--hi" :style="{ stroke: `url(#${gid}-ln)` }" />
      <circle :cx="RIDGE_PEAK.x" :cy="RIDGE_PEAK.y" r="7.5" class="spark__halo" />
      <circle :cx="RIDGE_PEAK.x" :cy="RIDGE_PEAK.y" r="2.8" class="spark__dot" />
    </template>
    <!-- 层叠波浪：三层半透明的正弦波，最前一层带亮线 -->
    <template v-else-if="kind === 'tide'">
      <path v-for="(w, i) in tide" :key="i" :d="w.fill" :fill="`url(#${gid})`" :opacity="w.opacity" />
      <path :d="tide[1].line" class="spark__tide-mid" />
      <path :d="tide[2].line" class="spark__line spark__line--hi" :style="{ stroke: `url(#${gid}-ln)` }" />
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
// kind：ring = 圆环；dial = 秒表；ridge = 层叠山峰；tide = 层叠波浪；bubbles = 一周 7 个球；swing = 起伏面积（W 形）；
//       bars = 蜡烛柱；wave = 上下对称的柱（像声波）；dots = 点阵柱（阶梯）
const props = defineProps<{ kind: 'ring' | 'dial' | 'ridge' | 'tide' | 'bubbles' | 'swing' | 'bars' | 'wave' | 'dots'; gid: string }>()

// 画布高度：点阵柱用正方形（容器约 95×94，5 列 × 最高 5 层），层叠山峰略高；其余 60
const W = 100, H = props.kind === 'dots' ? 100 : props.kind === 'ridge' ? 72 : 60
// 各图案的画布缩放方式：需要保持正圆 / 正方的用 meet 且居中，其余拉伸铺满
const PAR: Record<string, string> = { ring: 'xMidYMid meet', dial: 'xMidYMid meet', dots: 'xMidYMid meet', bubbles: 'xMidYMid meet', ridge: 'xMidYMid meet' }
const PRESET: Record<string, number[]> = {
  swing: [9, 8, 4, 1, 3, 6, 6, 4, 5, 8, 10],
  bars:  [3, 6, 10, 7, 0],
  wave:  [2, 4, 6, 8, 10, 8, 6, 4, 2],
  dots:  [0, 1, 2, 3, 5],
}
const nums = computed(() => PRESET[props.kind] ?? [])
const max = computed(() => Math.max(1, ...nums.value))
// 高亮的那一个：声波取最高的一根，蜡烛取最后一根有值的，点阵取最后一列
const hiIdx = computed(() => {
  const a = nums.value
  if (props.kind === 'wave') return a.indexOf(Math.max(...a))
  if (props.kind === 'bars') { for (let i = a.length - 1; i >= 0; i--) if (a[i] > 0) return i }
  return a.length - 1
})

// ── 圆环亮弧：从 5 点钟方向顺时针转到 10 点钟方向（经过 6、7、8、9 点），约占四成；角度从 12 点起顺时针计
const RING_FROM = 150, RING_SPAN = 150
const RING_R = 22   // 画布 60×60，半径 + 半线宽 ≤ 30
const polar = (cx: number, cy: number, r: number, deg: number) => { const a = Math.PI * deg / 180; return { x: cx + r * Math.sin(a), y: cy - r * Math.cos(a) } }
const ringArc = (() => {
  const a = polar(30, 30, RING_R, RING_FROM), b = polar(30, 30, RING_R, RING_FROM + RING_SPAN)
  return `M${a.x.toFixed(2)} ${a.y.toFixed(2)} A${RING_R} ${RING_R} 0 ${RING_SPAN > 180 ? 1 : 0} 1 ${b.x.toFixed(2)} ${b.y.toFixed(2)}`
})()

// ── 秒表：12 个刻度（每 90° 一个长刻度）；扇形从 12 点扫到 DIAL_DEG，指针停在扫过的边缘
const DIAL_R = 21, DIAL_DEG = 125
const dialEnd = polar(30, 30, DIAL_R, DIAL_DEG)
const dialWedge = `M30 30 L30 ${30 - DIAL_R} A${DIAL_R} ${DIAL_R} 0 0 1 ${dialEnd.x.toFixed(2)} ${dialEnd.y.toFixed(2)} Z`
const dialTicks = Array.from({ length: 12 }, (_, i) => {
  const major = i % 3 === 0
  const a = polar(30, 30, major ? 22.6 : 24.2, i * 30), b = polar(30, 30, 26, i * 30)
  return { x1: a.x, y1: a.y, x2: b.x, y2: b.y, major }
})

// ── 层叠山峰（画布 100×72）：后层山脊 + 前层山脊，最高峰在前层
const RIDGE_PEAK = { x: 62, y: 12 }
const ridgeLine = (pts: number[][]) => 'M' + pts.map(p => p.join(' ')).join(' L')
const ridgeBackPts = [[0, 52], [16, 36], [28, 45], [44, 19], [60, 41], [72, 32], [100, 55]]
const ridgeFrontPts = [[0, 64], [22, 43], [38, 55], [RIDGE_PEAK.x, RIDGE_PEAK.y], [82, 46], [100, 64]]
const ridgeBackLine = ridgeLine(ridgeBackPts)
const ridgeFrontLine = ridgeLine(ridgeFrontPts)
const ridgeBack = `${ridgeBackLine} L100 72 L0 72 Z`
const ridgeFront = `${ridgeFrontLine} L100 72 L0 72 Z`

// ── 层叠波浪（画布 100×60）：三层正弦波，越靠前越低、越实
const tide = [
  { base: 30, amp: 7, period: 62, phase: 0.4, opacity: 0.45 },
  { base: 38, amp: 7, period: 48, phase: 1.8, opacity: 0.7 },
  { base: 46, amp: 6, period: 40, phase: 3.3, opacity: 1 },
].map(w => {
  const pts: string[] = []
  for (let x = 0; x <= 100; x += 2.5) pts.push(`${x} ${(w.base + w.amp * Math.sin((2 * Math.PI * x) / w.period + w.phase)).toFixed(2)}`)
  const line = 'M' + pts.join(' L')
  return { line, fill: `${line} L100 60 L0 60 Z`, opacity: w.opacity }
})

// ── 起伏面积（W 形）：折线用中点三次贝塞尔做平滑
const pts = computed(() => {
  const vals = nums.value
  const n = vals.length
  if (n < 2) return []
  const lo = Math.min(...vals), hi = Math.max(...vals)
  const span = hi - lo || 1
  return vals.map((v, i) => ({ x: (i / (n - 1)) * W, y: H - 6 - ((v - lo) / span) * (H - 14) }))
})
const line = computed(() => {
  const p = pts.value
  if (p.length < 2) return ''
  let d = `M${p[0].x},${p[0].y}`
  for (let i = 1; i < p.length; i++) { const mx = (p[i - 1].x + p[i].x) / 2; d += ` C${mx},${p[i - 1].y} ${mx},${p[i].y} ${p[i].x},${p[i].y}` }
  return d
})
const area = computed(() => (line.value ? `${line.value} L${pts.value[pts.value.length - 1].x},${H} L${pts.value[0].x},${H} Z` : ''))

// ── 一周 7 个球：左 5 个是工作日（小、暗），右 2 个是周六、周日（大、亮）
const bubbles = [
  { x: 6, y: 38, r: 4.5, weekend: false }, { x: 18, y: 33, r: 5.5, weekend: false }, { x: 30, y: 37, r: 5, weekend: false },
  { x: 42, y: 30, r: 6.5, weekend: false }, { x: 54, y: 34, r: 6, weekend: false },
  { x: 73, y: 29, r: 14.5, weekend: true }, { x: 93, y: 35, r: 9.5, weekend: true },
]

// ── 蜡烛 / 声波 / 点阵：每个点一根
const bars = computed(() => {
  const n = nums.value.length
  if (!n) return []
  const slot = W / n
  const w = props.kind === 'dots' ? Math.max(3, Math.min(14, slot * 0.72)) : props.kind === 'bars' ? Math.max(3, Math.min(7, slot * 0.5)) : Math.max(1.6, Math.min(7, slot * 0.55))
  return nums.value.map((v, i) => {
    const k = v / max.value
    const x = i * slot + (slot - w) / 2
    if (props.kind === 'wave') { const h = Math.max(3, k * (H - 4)); return { x, y: (H - h) / 2, w, h, v, k } }
    if (props.kind === 'dots') { const cell = w + 4.2; return { x, y: 0, w, h: 0, v, k, cell, dots: v } }
    // 蜡烛：高度随数值，位置也随数值上移，错落有致
    const h = 9 + k * 12; return { x, y: H - 16 - k * (H - 40) - h / 2, w, h, v, k }
  })
})
</script>

<style scoped lang="scss">
.spark { display: block; width: 100%; height: 100%; color: var(--spark, #8b9bff); overflow: visible;
  &__track { fill: none; stroke: currentColor; stroke-width: 6; opacity: 0.16; }
  &__arc { fill: none; stroke-width: 8.5; stroke-linecap: round; }
  &__rim { fill: none; stroke: currentColor; stroke-width: 1; opacity: 0.3; }
  &__tick { stroke: currentColor; stroke-width: 1.3; stroke-linecap: round; }
  &__hand { stroke: var(--spark-accent, var(--spark-hi, #fff)); stroke-width: 1.8; stroke-linecap: round; }
  &__dot { fill: var(--spark-accent, var(--spark-hi, #fff)); }
  &__halo { fill: var(--spark-accent, var(--spark-hi, #fff)); opacity: 0.2; }
  &__ridge-back { fill: none; stroke: currentColor; stroke-width: 1; stroke-linejoin: round; opacity: 0.35; vector-effect: non-scaling-stroke; }
  &__tide-mid { fill: none; stroke: currentColor; stroke-width: 1; opacity: 0.4; vector-effect: non-scaling-stroke; }
  &__stem { stroke: var(--spark-accent, var(--spark-hi, #fff)); stroke-width: 1; stroke-dasharray: 2 2; opacity: 0.5; vector-effect: non-scaling-stroke; }
  &__line--thick { stroke-width: 2.4 !important; }
  &__line--hi { stroke-width: 1.8; stroke-linejoin: round; opacity: 1; }
  &__line { fill: none; stroke: currentColor; stroke-width: 1.6; vector-effect: non-scaling-stroke; stroke-linecap: round; opacity: 0.9; }
  &__fill { fill: currentColor; }
  &__wick { stroke: currentColor; stroke-width: 1; vector-effect: non-scaling-stroke; opacity: 0.55; }
  &__last { fill: var(--spark-hi, #fff); opacity: 1 !important; } }
</style>

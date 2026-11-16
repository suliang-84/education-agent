<template>
  <svg class="spark" viewBox="0 0 100 60" preserveAspectRatio="none" aria-hidden="true">
    <defs>
      <linearGradient :id="gid" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="currentColor" stop-opacity="0.38" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
      </linearGradient>
      <linearGradient :id="`${gid}-cap`" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" style="stop-color: var(--spark-hi, #fff)" stop-opacity="0.95" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0.55" />
      </linearGradient>
    </defs>
    <!-- 面积折线 -->
    <template v-if="kind === 'line'">
      <path v-if="area" :d="area" :fill="`url(#${gid})`" />
      <path v-if="line" :d="line" class="spark__line" />
    </template>
    <!-- 柱 / 对称波形 / 点阵：每个点一根 -->
    <template v-else>
      <template v-for="(b, i) in bars" :key="i">
        <rect v-if="kind === 'dots'" :x="b.x" :y="b.y" :width="b.w" :height="b.w * 2.5" :rx="b.w" :opacity="b.v > 0 ? 0.25 + 0.75 * b.k : 0.14" class="spark__fill" :class="{ 'spark__last': i === bars.length - 1 && b.v > 0 }" />
        <template v-else-if="kind === 'bars'">
          <!-- 蜡烛：细影线 + 胶囊实体，最后一根最亮；没有数据的点画成一小段横线 -->
          <line v-if="b.v > 0" :x1="b.x + b.w / 2" :x2="b.x + b.w / 2" :y1="b.y - 5" :y2="b.y + b.h + 5" class="spark__wick" />
          <rect v-if="b.v > 0" :x="b.x" :y="b.y" :width="b.w" :height="b.h" :rx="b.w / 2" :fill="i === bars.length - 1 ? 'var(--spark-hi, #fff)' : `url(#${gid}-cap)`" :opacity="i === bars.length - 1 ? 0.95 : 0.85" />
          <rect v-else :x="b.x" :y="H - 12" :width="b.w" height="1.6" rx="0.8" class="spark__fill" opacity="0.4" />
        </template>
        <rect v-else :x="b.x" :y="b.y" :width="b.w" :height="b.h" :rx="Math.min(1.2, b.w / 2)" :opacity="b.v > 0 ? 0.3 + 0.7 * b.k : 0.12" class="spark__fill" :class="{ 'spark__last': i === bars.length - 1 && b.v > 0 }" />
      </template>
    </template>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// kind：line = 面积折线；bars = 底部柱；wave = 上下对称的柱（像声波）；dots = 点阵
const props = defineProps<{ values: (number | null)[]; kind: 'line' | 'bars' | 'wave' | 'dots'; gid: string }>()

const W = 100, H = 60
const nums = computed(() => props.values.map(v => v ?? 0))
const max = computed(() => Math.max(1, ...nums.value))

const pts = computed(() => {
  const n = props.values.length
  const vals = props.values
  const real = vals.filter((v): v is number => v !== null)
  if (real.length < 2) return []
  const lo = Math.min(...real), hi = Math.max(...real)
  const span = hi - lo || 1
  return vals.map((v, i) => (v === null ? null : { x: n === 1 ? W / 2 : (i / (n - 1)) * W, y: H - 6 - ((v - lo) / span) * (H - 14) })).filter((p): p is { x: number; y: number } => p !== null)
})
// 折线用中点二次贝塞尔做平滑
const line = computed(() => {
  const p = pts.value
  if (p.length < 2) return ''
  let d = `M${p[0].x},${p[0].y}`
  for (let i = 1; i < p.length; i++) { const mx = (p[i - 1].x + p[i].x) / 2; d += ` C${mx},${p[i - 1].y} ${mx},${p[i].y} ${p[i].x},${p[i].y}` }
  return d
})
const area = computed(() => (line.value ? `${line.value} L${pts.value[pts.value.length - 1].x},${H} L${pts.value[0].x},${H} Z` : ''))

const bars = computed(() => {
  const n = nums.value.length
  if (!n) return []
  const slot = W / n
  const w = props.kind === 'bars' ? Math.max(3, Math.min(7, slot * 0.5)) : Math.max(1.6, Math.min(7, slot * 0.55))
  return nums.value.map((v, i) => {
    const k = v / max.value
    const x = i * slot + (slot - w) / 2
    if (props.kind === 'wave') { const h = Math.max(3, k * (H - 4)); return { x, y: (H - h) / 2, w, h, v, k } }
    if (props.kind === 'dots') return { x, y: H / 2 - w * 1.25, w, h: 0, v, k }
    // 蜡烛：高度随数值，位置也随数值上移，错落有致
    const h = 9 + k * 12; return { x, y: H - 16 - k * (H - 40) - h / 2, w, h, v, k }
  })
})
</script>

<style scoped lang="scss">
.spark { display: block; width: 100%; height: 100%; color: var(--spark, #8b9bff); overflow: visible;
  &__line { fill: none; stroke: currentColor; stroke-width: 1.6; vector-effect: non-scaling-stroke; stroke-linecap: round; opacity: 0.9; }
  &__fill { fill: currentColor; }
  &__wick { stroke: currentColor; stroke-width: 1; vector-effect: non-scaling-stroke; opacity: 0.55; }
  &__last { fill: var(--spark-hi, #fff); opacity: 1 !important; } }
</style>

<template>
  <div class="gs" :style="{ '--gc': color }">
    <svg class="gs__svg" viewBox="0 0 300 100" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient :id="`${gid}-ln`" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" :stop-color="color" stop-opacity="0.7" />
          <stop offset="100%" style="stop-color: var(--gs-hi)" stop-opacity="0.95" />
        </linearGradient>
        <linearGradient :id="`${gid}-area`" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="color" stop-opacity="0.34" />
          <stop offset="100%" :stop-color="color" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path v-if="ok" :d="areaD" :style="{ fill: `url(#${gid}-area)` }" class="gs__area" />
      <line v-if="ok" x1="0" x2="300" :y1="avgY" :y2="avgY" class="gs__avg" />
      <path v-if="ok" :d="lineD" class="gs__glow" :stroke="color" />
      <path v-if="ok" :d="lineD" class="gs__line" :stroke="`url(#${gid}-ln)`" />
    </svg>
    <template v-if="ok">
      <span class="gs__dot" :style="{ left: '0%', top: startY + '%' }" />
      <span class="gs__dot" :style="{ left: '100%', top: endY + '%' }" />
      <span class="gs__tip">{{ tip }}</span>
    </template>
    <div v-else class="gs__empty">暂无趋势数据</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 发光折线：只画最近 hl 天（起点到终点两个环形标记之间）并放大铺满整张图，带增量标签；其余（更早的数据、背景淡线、虚线基准、高亮底带）都不画。
// 线条画在拉伸的 SVG 里，标记 / 标签用 HTML 叠在上面，避免被拉变形。
const props = withDefaults(defineProps<{ values: number[]; color?: string; hl?: number; gid: string; unit?: string; tipPrefix?: string; soft?: number; env?: number }>(), { color: '#8b7cf6', hl: 14, unit: '', tipPrefix: '近 14 天', soft: 6, env: 0 })
// env 是画线前的滑动平均窗口（前后各几天）：0 = 每天的原始值；越大线越像缓坡。两张图取不同的 soft / env，趋势形状就不会一致
// soft 是曲线柔和度（越小拐弯越尖、越大越圆），两张图取不同值，形状上拉开差别

// 只画最近 hl 天（默认 14 天，含起点那天）这一段并放大到铺满整张图；更早的数据不画
const vals = computed(() => props.values.slice(-(props.hl + 1)))
const n = computed(() => vals.value.length)
const total = computed(() => vals.value.reduce((a, v) => a + (v || 0), 0))
const ok = computed(() => n.value > 2 && total.value > 0)
const gain = computed(() => vals.value.slice(1).reduce((a, v) => a + (v || 0), 0))   // 不含起点那天的合计
const tip = computed(() => `${props.tipPrefix} +${gain.value}${props.unit}`)

// 主线：每天的原始值（不是累计），每天一个起伏点；纵轴按这一段的最低 ~ 最高拉满上下空间（最低值贴着底部），再轻微下压让中间值偏低一点，线不会整体偏高、右下角不会空出一块
const PAD_T = 36, PAD_B = 12
// 画线用的值：按 env 做滑动平均；平均线（虚线）和增量标签仍用真实的每日值
const shown = computed(() => vals.value.map((_, i) => { const a = Math.max(0, i - props.env), b = Math.min(n.value - 1, i + props.env); let t = 0; for (let j = a; j <= b; j++) t += vals.value[j] || 0; return t / (b - a + 1) }))
const top = computed(() => Math.max(1, ...shown.value))
const low = computed(() => Math.min(...shown.value))
const X = (i: number) => (i / (n.value - 1)) * 300
const Y = (v: number) => PAD_T + (1 - (v - low.value) / Math.max(1e-6, top.value - low.value)) ** 1.15 * (100 - PAD_T - PAD_B)
const pts = computed(() => shown.value.map((v, i) => [X(i), Y(v)] as const))
// Catmull-Rom → 三次贝塞尔：过每个点的平滑曲线；控制点的 y 夹在图框内，避免冲出上下边
const clampY = (y: number) => Math.min(100 - PAD_B + 4, Math.max(PAD_T - 4, y))
function smooth(p: readonly (readonly [number, number])[]) {
  let d = `M${p[0][0].toFixed(2)},${p[0][1].toFixed(2)}`
  const k = props.soft
  for (let i = 0; i < p.length - 1; i++) {
    const p0 = p[i - 1] ?? p[i], p1 = p[i], p2 = p[i + 1], p3 = p[i + 2] ?? p[i + 1]
    d += ` C${(p1[0] + (p2[0] - p0[0]) / k).toFixed(2)},${clampY(p1[1] + (p2[1] - p0[1]) / k).toFixed(2)} ${(p2[0] - (p3[0] - p1[0]) / k).toFixed(2)},${clampY(p2[1] - (p3[1] - p1[1]) / k).toFixed(2)} ${p2[0].toFixed(2)},${p2[1].toFixed(2)}`
  }
  return d
}
const lineD = computed(() => smooth(pts.value))
const avgY = computed(() => Y(total.value / n.value))   // 平均线：这一段每天的平均水平
// 折线以下的面积：沿线填到图底，颜色从线向下渐隐到透明
const areaD = computed(() => { const p = pts.value; return p.length < 2 ? '' : `${lineD.value} L${p[p.length - 1][0].toFixed(2)},100 L${p[0][0].toFixed(2)},100 Z` })
const startY = computed(() => pts.value[0]?.[1] ?? 50)
const endY = computed(() => pts.value[pts.value.length - 1]?.[1] ?? 50)
</script>

<style scoped>
.gs { --gs-hi: #fff; position: relative; width: calc(100% - 24px); margin-left: 12px; height: 100%; }   /* 右侧留 12px（圆环半径 5 + 外圈 3 + 余量）：终点圆环有一半在 100% 之外，父级的渐隐蒙版会把它裁掉 */
:global(html[data-theme="light"]) .gs { --gs-hi: var(--gc); }
.gs__svg { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.gs__svg path, .gs__svg line { fill: none; vector-effect: non-scaling-stroke; stroke-linecap: round; stroke-linejoin: round; }
.gs__svg .gs__area { stroke: none; }
.gs__avg { stroke: var(--text-2); stroke-width: 1; stroke-dasharray: 3 4; opacity: 0.55; }
.gs__line { stroke-width: 1.3; }
.gs__glow { stroke-width: 6; opacity: 0.28; filter: blur(3px); }
.gs__dot { position: absolute; width: 10px; height: 10px; margin: -5px 0 0 -5px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 3px color-mix(in srgb, var(--gc) 55%, transparent), 0 0 6px var(--gc); }
.gs__dot::after { content: ''; position: absolute; inset: 2.5px; border-radius: 50%; background: var(--gc); }
.gs__tip { position: absolute; top: 0; right: 0; font-size: 12.5px; line-height: 24px; white-space: nowrap; color: var(--text-1); letter-spacing: 0.02em; font-variant-numeric: tabular-nums; }
.gs__empty { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 12px; color: var(--text-3); }
</style>

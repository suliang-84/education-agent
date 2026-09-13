<template>
  <div class="page-root">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="$router.push('/dashboard')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回看板
        </el-button>
        <div>
          <h1 class="page-title">AI 助教效果分析</h1>
          <p class="page-subtitle">理解突破、策略有效性与对话量趋势分析</p>
        </div>
      </div>
      <el-radio-group v-model="days" size="small" @change="loadData">
        <el-radio-button :value="7">近7天</el-radio-button>
        <el-radio-button :value="30">近30天</el-radio-button>
      </el-radio-group>
    </div>

    <div v-loading="loading">

      <!-- 关键指标 -->
      <div class="surface kpi-strip" v-if="data">
        <div class="kpi-item">
          <span class="kpi-val num" style="color:var(--indigo)">{{ data.summary.aha_total }}</span>
          <span class="kpi-lbl">理解突破（aha）次数</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num" style="color:var(--green)">{{ data.summary.avg_rounds.toFixed(1) }}</span>
          <span class="kpi-lbl">平均每会话对话轮数</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num" style="color:var(--amber)">{{ (data.summary.breakthrough_rate * 100).toFixed(0) }}%</span>
          <span class="kpi-lbl">突破率（aha/总会话）</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num" style="color:var(--teal)">{{ (data.summary.review_breakthrough_rate * 100).toFixed(0) }}%</span>
          <span class="kpi-lbl">错题复盘突破率</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num" style="color:var(--text-3)">{{ (data.summary.silence_rate * 100).toFixed(0) }}%</span>
          <span class="kpi-lbl">沉默模式触发率</span>
        </div>
      </div>

      <!-- 会话模式分布 + 策略有效性 -->
      <div class="two-cols">

        <!-- 会话模式饼图 -->
        <div class="surface chart-card">
          <div class="section-hd">
            <span class="section-title">会话模式分布</span>
          </div>
          <div ref="modeRef" style="height:260px;margin-top:12px" />
        </div>

        <!-- 策略有效性排名 -->
        <div class="surface chart-card">
          <div class="section-hd">
            <span class="section-title">9 种启发策略有效性排名</span>
            <span style="font-size:12px;color:var(--text-3)">使用次数 × 成功率</span>
          </div>
          <div class="strategy-table">
            <div class="strategy-hd">
              <span>策略名称</span>
              <span>使用次数</span>
              <span>成功率</span>
            </div>
            <div v-for="s in data?.strategy_effectiveness" :key="s.name" class="strategy-row">
              <span class="strategy-name">{{ s.name }}</span>
              <span class="num strategy-uses">{{ s.uses.toLocaleString() }}</span>
              <div class="strategy-rate-wrap">
                <div class="strategy-rate-bar" :style="{ width: (s.success_rate * 100) + '%' }" />
                <span class="num strategy-rate-pct">{{ (s.success_rate * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- 趋势折线图 -->
      <div class="two-cols">
        <div class="surface chart-card">
          <div class="section-hd"><span class="section-title">理解突破量趋势</span></div>
          <div ref="ahaRef" style="height:220px;margin-top:12px" />
        </div>
        <div class="surface chart-card">
          <div class="section-hd"><span class="section-title">对话量趋势</span></div>
          <div ref="chatRef" style="height:220px;margin-top:12px" />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'

type AiData = {
  summary: { aha_total: number; avg_rounds: number; breakthrough_rate: number; review_breakthrough_rate: number; silence_rate: number }
  session_mode_distribution: { mode: string; pct: number; color: string }[]
  strategy_effectiveness: { name: string; uses: number; success_rate: number }[]
  aha_trend: { date: string; aha_count: number; session_count: number; message_count: number }[]
}

const days = ref(7)
const loading = ref(false)
const data = ref<AiData | null>(null)

const modeRef = ref<HTMLElement>()
const ahaRef  = ref<HTMLElement>()
const chatRef = ref<HTMLElement>()
let modeChart: echarts.ECharts | undefined
let ahaChart:  echarts.ECharts | undefined
let chatChart: echarts.ECharts | undefined

const CHART_TEXT = '#94A3B8'

async function loadData() {
  loading.value = true
  try {
    data.value = await dashboardApi.getAiTeachingAnalysis(days.value) as AiData
    await nextTick()
    renderMode(); renderAha(); renderChat()
  } finally { loading.value = false }
}

function renderMode() {
  if (!modeRef.value || !data.value) return
  if (!modeChart) modeChart = echarts.init(modeRef.value)
  modeChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', backgroundColor: '#1E293B', borderColor: 'transparent', textStyle: { color: '#F8FAFC', fontSize: 12 }, extraCssText: 'border-radius:12px;padding:10px 14px', formatter: '{b}: {c}% ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: CHART_TEXT, fontSize: 12 } },
    series: [{ type: 'pie', radius: ['45%', '70%'], center: ['40%', '55%'], avoidLabelOverlap: false, label: { show: false }, data: data.value.session_mode_distribution.map(m => ({ value: m.pct, name: m.mode, itemStyle: { color: m.color } })) }],
  })
}

function makeTrendOptions(dates: string[], seriesData: { name: string; data: number[]; color: string }[]) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1E293B', borderColor: 'transparent', textStyle: { color: '#F8FAFC', fontSize: 12 }, extraCssText: 'border-radius:12px;padding:10px 14px' },
    legend: { data: seriesData.map(s => s.name), top: 0, right: 0, textStyle: { color: CHART_TEXT, fontSize: 11 }, icon: 'roundRect', itemWidth: 8, itemHeight: 8 },
    grid: { left: 36, right: 16, top: 28, bottom: 24 },
    xAxis: { type: 'category', data: dates.map(d => d.slice(5)), axisLine: { lineStyle: { color: 'rgba(79,70,229,0.12)' } }, axisLabel: { color: CHART_TEXT, fontSize: 10 }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: CHART_TEXT, fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(79,70,229,0.06)' } }, axisLine: { show: false } },
    series: seriesData.map(s => ({ name: s.name, type: 'line', smooth: true, showSymbol: false, data: s.data, itemStyle: { color: s.color }, lineStyle: { color: s.color, width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:s.color+'22'},{offset:1,color:s.color+'00'}]) } })),
  }
}

function renderAha() {
  if (!ahaRef.value || !data.value) return
  if (!ahaChart) ahaChart = echarts.init(ahaRef.value)
  const t = data.value.aha_trend
  ahaChart.setOption(makeTrendOptions(t.map(d => d.date), [{ name: '理解突破次数', data: t.map(d => d.aha_count), color: '#4F46E5' }]))
}

function renderChat() {
  if (!chatRef.value || !data.value) return
  if (!chatChart) chatChart = echarts.init(chatRef.value)
  const t = data.value.aha_trend
  chatChart.setOption(makeTrendOptions(t.map(d => d.date), [
    { name: '会话数', data: t.map(d => d.session_count), color: '#10B981' },
    { name: '消息数', data: t.map(d => d.message_count), color: '#F59E0B' },
  ]))
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.chart-card { padding: 20px 24px; }

.two-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.kpi-strip {
  display: flex;
  align-items: center;
  padding: 18px 24px;
  margin-bottom: 16px;
}

.kpi-item { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.kpi-val { font-size: 22px; font-weight: 700; }
.kpi-lbl { font-size: 12px; color: var(--text-3); text-align: center; }
.kpi-divider { width: 1px; height: 36px; background: var(--border); margin: 0 6px; }

// 策略列表
.strategy-table { display: flex; flex-direction: column; gap: 2px; margin-top: 12px; }

.strategy-hd {
  display: grid;
  grid-template-columns: 1fr 80px 140px;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-3);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0 4px 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}

.strategy-row {
  display: grid;
  grid-template-columns: 1fr 80px 140px;
  gap: 8px;
  align-items: center;
  padding: 7px 4px;
  border-radius: var(--r-sm);

  &:hover { background: var(--bg-muted); }
}

.strategy-name { font-size: 13px; color: var(--text-1); }
.strategy-uses  { font-size: 13px; color: var(--text-2); text-align: right; }

.strategy-rate-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strategy-rate-bar {
  flex: 1;
  height: 6px;
  background: var(--indigo);
  border-radius: 3px;
  opacity: 0.75;
}

.strategy-rate-pct { font-size: 12px; font-weight: 600; color: var(--indigo); min-width: 32px; text-align: right; }
</style>

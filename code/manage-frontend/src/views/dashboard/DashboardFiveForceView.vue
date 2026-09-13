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
          <h1 class="page-title">五力测试分析</h1>
          <p class="page-subtitle">全体学生五力认知能力分布与薄弱点归因分析</p>
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
          <span class="kpi-val num">{{ data.summary.total_tests.toLocaleString() }}</span>
          <span class="kpi-lbl">累计测试人次</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num">{{ data.summary.today_tests }}</span>
          <span class="kpi-lbl">今日测试人数</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num">{{ (data.summary.retest_rate * 100).toFixed(0) }}%</span>
          <span class="kpi-lbl">重测率</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num">{{ (data.summary.completion_rate * 100).toFixed(0) }}%</span>
          <span class="kpi-lbl">测试完成率</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num">{{ data.summary.avg_duration_min }}</span>
          <span class="kpi-lbl">平均耗时（分钟）</span>
        </div>
      </div>

      <!-- 雷达图 + 薄弱分布 -->
      <div class="two-cols">

        <div class="surface chart-card">
          <div class="section-hd">
            <span class="section-title">全体学生五力平均得分</span>
            <span style="font-size:12px;color:var(--text-3)">测试成绩均值</span>
          </div>
          <div ref="radarRef" style="height:300px;margin-top:12px" />
        </div>

        <div class="surface chart-card">
          <div class="section-hd">
            <span class="section-title">各维度薄弱分布</span>
            <span style="font-size:12px;color:var(--text-3)">最弱力归属占比</span>
          </div>
          <div ref="barRef" style="height:300px;margin-top:12px" />
        </div>

      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'

const days = ref(30)
const loading = ref(false)
const data = ref<{ summary: { total_tests: number; today_tests: number; retest_rate: number; completion_rate: number; avg_duration_min: number }; avg_scores: Record<string, number>; weakness_distribution: { power: string; power_key: string; pct: number }[] } | null>(null)

const radarRef = ref<HTMLElement>()
const barRef   = ref<HTMLElement>()
let radarChart: echarts.ECharts | undefined
let barChart:   echarts.ECharts | undefined

const POWER_COLORS: Record<string, string> = { INSIGHT: '#0D9488', CONSTRUCT: '#E11D48', DEDUCE: '#4F46E5', ADAPT: '#D97706', MIGRATE: '#7C3AED' }
const CHART_TEXT = '#94A3B8'

async function loadData() {
  loading.value = true
  try {
    data.value = await dashboardApi.getFiveForceAnalysis(days.value) as typeof data.value
    await nextTick()
    renderRadar()
    renderBar()
  } finally { loading.value = false }
}

function renderRadar() {
  if (!radarRef.value || !data.value) return
  if (!radarChart) radarChart = echarts.init(radarRef.value)
  const scores = data.value.avg_scores
  const powers = [
    { name: '洞察力', key: 'INSIGHT' }, { name: '建构力', key: 'CONSTRUCT' },
    { name: '推演力', key: 'DEDUCE' },  { name: '调适力', key: 'ADAPT' },
    { name: '迁移力', key: 'MIGRATE' },
  ]
  radarChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { backgroundColor: '#1E293B', borderColor: 'transparent', textStyle: { color: '#F8FAFC', fontSize: 12 }, extraCssText: 'border-radius:12px;padding:10px 14px' },
    radar: {
      indicator: powers.map(p => ({ name: `${p.name}\n${scores[p.key]}`, max: 100 })),
      shape: 'circle',
      splitNumber: 4,
      axisName: { color: CHART_TEXT, fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(79,70,229,0.10)' } },
      splitArea: { areaStyle: { color: ['rgba(79,70,229,0.02)', 'rgba(79,70,229,0.04)'] } },
      axisLine: { lineStyle: { color: 'rgba(79,70,229,0.15)' } },
    },
    series: [{
      type: 'radar',
      data: [{ value: powers.map(p => scores[p.key]), name: '五力均值', itemStyle: { color: '#4F46E5' }, lineStyle: { color: '#4F46E5', width: 2 }, areaStyle: { color: 'rgba(79,70,229,0.15)' } }],
    }],
  })
}

function renderBar() {
  if (!barRef.value || !data.value) return
  if (!barChart) barChart = echarts.init(barRef.value)
  const dist = [...data.value.weakness_distribution].sort((a, b) => b.pct - a.pct)
  barChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'none' }, backgroundColor: '#1E293B', borderColor: 'transparent', textStyle: { color: '#F8FAFC', fontSize: 12 }, extraCssText: 'border-radius:12px;padding:10px 14px', formatter: (p: { name: string; value: number }[]) => `${p[0].name}：${p[0].value}%` },
    grid: { left: 60, right: 56, top: 10, bottom: 10 },
    xAxis: { type: 'value', max: 50, axisLabel: { show: false }, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(79,70,229,0.06)' } } },
    yAxis: { type: 'category', data: dist.map(d => d.power), inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: CHART_TEXT, fontSize: 12 } },
    series: [{
      type: 'bar', barWidth: 18,
      data: dist.map(d => ({ value: d.pct, itemStyle: { color: POWER_COLORS[d.power_key] || '#4F46E5', borderRadius: [0, 4, 4, 0] } })),
      label: { show: true, position: 'right', color: CHART_TEXT, fontSize: 11, formatter: '{c}%' },
    }],
  })
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
  padding: 18px 28px;
  margin-bottom: 16px;
  gap: 0;
}

.kpi-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.kpi-val {
  font-size: 22px;
  font-weight: 700;
  color: var(--indigo);
}

.kpi-lbl { font-size: 12px; color: var(--text-3); }

.kpi-divider {
  width: 1px;
  height: 36px;
  background: var(--border);
  margin: 0 8px;
}
</style>

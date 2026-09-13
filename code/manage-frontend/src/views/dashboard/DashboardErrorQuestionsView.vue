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
          <h1 class="page-title">错题集分析</h1>
          <p class="page-subtitle">错题复盘状态、五力错题分布与高频共性难题 Top 10</p>
        </div>
      </div>
      <div style="display:flex;gap:10px">
        <el-radio-group v-model="days" size="small" @change="loadData">
          <el-radio-button :value="7">近7天</el-radio-button>
          <el-radio-button :value="30">近30天</el-radio-button>
        </el-radio-group>
        <el-button size="small">导出 CSV</el-button>
      </div>
    </div>

    <div v-loading="loading">

      <!-- 关键指标 -->
      <div class="surface kpi-strip" v-if="data">
        <div class="kpi-item">
          <span class="kpi-val num">{{ data.summary.total_errors.toLocaleString() }}</span>
          <span class="kpi-lbl">错题总量</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num" style="color:var(--green)">{{ (data.summary.review_rate * 100).toFixed(0) }}%</span>
          <span class="kpi-lbl">复盘率</span>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-item">
          <span class="kpi-val num" style="color:var(--indigo)">{{ (data.summary.breakthrough_rate * 100).toFixed(0) }}%</span>
          <span class="kpi-lbl">突破率（已复盘中）</span>
        </div>
      </div>

      <!-- 复盘状态 + 五力分布 -->
      <div class="two-cols">

        <div class="surface chart-card">
          <div class="section-hd"><span class="section-title">错题复盘状态分布</span></div>
          <div v-if="data" class="status-list">
            <div v-for="s in data.review_status_distribution" :key="s.status" class="status-row">
              <div class="status-dot" :style="{ background: s.color }" />
              <span class="status-name">{{ s.status }}</span>
              <div class="status-bar-wrap">
                <div class="status-bar" :style="{ width: s.pct + '%', background: s.color }" />
              </div>
              <span class="num status-count">{{ s.count.toLocaleString() }}道</span>
              <span class="num status-pct">{{ s.pct }}%</span>
            </div>
          </div>
          <div ref="pieRef" style="height:180px;margin-top:4px" />
        </div>

        <div class="surface chart-card">
          <div class="section-hd"><span class="section-title">五力错题分布</span></div>
          <div ref="barRef" style="height:260px;margin-top:12px" />
        </div>

      </div>

      <!-- 高频错题 Top 10 -->
      <div class="surface chart-card">
        <div class="section-hd">
          <span class="section-title">高频错题 Top 10</span>
          <span style="font-size:12px;color:var(--text-3)">暴露共性难点</span>
        </div>
        <el-table :data="data?.top_error_questions" style="width:100%" v-if="data">
          <el-table-column label="排名" width="60" align="center">
            <template #default="{ row }">
              <span class="num" :class="row.rank <= 3 ? 'rank-hot' : 'rank-normal'">{{ row.rank }}</span>
            </template>
          </el-table-column>
          <el-table-column label="题干摘要" min-width="340">
            <template #default="{ row }">
              <span style="font-size:13.5px;color:var(--text-1)">{{ row.stem.substring(0, 55) }}{{ row.stem.length > 55 ? '…' : '' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="错题人数" width="100" align="center">
            <template #default="{ row }">
              <span class="num" style="font-weight:700;color:var(--red)">{{ row.error_count }}</span>
              <span style="font-size:11px;color:var(--text-3)"> 人</span>
            </template>
          </el-table-column>
          <el-table-column label="所属五力" width="100">
            <template #default="{ row }">
              <span class="power-badge" :class="`power-badge--${row.power_key}`">{{ row.power }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'

type ErrorData = {
  summary: { total_errors: number; review_rate: number; breakthrough_rate: number }
  review_status_distribution: { status: string; count: number; pct: number; color: string }[]
  power_distribution: { power: string; power_key: string; pct: number }[]
  top_error_questions: { rank: number; stem: string; error_count: number; power: string; power_key: string }[]
}

const days = ref(30)
const loading = ref(false)
const data = ref<ErrorData | null>(null)

const pieRef = ref<HTMLElement>()
const barRef = ref<HTMLElement>()
let pieChart: echarts.ECharts | undefined
let barChart: echarts.ECharts | undefined

const POWER_COLORS: Record<string, string> = { INSIGHT: '#0D9488', CONSTRUCT: '#E11D48', DEDUCE: '#4F46E5', ADAPT: '#D97706', MIGRATE: '#7C3AED' }
const CHART_TEXT = '#94A3B8'

async function loadData() {
  loading.value = true
  try {
    data.value = await dashboardApi.getErrorQuestionsAnalysis(days.value) as ErrorData
    await nextTick()
    renderPie(); renderBar()
  } finally { loading.value = false }
}

function renderPie() {
  if (!pieRef.value || !data.value) return
  if (!pieChart) pieChart = echarts.init(pieRef.value)
  pieChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', backgroundColor: '#1E293B', borderColor: 'transparent', textStyle: { color: '#F8FAFC', fontSize: 12 }, extraCssText: 'border-radius:12px;padding:10px 14px', formatter: '{b}: {c}道 ({d}%)' },
    series: [{ type: 'pie', radius: ['40%', '65%'], center: ['50%', '55%'], avoidLabelOverlap: false, label: { show: false }, data: data.value.review_status_distribution.map(s => ({ value: s.count, name: s.status, itemStyle: { color: s.color } })) }],
  })
}

function renderBar() {
  if (!barRef.value || !data.value) return
  if (!barChart) barChart = echarts.init(barRef.value)
  const dist = [...data.value.power_distribution].sort((a, b) => b.pct - a.pct)
  barChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'none' }, backgroundColor: '#1E293B', borderColor: 'transparent', textStyle: { color: '#F8FAFC', fontSize: 12 }, extraCssText: 'border-radius:12px;padding:10px 14px', formatter: (p: { name: string; value: number }[]) => `${p[0].name}：${p[0].value}%` },
    grid: { left: 60, right: 56, top: 10, bottom: 10 },
    xAxis: { type: 'value', max: 50, axisLabel: { show: false }, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(79,70,229,0.06)' } } },
    yAxis: { type: 'category', data: dist.map(d => d.power), inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: CHART_TEXT, fontSize: 12 } },
    series: [{ type: 'bar', barWidth: 18, data: dist.map(d => ({ value: d.pct, itemStyle: { color: POWER_COLORS[d.power_key] || '#4F46E5', borderRadius: [0, 4, 4, 0] } })), label: { show: true, position: 'right', color: CHART_TEXT, fontSize: 11, formatter: '{c}%' } }],
  })
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.chart-card { padding: 20px 24px; margin-bottom: 16px; }

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
}

.kpi-item { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.kpi-val { font-size: 22px; font-weight: 700; color: var(--text-1); }
.kpi-lbl { font-size: 12px; color: var(--text-3); text-align: center; }
.kpi-divider { width: 1px; height: 36px; background: var(--border); margin: 0 16px; }

// 状态列表
.status-list { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-name { font-size: 13px; color: var(--text-2); min-width: 70px; }

.status-bar-wrap {
  flex: 1;
  height: 8px;
  background: var(--bg-muted);
  border-radius: 4px;
  overflow: hidden;
}

.status-bar {
  height: 100%;
  border-radius: 4px;
  opacity: 0.8;
  transition: width 0.6s ease;
}

.status-count { font-size: 12px; color: var(--text-2); min-width: 60px; text-align: right; }
.status-pct   { font-size: 12px; color: var(--text-3); min-width: 36px; text-align: right; }

// 排名样式
.rank-hot    { font-size: 15px; font-weight: 700; color: var(--red); }
.rank-normal { font-size: 14px; font-weight: 600; color: var(--text-3); }
</style>

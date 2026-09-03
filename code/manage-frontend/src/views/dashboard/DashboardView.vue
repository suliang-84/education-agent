<template>
  <div class="dashboard-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">数据看板</h1>
        <span class="page-date">{{ selectedDate }}</span>
      </div>
      <el-date-picker
        v-model="selectedDate"
        type="date"
        placeholder="选择日期"
        size="small"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
      />
    </div>

    <!-- 概览卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6" class="stat-col stat-col--1">
        <div class="stat-card">
          <div class="stat-icon stat-icon--blue">
            <el-icon size="22"><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number indigo-shimmer">{{ animStudents || '—' }}</div>
            <div class="stat-label">总学生数</div>
            <div class="stat-sub">
              <span class="pill-green">+{{ overview?.users.new_today ?? 0 }} 今日</span>
              活跃 <strong>{{ overview?.users.active_today ?? 0 }}</strong>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="6" class="stat-col stat-col--2">
        <div class="stat-card">
          <div class="stat-icon stat-icon--purple">
            <el-icon size="22"><DataAnalysis /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number indigo-shimmer">{{ animSessions || '—' }}</div>
            <div class="stat-label">今日训练会话</div>
            <div class="stat-sub">
              正确率 <strong>{{ formatPercent(overview?.training.accuracy_rate ?? 0) }}</strong>
              · 答题 {{ overview?.training.answers_today ?? 0 }} 题
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="6" class="stat-col stat-col--3">
        <div class="stat-card">
          <div class="stat-icon stat-icon--amber">
            <el-icon size="22"><ChatDotSquare /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number indigo-shimmer">{{ formatCost(overview?.ai.token_cost_today_usd ?? 0) }}</div>
            <div class="stat-label">今日 AI 成本</div>
            <div class="stat-sub">
              RAG {{ overview?.ai.rag_calls_today ?? 0 }} 次
              · 降级 <span :class="downgradeClass">{{ formatPercent(overview?.ai.downgrade_rate ?? 0) }}</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="6" class="stat-col stat-col--4">
        <div class="stat-card">
          <div class="stat-icon stat-icon--teal">
            <el-icon size="22"><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number indigo-shimmer">{{ animQuestions || '—' }}</div>
            <div class="stat-label">已发布题目</div>
            <div class="stat-sub">
              待审核 <strong class="pill-warning">{{ overview?.question_bank.pending_annotation ?? 0 }}</strong>
              · 待向量化 {{ overview?.question_bank.pending_embedding ?? 0 }}
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" class="charts-row">
      <!-- Token消耗趋势 -->
      <el-col :span="16">
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">Token 消耗趋势</h3>
            <el-select v-model="tokenRange" size="small" style="width: 120px">
              <el-option label="最近7天" value="7" />
              <el-option label="最近30天" value="30" />
            </el-select>
          </div>
          <div ref="lineChartRef" class="chart-container"></div>
        </div>
      </el-col>

      <!-- 模块分布 -->
      <el-col :span="8">
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">Token 模块分布</h3>
          </div>
          <div ref="pieChartRef" class="chart-container"></div>
          <div class="pie-legend">
            <div v-for="item in moduleData" :key="item.name" class="legend-item">
              <span class="legend-dot" :style="{ background: item.color }"></span>
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-value">{{ formatCost(item.cost) }}</span>
              <span class="legend-pct">({{ item.pct }}%)</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 题库状态 + AI指标 -->
    <el-row :gutter="16" class="extra-row">
      <el-col :span="12">
        <div class="info-card">
          <h3 class="card-title">题库状态</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="已发布题目">
              <span class="bold">{{ overview?.question_bank.total_published }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="待审核标注">
              <el-tag type="warning">{{ overview?.question_bank.pending_annotation }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="待向量化">
              <el-tag type="info">{{ overview?.question_bank.pending_embedding }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="今日完成测试">
              <span class="bold">{{ overview?.users.completed_test }}</span> 人
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="info-card">
          <h3 class="card-title">AI 指标</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="RAG 调用">
              <span class="bold">{{ overview?.ai.rag_calls_today }}</span> 次
            </el-descriptions-item>
            <el-descriptions-item label="对话消息">
              <span class="bold">{{ overview?.ai.chat_messages_today }}</span> 条
            </el-descriptions-item>
            <el-descriptions-item label="Token 成本">
              <span class="bold">{{ formatCost(overview?.ai.token_cost_today_usd ?? 0) }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="降级率">
              <el-tag :type="(overview?.ai.downgrade_rate ?? 0) > 0.05 ? 'danger' : 'success'">
                {{ formatPercent(overview?.ai.downgrade_rate ?? 0) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { User, DataAnalysis, Document, ChatDotSquare } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { dashboardApi } from '../../api'
import type { DashboardOverview, TokenUsage } from '../../types'
import { formatPercent, formatCost } from '../../utils/format'

const overview = ref<DashboardOverview | null>(null)
const tokenUsage = ref<TokenUsage | null>(null)
const selectedDate = ref('2026-08-30')
const tokenRange = ref('7')

const lineChartRef = ref<HTMLElement | null>(null)
const pieChartRef = ref<HTMLElement | null>(null)
let lineChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

/* ── Number count-up animation ── */
const animStudents  = ref(0)
const animSessions  = ref(0)
const animQuestions = ref(0)

function countUp(setter: (v: number) => void, target: number, duration = 1400) {
  if (!target) { setter(0); return }
  const start = performance.now()
  const tick = (now: number) => {
    const t = Math.min((now - start) / duration, 1)
    const eased = 1 - Math.pow(1 - t, 4) // easeOutQuart
    setter(Math.round(target * eased))
    if (t < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

watch(overview, (val) => {
  if (!val) return
  countUp(v => animStudents.value  = v, val.users.total_students ?? 0)
  countUp(v => animSessions.value  = v, val.training.sessions_today ?? 0, 900)
  countUp(v => animQuestions.value = v, val.question_bank.total_published ?? 0, 1600)
})

const downgradeClass = computed(() => {
  const rate = overview.value?.ai.downgrade_rate ?? 0
  return rate > 0.05 ? 'highlight-red' : 'highlight-green'
})

const moduleData = computed(() => {
  if (!tokenUsage.value) return []
  const { by_module, total_cost_usd } = tokenUsage.value.summary
  return [
    { name: '训练模块', cost: by_module.training.cost_usd,  pct: Math.round(by_module.training.cost_usd  / total_cost_usd * 100), color: '#4361EE' },
    { name: '助教模块', cost: by_module.assistant.cost_usd, pct: Math.round(by_module.assistant.cost_usd / total_cost_usd * 100), color: '#7B2FBE' },
    { name: '测试模块', cost: by_module.test.cost_usd,      pct: Math.round(by_module.test.cost_usd      / total_cost_usd * 100), color: '#10B981' },
  ]
})

/* Shared ECharts tooltip style (light) */
const tooltipStyle = {
  backgroundColor: '#FFFFFF',
  borderColor: 'rgba(67, 97, 238, 0.15)',
  textStyle: { color: '#0F172A' },
  extraCssText: 'box-shadow: 0 4px 20px rgba(67,97,238,0.12); border-radius: 8px;',
}

function initLineChart() {
  if (!lineChartRef.value || !tokenUsage.value) return
  lineChart = echarts.init(lineChartRef.value)
  const data = tokenUsage.value.daily_data
  lineChart.setOption({
    tooltip: {
      trigger: 'axis',
      ...tooltipStyle,
      formatter: (params: any) => {
        const d = params[0]
        return `<span style="color:#64748B">${d.axisValue}</span><br/>消耗：<b>${d.data[1].toLocaleString()}</b> tokens<br/>成本：<b>$${(params[1]?.data[1] ?? 0).toFixed(4)}</b>`
      },
    },
    legend: {
      data: ['Token数量', '成本($)'],
      textStyle: { color: '#64748B', fontSize: 12 },
      top: 0,
    },
    grid: { left: 60, right: 60, top: 36, bottom: 36 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLabel: { color: '#94A3B8', fontSize: 12 },
      axisLine: { lineStyle: { color: 'rgba(67, 97, 238, 0.1)' } },
      splitLine: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: 'Tokens',
        nameTextStyle: { color: '#94A3B8', fontSize: 11 },
        axisLabel: { color: '#94A3B8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(67, 97, 238, 0.06)' } },
        axisLine: { lineStyle: { color: 'rgba(67, 97, 238, 0.08)' } },
      },
      {
        type: 'value',
        name: '成本($)',
        nameTextStyle: { color: '#94A3B8', fontSize: 11 },
        axisLabel: { color: '#94A3B8', fontSize: 11 },
        position: 'right',
        axisLine: { lineStyle: { color: 'rgba(67, 97, 238, 0.08)' } },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: 'Token数量',
        type: 'bar',
        data: data.map(d => [d.date.slice(5), d.total_tokens]),
        itemStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(67, 97, 238, 0.65)' },
              { offset: 1, color: 'rgba(67, 97, 238, 0.08)' },
            ],
          },
          borderRadius: [4, 4, 0, 0],
        },
      },
      {
        name: '成本($)',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(d => [d.date.slice(5), d.total_cost_usd]),
        lineStyle: { color: '#7B2FBE', width: 2 },
        itemStyle: { color: '#7B2FBE' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(123, 47, 190, 0.14)' },
              { offset: 1, color: 'rgba(123, 47, 190, 0.01)' },
            ],
          },
        },
        symbol: 'circle',
        symbolSize: 6,
        smooth: true,
      },
    ],
  })
}

function initPieChart() {
  if (!pieChartRef.value || !tokenUsage.value) return
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {d}%',
      ...tooltipStyle,
    },
    series: [{
      type: 'pie',
      radius: ['40%', '68%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#0F172A' },
        itemStyle: { shadowBlur: 16, shadowColor: 'rgba(67, 97, 238, 0.3)' },
      },
      data: moduleData.value.map(m => ({
        value: m.cost,
        name: m.name,
        itemStyle: { color: m.color },
      })),
    }],
  })
}

async function loadData() {
  const [overviewRes, tokenRes] = await Promise.all([
    dashboardApi.getOverview(),
    dashboardApi.getTokenUsage(),
  ])
  if (overviewRes.status === 'success') overview.value = overviewRes.data
  if (tokenRes.status === 'success') tokenUsage.value = tokenRes.data

  await nextTick()
  initLineChart()
  initPieChart()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => {
    lineChart?.resize()
    pieChart?.resize()
  })
})

onUnmounted(() => {
  lineChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.dashboard-view { max-width: 1400px; }

/* ── Page header ── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
  animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.page-header-left { display: flex; align-items: baseline; gap: 12px; }

.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.5px;
}

.page-date {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-muted);
}

/* ── Stat cards stagger ── */
.stats-row { margin-bottom: 16px; }

.stat-col--1 { animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 60ms both; }
.stat-col--2 { animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 130ms both; }
.stat-col--3 { animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 200ms both; }
.stat-col--4 { animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 270ms both; }

.stat-card {
  background: var(--bg-surface);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-card);
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon--blue   { background: rgba(67, 97, 238, 0.1);  color: #4361EE; }
.stat-icon--purple { background: rgba(123, 47, 190, 0.1); color: #7B2FBE; }
.stat-icon--amber  { background: rgba(245, 158, 11, 0.1); color: #D97706; }
.stat-icon--teal   { background: rgba(16, 185, 129, 0.1); color: #10B981; }

.stat-content { flex: 1; min-width: 0; }

/* Number with indigo shimmer on count-up */
.stat-number {
  font-family: 'JetBrains Mono', monospace;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 5px;
  letter-spacing: -0.5px;
  font-variant-numeric: tabular-nums;
}
.indigo-shimmer {
  background: linear-gradient(
    90deg,
    var(--text-primary) 0%,
    #4361EE 45%,
    #7B2FBE 55%,
    var(--text-primary) 100%
  );
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmerSlide 2s linear 0.2s 1 both;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.stat-sub {
  font-size: 12px;
  color: var(--text-muted);
}

.pill-green {
  display: inline-block;
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border-radius: 9999px;
  padding: 0 7px;
  font-weight: 600;
  font-size: 11px;
  margin-right: 4px;
}
.pill-warning {
  color: #D97706;
}

/* ── Charts ── */
.charts-row { margin-bottom: 16px; }

.charts-row .el-col:nth-child(1) .chart-card {
  animation: scaleIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) 360ms both;
}
.charts-row .el-col:nth-child(2) .chart-card {
  animation: scaleIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) 440ms both;
}

.chart-card {
  background: var(--bg-surface);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-card);
  transition: border-color 0.25s, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s;
}
.chart-card:hover {
  border-color: rgba(67, 97, 238, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(67, 97, 238, 0.08), 0 0 0 1px rgba(67, 97, 238, 0.08);
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.chart-title {
  font-family: 'Outfit', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.2px;
}

.chart-container { width: 100%; height: 260px; }

.pie-legend { margin-top: 12px; }

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.legend-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.legend-name  { flex: 1; color: var(--text-secondary); }
.legend-value { color: var(--text-primary); font-weight: 600; font-variant-numeric: tabular-nums; font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.legend-pct   { color: var(--text-muted); font-size: 12px; }

/* ── Info cards ── */
.extra-row { margin-bottom: 16px; }

.extra-row .el-col:nth-child(1) .info-card {
  animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 520ms both;
}
.extra-row .el-col:nth-child(2) .info-card {
  animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 600ms both;
}

.info-card {
  background: var(--bg-surface);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-card);
  transition: border-color 0.25s;
}
.info-card:hover { border-color: rgba(67, 97, 238, 0.2); }

.card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
  letter-spacing: -0.2px;
}

.bold { font-weight: 600; }
.highlight-green { color: #059669; font-weight: 600; }
.highlight-red   { color: #DC2626; font-weight: 600; }
</style>

<template>
  <div class="dash-root">

    <!-- ── 顶部欢迎区 ─────────────────────────────────────── -->
    <div class="welcome-bar">
      <div>
        <h1 class="welcome-title">
          Hi，<span class="welcome-name">{{ authStore.user?.username ?? 'admin' }}</span> 👋
        </h1>
        <p class="welcome-date">{{ todayLabel }} · 实时运营数据概览</p>
      </div>
      <div class="welcome-right">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :clearable="false"
          size="small"
          @change="loadStats"
          style="width: 148px"
        />
      </div>
    </div>

    <!-- ── 4个指标卡 ───────────────────────────────────────── -->
    <div class="stats-grid" v-loading="loading">

      <!-- 总学生数：靛蓝 -->
      <div class="stat-card">
        <div class="stat-card__top">
          <div class="stat-card__icon-block" style="background: rgba(79,70,229,0.12)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>
            </svg>
          </div>
          <span class="stat-card__label">总学生数</span>
        </div>
        <div class="stat-card__value num">{{ stats?.total_students?.toLocaleString() ?? '--' }}</div>
        <div class="stat-card__footer">
          <span class="stat-trend stat-trend--up">+{{ stats?.new_students_today ?? 0 }} 今日新增</span>
          <span class="stat-card__sub">活跃 {{ stats?.active_students_today ?? '--' }}</span>
        </div>
      </div>

      <!-- 今日训练：绿色 -->
      <div class="stat-card">
        <div class="stat-card__top">
          <div class="stat-card__icon-block" style="background: rgba(34,197,94,0.12)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/>
            </svg>
          </div>
          <span class="stat-card__label">今日训练</span>
        </div>
        <div class="stat-card__value num">{{ stats?.training_sessions_today ?? '--' }}</div>
        <div class="stat-card__footer">
          <span class="stat-card__sub">答题 {{ stats?.answers_today ?? '--' }}</span>
          <span class="stat-trend" :class="accuracyClass">正确率 {{ accPct }}%</span>
        </div>
      </div>

      <!-- RAG调用：琥珀 -->
      <div class="stat-card">
        <div class="stat-card__top">
          <div class="stat-card__icon-block" style="background: rgba(245,158,11,0.12)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"/>
            </svg>
          </div>
          <span class="stat-card__label">RAG 调用</span>
        </div>
        <div class="stat-card__value num">{{ stats?.rag_calls_today ?? '--' }}</div>
        <div class="stat-card__footer">
          <span class="stat-card__sub">AI消息 {{ stats?.chat_messages_today ?? '--' }}</span>
          <span class="stat-trend" :class="degradeClass">降级 {{ degradePct }}%</span>
        </div>
      </div>

      <!-- Token成本：粉色 -->
      <div class="stat-card">
        <div class="stat-card__top">
          <div class="stat-card__icon-block" style="background: rgba(244,63,126,0.10)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F43F7E" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"/>
            </svg>
          </div>
          <span class="stat-card__label">Token 成本</span>
        </div>
        <div class="stat-card__value num">${{ stats?.token_cost_today?.toFixed(2) ?? '--' }}</div>
        <div class="stat-card__footer">
          <span class="stat-card__sub">今日 AI 调用综合费用</span>
        </div>
      </div>
    </div>

    <!-- ── 中间行：题库状态 + ECharts图表 ─────────────────── -->
    <div class="mid-row">

      <!-- 左：题库状态面板 -->
      <div class="surface bank-panel">
        <div class="section-hd">
          <span class="section-title">题库状态</span>
          <router-link to="/questions" class="text-link">查看题库 →</router-link>
        </div>

        <!-- 三格数字 -->
        <div class="bank-grid">
          <div class="bank-item">
            <div class="bank-item__value num">{{ stats?.published_questions?.toLocaleString() ?? '--' }}</div>
            <div class="bank-item__label">已发布题目</div>
          </div>
          <div class="bank-item bank-item--amber" @click="$router.push('/annotations')" style="cursor: pointer">
            <div class="bank-item__value num">{{ stats?.pending_annotations ?? '--' }}</div>
            <div class="bank-item__label">待审核标注</div>
          </div>
          <div class="bank-item">
            <div class="bank-item__value num">{{ stats?.pending_vectors ?? '--' }}</div>
            <div class="bank-item__label">待向量化</div>
          </div>
        </div>

        <!-- 分隔线 -->
        <div class="row-divider"></div>

        <!-- 五力覆盖进度条 -->
        <div class="section-title" style="margin-bottom: 12px">五力覆盖分布</div>
        <div class="power-bars">
          <div class="power-bar-row" v-for="p in powerBars" :key="p.key">
            <div class="power-bar-row__label" :style="{ color: p.color }">{{ p.name }}</div>
            <div class="power-bar-row__track">
              <div
                class="power-bar-row__fill"
                :style="{ width: p.pct + '%', background: p.color }"
              ></div>
            </div>
            <div class="power-bar-row__val num" :style="{ color: p.color }">{{ p.pct }}%</div>
          </div>
        </div>
      </div>

      <!-- 右：ECharts折线图 -->
      <div class="surface chart-panel">
        <div class="section-hd">
          <span class="section-title">Token 消耗趋势</span>
          <el-radio-group v-model="trendDays" size="small" @change="loadTrend">
            <el-radio-button :value="7">7天</el-radio-button>
            <el-radio-button :value="14">14天</el-radio-button>
            <el-radio-button :value="30">30天</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="chartRef" style="height: 260px; margin-top: 14px" />
      </div>
    </div>

    <!-- ── 底部成本分布 ────────────────────────────────────── -->
    <div class="surface cost-section">
      <div class="section-hd" style="margin-bottom: 20px">
        <span class="section-title">模块成本分布</span>
        <span style="font-size: 12px; color: #94A3B8">近 {{ trendDays }} 天统计</span>
      </div>
      <div class="cost-grid">
        <div class="cost-item" v-for="c in costBreakdown" :key="c.label">
          <!-- 大数字 -->
          <div class="cost-item__amount num" :style="{ color: c.color }">${{ c.total.toFixed(2) }}</div>
          <!-- 标签行 -->
          <div class="cost-item__meta">
            <span class="cost-item__dot" :style="{ background: c.color }"></span>
            <span class="cost-item__label">{{ c.label }}</span>
            <span class="cost-item__pct num" :style="{ color: c.color }">{{ c.pct }}%</span>
          </div>
          <!-- 进度条 -->
          <div class="cost-item__bar">
            <div
              class="cost-item__fill"
              :style="{ width: c.pct + '%', background: c.color }"
            ></div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'
import type { DashboardStats, TokenTrend } from '@/types'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'

const authStore = useAuthStore()
const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
const loading = ref(false)
const trendDays = ref(7)
const stats = ref<DashboardStats>()
const chartRef = ref<HTMLElement>()
let lineChart: echarts.ECharts | null = null

// 今日日期中文格式
const todayLabel = computed(() => dayjs().format('YYYY年M月D日'))

// 正确率计算
const accPct = computed(() => ((stats.value?.avg_accuracy ?? 0) * 100).toFixed(0))
const accuracyClass = computed(() => {
  const v = stats.value?.avg_accuracy ?? 0
  return v >= 0.7 ? 'stat-trend--up' : v < 0.5 ? 'stat-trend--down' : ''
})

// 降级率
const degradePct = computed(() => ((stats.value?.degradation_rate ?? 0) * 100).toFixed(1))
const degradeClass = computed(() =>
  (stats.value?.degradation_rate ?? 0) > 0.05 ? 'stat-trend--down' : ''
)

// 五力覆盖数据（固定占位，可接后端）
const powerBars = [
  { key: 'INSIGHT',   name: '洞察力', color: '#4F46E5', pct: 28 },
  { key: 'CONSTRUCT', name: '建构力', color: '#F43F7E', pct: 22 },
  { key: 'DEDUCE',    name: '推演力', color: '#14B8A6', pct: 20 },
  { key: 'ADAPT',     name: '调适力', color: '#F59E0B', pct: 17 },
  { key: 'MIGRATE',   name: '迁移力', color: '#A855F7', pct: 13 },
]

// 成本分布
const costBreakdown = ref([
  { label: '训练模块', color: '#4F46E5', pct: 63, total: 0 },
  { label: 'AI 助教',  color: '#14B8A6', pct: 33, total: 0 },
  { label: '测试模块', color: '#F59E0B', pct: 4,  total: 0 },
])

async function loadStats() {
  loading.value = true
  try {
    stats.value = await dashboardApi.getStats(selectedDate.value)
  } finally {
    loading.value = false
  }
}

async function loadTrend() {
  const data = await dashboardApi.getTokenTrend(trendDays.value)
  renderChart(data)
  const totals = data.reduce(
    (a, d) => ({
      training:  a.training  + d.training_cost,
      assistant: a.assistant + d.assistant_cost,
      test:      a.test      + d.test_cost,
    }),
    { training: 0, assistant: 0, test: 0 }
  )
  const sum = totals.training + totals.assistant + totals.test || 1
  costBreakdown.value = [
    { label: '训练模块', color: '#4F46E5', pct: Math.round(totals.training  / sum * 100), total: totals.training  },
    { label: 'AI 助教',  color: '#14B8A6', pct: Math.round(totals.assistant / sum * 100), total: totals.assistant },
    { label: '测试模块', color: '#F59E0B', pct: Math.round(totals.test      / sum * 100), total: totals.test      },
  ]
}

function renderChart(data: TokenTrend[]) {
  if (!chartRef.value) return
  // 亮色模式：不传第二个参数
  if (!lineChart) lineChart = echarts.init(chartRef.value)

  lineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1E293B',
      borderColor: 'transparent',
      textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: 'Inter, system-ui' },
      extraCssText: 'border-radius: 12px; box-shadow: 0 8px 32px rgba(30,41,59,0.20); padding: 12px 16px;',
      formatter: (params: { name: string; color: string; seriesName: string; value: number }[]) => {
        let s = `<div style="margin-bottom:8px;font-weight:600;color:#94A3B8;font-size:11px;letter-spacing:0.04em">${params[0].name}</div>`
        params.forEach(p => {
          s += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${p.color};flex-shrink:0"></span>
            <span style="color:#CBD5E1;flex:1">${p.seriesName}</span>
            <span style="font-family:'JetBrains Mono',monospace;color:#F8FAFC;font-weight:600;margin-left:16px">$${p.value.toFixed(3)}</span>
          </div>`
        })
        return s
      },
    },
    legend: {
      data: ['训练模块', 'AI助教', '测试模块'],
      top: 0,
      right: 0,
      textStyle: { color: '#94A3B8', fontSize: 12, fontFamily: 'Inter, system-ui' },
      icon: 'roundRect',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 16,
    },
    grid: { left: 40, right: 16, top: 36, bottom: 28 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: 'rgba(79,70,229,0.12)' } },
      axisLabel: { color: '#94A3B8', fontSize: 11, fontFamily: 'Inter' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94A3B8', fontSize: 11, fontFamily: 'Inter', formatter: '${value}' },
      splitLine: { lineStyle: { color: 'rgba(79,70,229,0.06)' } },
      axisLine: { show: false },
    },
    series: [
      {
        name: '训练模块',
        type: 'line',
        smooth: true,
        data: data.map(d => d.training_cost),
        itemStyle: { color: '#4F46E5' },
        lineStyle: { color: '#4F46E5', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79,70,229,0.12)' },
            { offset: 1, color: 'rgba(79,70,229,0)' },
          ]),
        },
        symbol: 'circle',
        symbolSize: 5,
        showSymbol: false,
      },
      {
        name: 'AI助教',
        type: 'line',
        smooth: true,
        data: data.map(d => d.assistant_cost),
        itemStyle: { color: '#14B8A6' },
        lineStyle: { color: '#14B8A6', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(20,184,166,0.10)' },
            { offset: 1, color: 'rgba(20,184,166,0)' },
          ]),
        },
        symbol: 'circle',
        symbolSize: 5,
        showSymbol: false,
      },
      {
        name: '测试模块',
        type: 'line',
        smooth: true,
        data: data.map(d => d.test_cost),
        itemStyle: { color: '#F59E0B' },
        lineStyle: { color: '#F59E0B', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245,158,11,0.08)' },
            { offset: 1, color: 'rgba(245,158,11,0)' },
          ]),
        },
        symbol: 'circle',
        symbolSize: 5,
        showSymbol: false,
      },
    ],
  })
}

onMounted(async () => {
  await loadStats()
  await nextTick()
  await loadTrend()
  window.addEventListener('resize', () => lineChart?.resize())
})
</script>

<style scoped>
/* ── 页面根 ───────────────────────────────────────────────── */
.dash-root {
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-family: 'Inter', system-ui, sans-serif;
}

/* 数字等宽字体 */
.num {
  font-family: 'JetBrains Mono', monospace;
}

/* ── Surface 卡片基础 ─────────────────────────────────────── */
.surface {
  background: #FFFFFF;
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(79,70,229,0.06);
}

/* ── 欢迎区 ───────────────────────────────────────────────── */
.welcome-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 4px 0;
}
.welcome-title {
  font-size: 26px;
  font-weight: 700;
  color: #1E293B;
  letter-spacing: -0.03em;
  margin: 0 0 4px;
}
.welcome-name {
  color: #4F46E5;
}
.welcome-date {
  font-size: 13px;
  color: #94A3B8;
  margin: 0;
}
.welcome-right {
  display: flex;
  align-items: center;
}

/* ── 指标卡网格 ───────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

/* ── 指标卡 ───────────────────────────────────────────────── */
.stat-card {
  background: #FFFFFF;
  border-radius: 18px;
  padding: 20px 20px 18px;
  box-shadow: 0 2px 8px rgba(79,70,229,0.06);
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: box-shadow 200ms, transform 200ms;
}
.stat-card:hover {
  box-shadow: 0 6px 24px rgba(79,70,229,0.12);
  transform: translateY(-2px);
}

.stat-card__top {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 彩色图标块 42×42 */
.stat-card__icon-block {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card__label {
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  flex: 1;
}

.stat-card__value {
  font-size: 32px;
  font-weight: 700;
  color: #1E293B;
  letter-spacing: -0.04em;
  line-height: 1;
}

.stat-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-card__sub {
  font-size: 12px;
  color: #94A3B8;
}

/* ── 趋势胶囊 ─────────────────────────────────────────────── */
.stat-trend {
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 9999px;
  background: #F1F5F9;
  color: #64748B;
  white-space: nowrap;
}
.stat-trend--up {
  background: rgba(34,197,94,0.12);
  color: #16A34A;
}
.stat-trend--down {
  background: rgba(239,68,68,0.10);
  color: #DC2626;
}

/* ── 中间行 ───────────────────────────────────────────────── */
.mid-row {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
}

.bank-panel,
.chart-panel {
  padding: 20px 22px;
}

/* ── Section 头部 ─────────────────────────────────────────── */
.section-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  letter-spacing: -0.01em;
}
.text-link {
  font-size: 12px;
  color: #4F46E5;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 150ms;
}
.text-link:hover { opacity: 0.75; }

/* ── 题库三格 ─────────────────────────────────────────────── */
.bank-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border: 1px solid #F1F5F9;
  border-radius: 12px;
  overflow: hidden;
}
.bank-item {
  padding: 14px 10px;
  text-align: center;
  border-right: 1px solid #F1F5F9;
  transition: background 150ms;
}
.bank-item:last-child { border-right: none; }
.bank-item:hover { background: #FAFBFF; }
.bank-item--amber .bank-item__value { color: #F59E0B; }
.bank-item__value {
  font-size: 28px;
  font-weight: 700;
  color: #1E293B;
  letter-spacing: -0.04em;
  line-height: 1;
  margin-bottom: 5px;
}
.bank-item__label {
  font-size: 11px;
  color: #94A3B8;
  font-weight: 500;
}

/* ── 分隔线 ───────────────────────────────────────────────── */
.row-divider {
  height: 1px;
  background: #F1F5F9;
  margin: 18px 0 14px;
}

/* ── 五力进度条 ───────────────────────────────────────────── */
.power-bars {
  display: flex;
  flex-direction: column;
  gap: 9px;
}
.power-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.power-bar-row__label {
  font-size: 12px;
  font-weight: 600;
  width: 40px;
  flex-shrink: 0;
  letter-spacing: 0.01em;
}
.power-bar-row__track {
  flex: 1;
  height: 5px;
  background: #F1F5F9;
  border-radius: 3px;
  overflow: hidden;
}
.power-bar-row__fill {
  height: 100%;
  border-radius: 3px;
  opacity: 0.80;
  transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
}
.power-bar-row__val {
  font-size: 11.5px;
  font-weight: 600;
  width: 32px;
  text-align: right;
  flex-shrink: 0;
}

/* ── 底部成本分布 ─────────────────────────────────────────── */
.cost-section {
  padding: 20px 22px;
}
.cost-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.cost-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cost-item__amount {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
}
.cost-item__meta {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cost-item__dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}
.cost-item__label {
  font-size: 12.5px;
  color: #475569;
  flex: 1;
}
.cost-item__pct {
  font-size: 12px;
  font-weight: 700;
}
.cost-item__bar {
  height: 4px;
  background: #F1F5F9;
  border-radius: 2px;
  overflow: hidden;
}
.cost-item__fill {
  height: 100%;
  border-radius: 2px;
  opacity: 0.75;
  transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

/* ── 响应式 ───────────────────────────────────────────────── */
@media (max-width: 1200px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .mid-row { grid-template-columns: 1fr; }
}
@media (max-width: 700px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .cost-grid { grid-template-columns: 1fr; }
  .welcome-bar { flex-direction: column; align-items: flex-start; }
}
</style>

<template>
  <div class="dash">

    <!-- ── Row 0：页头 欢迎语 + 时间范围切换 ──────────────────── -->
    <div class="welcome-bar">
      <div>
        <h1 class="welcome-title">
          Hi，<span class="welcome-name">{{ authStore.user?.username ?? 'admin' }}</span> 👋
        </h1>
        <p class="welcome-date">{{ todayLabel }} · 运营数据全局看板</p>
      </div>
      <div class="welcome-right">
        <el-radio-group v-model="days" size="small" @change="(v: number) => setDays(v)">
          <el-radio-button v-for="t in TABS" :key="t.v" :value="t.v">{{ t.l }}</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- ── Row 1：KPI 网格 4列 ──────────────────────────────────── -->
    <div class="kpi-row" v-loading="loading">

      <!-- 用户规模 -->
      <div class="card">
        <div class="kpi-top">
          <div class="kpi-icon" style="background:rgba(79,70,229,0.10)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>
            </svg>
          </div>
          <span class="kpi-label">用户规模</span>
        </div>
        <div class="kpi-value num">{{ stats?.total_students?.toLocaleString() ?? '--' }}</div>
        <div class="kpi-footer">
          <span class="badge badge--up">+{{ stats?.new_students_today ?? 0 }} 今日新增</span>
          <span class="kpi-sub">活跃 {{ stats?.active_students_today ?? '--' }}</span>
        </div>
      </div>

      <!-- 训练活跃 -->
      <div class="card">
        <div class="kpi-top">
          <div class="kpi-icon" style="background:rgba(34,197,94,0.10)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/>
            </svg>
          </div>
          <span class="kpi-label">训练活跃</span>
        </div>
        <div class="kpi-value num">{{ stats?.training_sessions_today ?? '--' }}</div>
        <div class="kpi-footer">
          <span class="kpi-sub">答题 {{ stats?.answers_today ?? '--' }}</span>
          <span class="badge" :class="accuracyClass">正确率 {{ accPct }}%</span>
        </div>
      </div>

      <!-- AI助教 -->
      <div class="card">
        <div class="kpi-top">
          <div class="kpi-icon" style="background:rgba(245,158,11,0.10)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"/>
            </svg>
          </div>
          <span class="kpi-label">AI 助教</span>
        </div>
        <div class="kpi-value num">{{ stats?.rag_calls_today ?? '--' }}</div>
        <div class="kpi-footer">
          <span class="kpi-sub">AI消息 {{ stats?.chat_messages_today ?? '--' }}</span>
          <span class="badge" :class="degradeClass">降级 {{ degradePct }}%</span>
        </div>
      </div>

      <!-- 题库健康度 -->
      <div class="card">
        <div class="kpi-top">
          <div class="kpi-icon" style="background:rgba(244,63,126,0.10)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F43F7E" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"/>
            </svg>
          </div>
          <span class="kpi-label">题库健康度</span>
        </div>
        <div class="kpi-value num">{{ stats?.published_questions?.toLocaleString() ?? '--' }}</div>
        <div class="kpi-footer">
          <span class="kpi-sub">待标注 {{ stats?.pending_annotations ?? '--' }}</span>
          <span class="kpi-sub">待向量 {{ stats?.pending_vectors ?? '--' }}</span>
        </div>
      </div>

    </div><!-- /kpi-row -->

    <!-- ── Row 2：用户增长折线图(6fr) + 五力薄弱水平柱状图(4fr) ── -->
    <div class="row-2">

      <!-- 用户增长折线图 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">用户增长趋势</span>
          <span class="section-sub">近 {{ days }} 天</span>
        </div>
        <div ref="growthRef" class="h-240" style="margin-top:10px" />
      </div>

      <!-- 五力薄弱水平柱状图 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">五力薄弱分布</span>
          <span class="section-sub">错题归因占比</span>
        </div>
        <div ref="weakRef" class="h-240" style="margin-top:10px" />
      </div>

    </div><!-- /row-2 -->

    <!-- ── Row 3：正确率折线(5fr) + 完成率饼图(3fr) + 热门知识点(4fr) ── -->
    <div class="row-training">

      <!-- 答题正确率趋势 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">答题正确率趋势</span>
          <span class="section-sub">近 {{ days }} 天均值</span>
        </div>
        <div ref="accRef" class="h-200" style="margin-top:10px" />
      </div>

      <!-- 训练完成率饼图 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">训练完成率</span>
        </div>
        <div ref="complRef" class="h-200" style="margin-top:10px" />
        <!-- 图例 -->
        <div class="donut-legend">
          <span v-for="l in COMPL_LEGEND" :key="l.name" class="donut-legend__item">
            <span class="donut-legend__dot" :style="{ background: l.color }"></span>
            <span class="donut-legend__name">{{ l.name }}</span>
            <span class="donut-legend__val num">{{ l.pct }}%</span>
          </span>
        </div>
      </div>

      <!-- 热门知识点 Top 8 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">热门知识点 Top 8</span>
          <span class="section-sub">按训练次数</span>
        </div>
        <div class="kp-list">
          <div class="kp-row" v-for="(kp, idx) in HOT_KPS" :key="kp.id">
            <span class="kp-rank" :class="idx < 3 ? 'kp-rank--hot' : ''">{{ idx + 1 }}</span>
            <span class="kp-name">{{ kp.name }}</span>
            <div class="kp-track">
              <div class="kp-fill" :style="{ width: (kp.n / HOT_KPS[0].n * 100) + '%' }"></div>
            </div>
            <span class="kp-count num">{{ kp.n }}</span>
          </div>
        </div>
      </div>

    </div><!-- /row-training -->

    <!-- ── Row 4：AI效果摘要+会话模式(4fr) + 启发策略有效性(8fr) ── -->
    <div class="row-ai">

      <!-- AI效果摘要 + 会话模式 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">AI 助教效果</span>
        </div>
        <!-- 4个数字卡 -->
        <div class="ai-nums">
          <div class="ai-num-item">
            <div class="ai-num-val num" style="color:#4F46E5">{{ stats?.aha_moments_today ?? '--' }}</div>
            <div class="ai-num-label">理解突破次数</div>
          </div>
          <div class="ai-num-item">
            <div class="ai-num-val num" style="color:#22C55E">{{ ahaPct }}%</div>
            <div class="ai-num-label">突破率</div>
          </div>
          <div class="ai-num-item">
            <div class="ai-num-val num" style="color:#F59E0B">{{ stats?.chat_sessions_today ?? '--' }}</div>
            <div class="ai-num-label">对话会话数</div>
          </div>
          <div class="ai-num-item">
            <div class="ai-num-val num" style="color:#A855F7">{{ avgRounds }}</div>
            <div class="ai-num-label">平均对话轮数</div>
          </div>
        </div>
        <!-- 会话模式分布 -->
        <div class="row-divider"></div>
        <div class="section-title" style="margin-bottom:12px">会话模式分布</div>
        <div class="session-bars">
          <div class="session-bar-row" v-for="s in SESSION_MODES" :key="s.name">
            <span class="session-bar-name">{{ s.name }}</span>
            <div class="session-bar-track">
              <div class="session-bar-fill" :style="{ width: s.pct + '%', background: s.color }"></div>
            </div>
            <span class="session-bar-pct num" :style="{ color: s.color }">{{ s.pct }}%</span>
          </div>
        </div>
      </div>

      <!-- 启发策略有效性 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">启发策略有效性</span>
          <span class="section-sub">成功率 / 使用次数</span>
        </div>
        <div class="strategy-list">
          <div class="strategy-header">
            <span class="s-name">策略名称</span>
            <span class="s-bar">有效率</span>
            <span class="s-rate">成功率</span>
            <span class="s-uses">使用次数</span>
          </div>
          <div class="strategy-row" v-for="s in STRATEGIES" :key="s.id">
            <span class="s-name">{{ s.name }}</span>
            <div class="s-bar">
              <div class="s-bar-track">
                <div
                  class="s-bar-fill"
                  :style="{ width: s.rate + '%', background: strategyColor(s.rate) }"
                ></div>
              </div>
            </div>
            <span class="s-rate num" :style="{ color: strategyColor(s.rate) }">{{ s.rate }}%</span>
            <span class="s-uses num muted">{{ s.uses.toLocaleString() }}</span>
          </div>
        </div>
      </div>

    </div><!-- /row-ai -->

    <!-- ── Row 5：题库健康度(4fr) + Token消耗趋势+成本分布(8fr) ── -->
    <div class="row-bottom">

      <!-- 题库健康度面板 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">题库健康度</span>
          <router-link to="/questions" class="text-link">查看题库 →</router-link>
        </div>
        <!-- 状态数字行 -->
        <div class="bank-grid">
          <div class="bank-item">
            <div class="bank-item__value num">{{ stats?.published_questions?.toLocaleString() ?? '--' }}</div>
            <div class="bank-item__label">已发布</div>
          </div>
          <div class="bank-item">
            <div class="bank-item__value num" style="color:#94A3B8">{{ stats?.draft_questions ?? '--' }}</div>
            <div class="bank-item__label">草稿</div>
          </div>
          <div class="bank-item" @click="$router.push('/annotations')" style="cursor:pointer">
            <div class="bank-item__value num" style="color:#F59E0B">{{ stats?.pending_annotations ?? '--' }}</div>
            <div class="bank-item__label">待标注</div>
          </div>
          <div class="bank-item">
            <div class="bank-item__value num" style="color:#22C55E">{{ stats?.confirmed_annotations?.toLocaleString() ?? '--' }}</div>
            <div class="bank-item__label">已确认</div>
          </div>
        </div>
        <!-- 五力覆盖分布 -->
        <div class="row-divider"></div>
        <div class="section-title" style="margin-bottom:12px">五力覆盖分布</div>
        <div class="power-bars">
          <div class="power-bar-row" v-for="p in POWER_BARS" :key="p.key">
            <div class="power-bar-label" :style="{ color: p.color }">{{ p.name }}</div>
            <div class="power-bar-track">
              <div class="power-bar-fill" :style="{ width: p.pct + '%', background: p.color }"></div>
            </div>
            <div class="power-bar-val num" :style="{ color: p.color }">{{ p.pct }}%</div>
          </div>
        </div>
        <!-- 标注进度 -->
        <div class="row-divider"></div>
        <div class="annot-stats">
          <div class="annot-item">
            <span class="annot-val num" style="color:#4F46E5">{{ stats?.confirmed_annotations?.toLocaleString() ?? '--' }}</span>
            <span class="annot-label">已确认标注</span>
          </div>
          <div class="annot-item">
            <span class="annot-val num" style="color:#F59E0B">{{ stats?.pending_annotations ?? '--' }}</span>
            <span class="annot-label">待审核</span>
          </div>
          <div class="annot-item">
            <span class="annot-val num" style="color:#94A3B8">{{ stats?.pending_vectors ?? '--' }}</span>
            <span class="annot-label">待向量化</span>
          </div>
        </div>
      </div>

      <!-- Token 消耗趋势 + 成本分布 -->
      <div class="card">
        <div class="section-hd">
          <span class="section-title">Token 消耗趋势</span>
          <span class="section-sub">近 {{ days }} 天</span>
        </div>
        <!-- ECharts 面积图 -->
        <div ref="tokenRef" class="h-240" style="margin-top:10px" />
        <!-- 成本分布 -->
        <div class="row-divider" style="margin-top:16px"></div>
        <div class="cost-grid">
          <div class="cost-item" v-for="c in costBreakdown" :key="c.label">
            <div class="cost-item__amount num" :style="{ color: c.color }">${{ c.total.toFixed(2) }}</div>
            <div class="cost-item__meta">
              <span class="cost-item__dot" :style="{ background: c.color }"></span>
              <span class="cost-item__label">{{ c.label }}</span>
              <span class="cost-item__pct num" :style="{ color: c.color }">{{ c.pct }}%</span>
            </div>
            <div class="cost-item__bar">
              <div class="cost-item__fill" :style="{ width: c.pct + '%', background: c.color }"></div>
            </div>
          </div>
        </div>
      </div>

    </div><!-- /row-bottom -->

  </div><!-- /dash -->
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'
import type { DashboardStats, TokenTrend, UserGrowthPoint } from '@/types'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'

// ── 认证 Store ────────────────────────────────────────────────
const authStore = useAuthStore()

// ── 图表公共样式配置 ──────────────────────────────────────────
const CHART_TEXT_COLOR = '#94A3B8'
const CHART_SPLIT_LINE = 'rgba(79,70,229,0.06)'
const CHART_FONT = 'Inter, system-ui'

// ── 时间范围 ──────────────────────────────────────────────────
const TABS = [
  { v: 1,  l: '今日' },
  { v: 7,  l: '近7天' },
  { v: 30, l: '近30天' },
]
const days = ref(7)

// ── 数据状态 ──────────────────────────────────────────────────
const loading = ref(false)
const stats = ref<DashboardStats>()
const costBreakdown = ref([
  { label: '训练模块', color: '#4F46E5', pct: 63, total: 0 },
  { label: 'AI 助教',  color: '#14B8A6', pct: 33, total: 0 },
  { label: '测试模块', color: '#F59E0B', pct: 4,  total: 0 },
])

// ── ECharts 实例引用 ──────────────────────────────────────────
const growthRef = ref<HTMLElement>()
const weakRef   = ref<HTMLElement>()
const accRef    = ref<HTMLElement>()
const complRef  = ref<HTMLElement>()
const tokenRef  = ref<HTMLElement>()

let growthChart: echarts.ECharts | null = null
let weakChart:   echarts.ECharts | null = null
let accChart:    echarts.ECharts | null = null
let complChart:  echarts.ECharts | null = null
let tokenChart:  echarts.ECharts | null = null

// ── 硬编码静态数据 ───────────────────────────────────────────
/** 启发策略有效性 */
const STRATEGIES = [
  { id: 'S-SOCRATIC',     name: '苏格拉底提问', uses: 3241, rate: 81 },
  { id: 'S-ANALOGY-LIFE', name: '生活场景类比', uses: 2186, rate: 74 },
  { id: 'S-SIMPLIFY',     name: '化简特例',     uses: 1843, rate: 68 },
  { id: 'S-COUNTER',      name: '反例证伪',     uses: 1204, rate: 62 },
  { id: 'S-SPATIAL',      name: '空间想象',     uses: 892,  rate: 58 },
  { id: 'S-DIAGRAM',      name: '图示引导',     uses: 756,  rate: 55 },
  { id: 'S-STORY',        name: '故事叙述',     uses: 634,  rate: 51 },
  { id: 'S-PATTERN',      name: '节奏模式感',   uses: 521,  rate: 47 },
  { id: 'S-KNOWN',        name: '已知知识类比', uses: 389,  rate: 43 },
]

/** 热门知识点 Top 8 */
const HOT_KPS = [
  { id: 1001, name: '二元一次方程组应用题', n: 68 },
  { id: 1003, name: '一次函数图像与性质',   n: 55 },
  { id: 2008, name: '相似三角形判定',       n: 41 },
  { id: 1005, name: '分式方程求解',         n: 38 },
  { id: 3002, name: '浮力与压强综合',       n: 34 },
  { id: 1009, name: '二次函数最值应用',     n: 29 },
  { id: 2011, name: '圆的切线性质',         n: 24 },
  { id: 3007, name: '欧姆定律综合电路',     n: 21 },
]

/** 五力薄弱分布（错题归因） */
const WEAKNESS_DATA = [
  { key: 'CONSTRUCT', name: '建构力', pct: 38, color: '#ef4444' },
  { key: 'TRANSFER',  name: '迁移力', pct: 29, color: '#a855f7' },
  { key: 'ADAPT',     name: '调适力', pct: 18, color: '#f59e0b' },
  { key: 'DEDUCE',    name: '推演力', pct: 10, color: '#3b82f6' },
  { key: 'INSIGHT',   name: '洞察力', pct: 5,  color: '#22c55e' },
]

/** 五力覆盖分布（题库维度） */
const POWER_BARS = [
  { key: 'INSIGHT',   name: '洞察力', color: '#22c55e', pct: 28 },
  { key: 'CONSTRUCT', name: '建构力', color: '#ef4444', pct: 25 },
  { key: 'DEDUCE',    name: '推演力', color: '#3b82f6', pct: 22 },
  { key: 'ADAPT',     name: '调适力', color: '#f59e0b', pct: 15 },
  { key: 'MIGRATE',   name: '迁移力', color: '#a855f7', pct: 10 },
]

/** 训练完成率饼图图例 */
const COMPL_LEGEND = [
  { name: '正常完成', pct: 72, color: '#22C55E' },
  { name: '提前结束', pct: 18, color: '#F59E0B' },
  { name: '中途放弃', pct: 10, color: '#EF4444' },
]

/** 会话模式分布 */
const SESSION_MODES = [
  { name: '错题复盘', pct: 45, color: '#A855F7' },
  { name: '自由提问', pct: 35, color: '#4F46E5' },
  { name: '训练介入', pct: 20, color: '#22C55E' },
]

// ── 计算属性 ──────────────────────────────────────────────────
/** 今日日期中文格式 */
const todayLabel = computed(() => dayjs().format('YYYY年M月D日'))

/** 正确率百分比 */
const accPct = computed(() => ((stats.value?.avg_accuracy ?? 0) * 100).toFixed(0))
const accuracyClass = computed(() => {
  const v = stats.value?.avg_accuracy ?? 0
  return v >= 0.7 ? 'badge--up' : v < 0.5 ? 'badge--down' : ''
})

/** 降级率百分比 */
const degradePct = computed(() => ((stats.value?.degradation_rate ?? 0) * 100).toFixed(1))
const degradeClass = computed(() =>
  (stats.value?.degradation_rate ?? 0) > 0.05 ? 'badge--down' : ''
)

/** 理解突破率（aha / chat_sessions） */
const ahaPct = computed(() => {
  const sessions = stats.value?.chat_sessions_today ?? 0
  const aha = stats.value?.aha_moments_today ?? 0
  if (!sessions) return '--'
  return ((aha / sessions) * 100).toFixed(1)
})

/** 平均对话轮数（messages / sessions） */
const avgRounds = computed(() => {
  const sessions = stats.value?.chat_sessions_today ?? 0
  const msgs = stats.value?.chat_messages_today ?? 0
  if (!sessions) return '--'
  return (msgs / sessions).toFixed(1)
})

// ── 策略颜色辅助函数 ─────────────────────────────────────────
function strategyColor(rate: number): string {
  if (rate >= 70) return '#22C55E'
  if (rate >= 55) return '#4F46E5'
  return '#94A3B8'
}

// ── 数据加载函数 ─────────────────────────────────────────────
async function loadStats() {
  loading.value = true
  try {
    stats.value = await dashboardApi.getStats()
  } finally {
    loading.value = false
  }
}

async function loadGrowth() {
  const data = await dashboardApi.getUserGrowth(days.value)
  renderGrowthChart(data)
}

async function loadToken() {
  const data = await dashboardApi.getTokenTrend(days.value)
  renderTokenChart(data)
  // 计算成本分布
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

/** 时间范围切换 */
async function setDays(d: number) {
  days.value = d
  await Promise.all([loadGrowth(), loadToken()])
  // 正确率趋势也需要重新生成
  renderAccuracyChart()
}

// ── ECharts 渲染函数 ──────────────────────────────────────────

/** 1. 用户增长折线图 */
function renderGrowthChart(data: UserGrowthPoint[]) {
  if (!growthRef.value) return
  if (!growthChart) growthChart = echarts.init(growthRef.value)
  growthChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1E293B',
      borderColor: 'transparent',
      textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: CHART_FONT },
      extraCssText: 'border-radius:12px;box-shadow:0 8px 32px rgba(30,41,59,0.20);padding:12px 16px',
    },
    legend: {
      data: ['新增用户', '活跃用户'],
      top: 0, right: 0,
      textStyle: { color: CHART_TEXT_COLOR, fontSize: 12, fontFamily: CHART_FONT },
      icon: 'roundRect', itemWidth: 10, itemHeight: 10, itemGap: 16,
    },
    grid: { left: 40, right: 16, top: 36, bottom: 28 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: 'rgba(79,70,229,0.12)' } },
      axisLabel: { color: CHART_TEXT_COLOR, fontSize: 11, fontFamily: CHART_FONT },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: CHART_TEXT_COLOR, fontSize: 11, fontFamily: CHART_FONT },
      splitLine: { lineStyle: { color: CHART_SPLIT_LINE } },
      axisLine: { show: false },
    },
    series: [
      {
        name: '新增用户',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: data.map(d => d.new_users),
        itemStyle: { color: '#4F46E5' },
        lineStyle: { color: '#4F46E5', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79,70,229,0.14)' },
            { offset: 1, color: 'rgba(79,70,229,0)' },
          ]),
        },
      },
      {
        name: '活跃用户',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: data.map(d => d.active_users),
        itemStyle: { color: '#22C55E' },
        lineStyle: { color: '#22C55E', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34,197,94,0.10)' },
            { offset: 1, color: 'rgba(34,197,94,0)' },
          ]),
        },
      },
    ],
  })
}

/** 2. 五力薄弱水平柱状图 */
function renderWeaknessChart() {
  if (!weakRef.value) return
  if (!weakChart) weakChart = echarts.init(weakRef.value)
  // 从大到小排序（数据已按 pct 降序）
  const sorted = [...WEAKNESS_DATA].sort((a, b) => b.pct - a.pct)
  weakChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'none' },
      backgroundColor: '#1E293B',
      borderColor: 'transparent',
      textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: CHART_FONT },
      extraCssText: 'border-radius:12px;padding:10px 14px',
      formatter: (params: { name: string; value: number }[]) =>
        `${params[0].name}：${params[0].value}%`,
    },
    grid: { left: 60, right: 56, top: 10, bottom: 10 },
    xAxis: {
      type: 'value',
      max: 50,
      axisLabel: { show: false },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: CHART_SPLIT_LINE } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map(d => d.name),
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: CHART_TEXT_COLOR, fontSize: 12, fontFamily: CHART_FONT },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map(d => ({
          value: d.pct,
          itemStyle: { color: d.color, borderRadius: [0, 4, 4, 0] },
        })),
        barWidth: 16,
        label: {
          show: true,
          position: 'right',
          color: CHART_TEXT_COLOR,
          fontSize: 11,
          fontFamily: CHART_FONT,
          formatter: '{c}%',
        },
      },
    ],
  })
}

/** 3. 答题正确率折线图（基于 stats.avg_accuracy 加随机偏移生成） */
function renderAccuracyChart() {
  if (!accRef.value) return
  if (!accChart) accChart = echarts.init(accRef.value)
  const base = stats.value?.avg_accuracy ?? 0.63
  const n = days.value
  // 生成 n 天的模拟正确率，均值接近 base，±0.08 随机，clamp [0.3, 0.95]
  const xData: string[] = []
  const yData: number[] = []
  for (let i = 0; i < n; i++) {
    const date = new Date(Date.now() - (n - 1 - i) * 86400000)
    xData.push(`${date.getMonth() + 1}/${date.getDate()}`)
    const v = Math.min(0.95, Math.max(0.3, base + (Math.random() - 0.5) * 0.16))
    yData.push(parseFloat((v * 100).toFixed(1)))
  }
  accChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1E293B',
      borderColor: 'transparent',
      textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: CHART_FONT },
      extraCssText: 'border-radius:12px;padding:10px 14px',
      formatter: (params: { name: string; value: number }[]) =>
        `${params[0].name}：${params[0].value}%`,
    },
    grid: { left: 48, right: 16, top: 16, bottom: 28 },
    xAxis: {
      type: 'category',
      data: xData,
      axisLine: { lineStyle: { color: 'rgba(79,70,229,0.12)' } },
      axisLabel: { color: CHART_TEXT_COLOR, fontSize: 11, fontFamily: CHART_FONT },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0, max: 100,
      axisLabel: { color: CHART_TEXT_COLOR, fontSize: 11, fontFamily: CHART_FONT, formatter: '{value}%' },
      splitLine: { lineStyle: { color: CHART_SPLIT_LINE } },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: yData,
        itemStyle: { color: '#4F46E5' },
        lineStyle: { color: '#4F46E5', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79,70,229,0.14)' },
            { offset: 1, color: 'rgba(79,70,229,0)' },
          ]),
        },
      },
    ],
  })
}

/** 4. 训练完成率饼图（donut） */
function renderCompletionChart() {
  if (!complRef.value) return
  if (!complChart) complChart = echarts.init(complRef.value)
  complChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1E293B',
      borderColor: 'transparent',
      textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: CHART_FONT },
      extraCssText: 'border-radius:12px;padding:10px 14px',
      formatter: '{b}: {c}%',
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        label: { show: false },
        emphasis: { scale: false },
        data: [
          { value: 72, name: '正常完成', itemStyle: { color: '#22C55E' } },
          { value: 18, name: '提前结束', itemStyle: { color: '#F59E0B' } },
          { value: 10, name: '中途放弃', itemStyle: { color: '#EF4444' } },
        ],
      },
    ],
  })
}

/** 5. Token 消耗趋势面积图（3条系列） */
function renderTokenChart(data: TokenTrend[]) {
  if (!tokenRef.value) return
  if (!tokenChart) tokenChart = echarts.init(tokenRef.value)
  tokenChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1E293B',
      borderColor: 'transparent',
      textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: CHART_FONT },
      extraCssText: 'border-radius:12px;box-shadow:0 8px 32px rgba(30,41,59,0.20);padding:12px 16px',
      formatter: (params: { name: string; color: string; seriesName: string; value: number }[]) => {
        let s = `<div style="margin-bottom:8px;font-weight:600;color:#94A3B8;font-size:11px">${params[0].name}</div>`
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
      top: 0, right: 0,
      textStyle: { color: CHART_TEXT_COLOR, fontSize: 12, fontFamily: CHART_FONT },
      icon: 'roundRect', itemWidth: 10, itemHeight: 10, itemGap: 16,
    },
    grid: { left: 40, right: 16, top: 36, bottom: 28 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: 'rgba(79,70,229,0.12)' } },
      axisLabel: { color: CHART_TEXT_COLOR, fontSize: 11, fontFamily: CHART_FONT },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: CHART_TEXT_COLOR, fontSize: 11, fontFamily: CHART_FONT, formatter: '${value}' },
      splitLine: { lineStyle: { color: CHART_SPLIT_LINE } },
      axisLine: { show: false },
    },
    series: [
      {
        name: '训练模块',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: data.map(d => d.training_cost),
        itemStyle: { color: '#4F46E5' },
        lineStyle: { color: '#4F46E5', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79,70,229,0.12)' },
            { offset: 1, color: 'rgba(79,70,229,0)' },
          ]),
        },
      },
      {
        name: 'AI助教',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: data.map(d => d.assistant_cost),
        itemStyle: { color: '#14B8A6' },
        lineStyle: { color: '#14B8A6', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(20,184,166,0.10)' },
            { offset: 1, color: 'rgba(20,184,166,0)' },
          ]),
        },
      },
      {
        name: '测试模块',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: data.map(d => d.test_cost),
        itemStyle: { color: '#F59E0B' },
        lineStyle: { color: '#F59E0B', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245,158,11,0.08)' },
            { offset: 1, color: 'rgba(245,158,11,0)' },
          ]),
        },
      },
    ],
  })
}

// ── Resize 处理 ───────────────────────────────────────────────
function handleResize() {
  ;[growthChart, weakChart, accChart, complChart, tokenChart].forEach(c => c?.resize())
}

// ── 生命周期 ──────────────────────────────────────────────────
onMounted(async () => {
  // 1. 先加载统计数据
  await loadStats()
  // 2. 等待 DOM 渲染
  await nextTick()
  // 3. 并行加载趋势数据
  await Promise.all([loadGrowth(), loadToken()])
  // 4. 渲染静态数据图表
  renderWeaknessChart()
  renderCompletionChart()
  renderAccuracyChart()
  // 5. 注册 resize 监听
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  ;[growthChart, weakChart, accChart, complChart, tokenChart].forEach(c => c?.dispose())
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
/* ── 根容器 ───────────────────────────────────────────────── */
.dash {
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-family: 'Inter', system-ui, sans-serif;
}

/* 等宽数字字体 */
.num {
  font-family: 'JetBrains Mono', monospace;
}
.muted {
  color: #94A3B8;
}

/* ── 卡片基础 ─────────────────────────────────────────────── */
.card {
  background: #FFFFFF;
  border-radius: 18px;
  padding: 20px 22px;
  box-shadow: 0 2px 8px rgba(79,70,229,0.06);
  transition: box-shadow 200ms, transform 200ms;
}
.card:hover {
  box-shadow: 0 6px 24px rgba(79,70,229,0.12);
  transform: translateY(-2px);
}

/* ── 图表高度辅助类 ─────────────────────────────────────────── */
.h-240 { height: 240px; }
.h-200 { height: 200px; }
.h-160 { height: 160px; }
.h-120 { height: 120px; }

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
.welcome-name { color: #4F46E5; }
.welcome-date {
  font-size: 13px;
  color: #94A3B8;
  margin: 0;
}
.welcome-right {
  display: flex;
  align-items: center;
}

/* ── KPI 网格行 ───────────────────────────────────────────── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

/* KPI 卡片内部 */
.kpi-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}
.kpi-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.kpi-label {
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  flex: 1;
}
.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: #1E293B;
  letter-spacing: -0.04em;
  line-height: 1;
  margin-bottom: 10px;
}
.kpi-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.kpi-sub {
  font-size: 12px;
  color: #94A3B8;
}

/* 趋势胶囊 */
.badge {
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 9999px;
  background: #F1F5F9;
  color: #64748B;
  white-space: nowrap;
}
.badge--up {
  background: rgba(34,197,94,0.12);
  color: #16A34A;
}
.badge--down {
  background: rgba(239,68,68,0.10);
  color: #DC2626;
}

/* ── Section 头部 ─────────────────────────────────────────── */
.section-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  letter-spacing: -0.01em;
}
.section-sub {
  font-size: 12px;
  color: #94A3B8;
}
.text-link {
  font-size: 12px;
  color: #4F46E5;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 150ms;
}
.text-link:hover { opacity: 0.75; }

/* ── 分隔线 ───────────────────────────────────────────────── */
.row-divider {
  height: 1px;
  background: #F1F5F9;
  margin: 16px 0 12px;
}

/* ── Row 布局 ─────────────────────────────────────────────── */
.row-2 {
  display: grid;
  grid-template-columns: 6fr 4fr;
  gap: 20px;
}
.row-training {
  display: grid;
  grid-template-columns: 5fr 3fr 4fr;
  gap: 20px;
}
.row-ai {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: 20px;
}
.row-bottom {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: 20px;
}

/* ── 热门知识点列表 ──────────────────────────────────────── */
.kp-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}
.kp-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.kp-rank {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  background: #F1F5F9;
  color: #94A3B8;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.kp-rank--hot {
  background: rgba(79,70,229,0.10);
  color: #4F46E5;
}
.kp-name {
  flex: 1;
  font-size: 12px;
  color: #475569;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kp-track {
  width: 64px;
  height: 5px;
  background: #F1F5F9;
  border-radius: 3px;
  overflow: hidden;
  flex-shrink: 0;
}
.kp-fill {
  height: 100%;
  background: #4F46E5;
  border-radius: 3px;
  opacity: 0.65;
  transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
}
.kp-count {
  width: 28px;
  font-size: 11.5px;
  color: #64748B;
  font-weight: 600;
  text-align: right;
  flex-shrink: 0;
}

/* ── AI 效果数字卡网格 ────────────────────────────────────── */
.ai-nums {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 0;
}
.ai-num-item {
  background: #FAFBFF;
  border-radius: 12px;
  padding: 12px 14px;
}
.ai-num-val {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
  margin-bottom: 4px;
}
.ai-num-label {
  font-size: 11px;
  color: #94A3B8;
}

/* ── 会话模式进度条 ──────────────────────────────────────── */
.session-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.session-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.session-bar-name {
  width: 56px;
  font-size: 12px;
  color: #64748B;
  flex-shrink: 0;
}
.session-bar-track {
  flex: 1;
  height: 8px;
  background: #F1F5F9;
  border-radius: 4px;
  overflow: hidden;
}
.session-bar-fill {
  height: 100%;
  border-radius: 4px;
  opacity: 0.80;
  transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
}
.session-bar-pct {
  width: 36px;
  font-size: 11.5px;
  font-weight: 700;
  text-align: right;
  flex-shrink: 0;
}

/* ── 启发策略有效性列表 ────────────────────────────────────── */
.strategy-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
}
.strategy-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #F1F5F9;
  font-size: 11px;
  color: #94A3B8;
  font-weight: 500;
}
.strategy-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.s-name {
  width: 88px;
  font-size: 12.5px;
  color: #475569;
  flex-shrink: 0;
  white-space: nowrap;
}
.s-bar {
  flex: 1;
}
.s-bar-track {
  height: 5px;
  background: #F1F5F9;
  border-radius: 3px;
  overflow: hidden;
}
.s-bar-fill {
  height: 100%;
  border-radius: 3px;
  opacity: 0.80;
  transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
}
.s-rate {
  width: 40px;
  font-size: 12px;
  font-weight: 700;
  text-align: right;
  flex-shrink: 0;
}
.s-uses {
  width: 56px;
  font-size: 11px;
  text-align: right;
  flex-shrink: 0;
}

/* ── 题库健康度 bank-grid ────────────────────────────────── */
.bank-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid #F1F5F9;
  border-radius: 12px;
  overflow: hidden;
  margin-top: 12px;
}
.bank-item {
  padding: 12px 8px;
  text-align: center;
  border-right: 1px solid #F1F5F9;
  transition: background 150ms;
}
.bank-item:last-child { border-right: none; }
.bank-item:hover { background: #FAFBFF; }
.bank-item__value {
  font-size: 22px;
  font-weight: 700;
  color: #1E293B;
  letter-spacing: -0.04em;
  line-height: 1;
  margin-bottom: 4px;
}
.bank-item__label {
  font-size: 10.5px;
  color: #94A3B8;
  font-weight: 500;
}

/* ── 五力覆盖进度条 ──────────────────────────────────────── */
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
.power-bar-label {
  font-size: 12px;
  font-weight: 600;
  width: 40px;
  flex-shrink: 0;
}
.power-bar-track {
  flex: 1;
  height: 5px;
  background: #F1F5F9;
  border-radius: 3px;
  overflow: hidden;
}
.power-bar-fill {
  height: 100%;
  border-radius: 3px;
  opacity: 0.80;
  transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
}
.power-bar-val {
  font-size: 11.5px;
  font-weight: 600;
  width: 32px;
  text-align: right;
  flex-shrink: 0;
}

/* ── 标注进度统计 ─────────────────────────────────────────── */
.annot-stats {
  display: flex;
  gap: 24px;
}
.annot-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.annot-val {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.annot-label {
  font-size: 11px;
  color: #94A3B8;
}

/* ── Token 成本分布 ───────────────────────────────────────── */
.cost-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 4px;
}
.cost-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cost-item__amount {
  font-size: 26px;
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

/* ── 训练完成率图例 ───────────────────────────────────────── */
.donut-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.donut-legend__item {
  display: flex;
  align-items: center;
  gap: 5px;
}
.donut-legend__dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}
.donut-legend__name {
  font-size: 11px;
  color: #64748B;
}
.donut-legend__val {
  font-size: 11px;
  font-weight: 700;
  color: #475569;
}

/* ── 响应式 ───────────────────────────────────────────────── */
@media (max-width: 1200px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .row-training {
    grid-template-columns: 1fr;
  }
  .row-ai {
    grid-template-columns: 1fr;
  }
  .row-bottom {
    grid-template-columns: 1fr;
  }
  .row-2 {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 700px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .cost-grid {
    grid-template-columns: 1fr;
  }
  .welcome-bar {
    flex-direction: column;
    align-items: flex-start;
  }
  .bank-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

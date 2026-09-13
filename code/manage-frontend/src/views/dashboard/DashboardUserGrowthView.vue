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
          <h1 class="page-title">用户增长分析</h1>
          <p class="page-subtitle">用户注册、活跃趋势及留存漏斗分析</p>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <el-radio-group v-model="days" size="small" @change="loadData">
          <el-radio-button :value="7">近7天</el-radio-button>
          <el-radio-button :value="30">近30天</el-radio-button>
          <el-radio-button :value="90">近90天</el-radio-button>
        </el-radio-group>
        <el-button size="small">导出 CSV</el-button>
      </div>
    </div>

    <div v-loading="loading">

      <!-- 每日新增用户折线图 -->
      <div class="surface chart-card">
        <div class="section-hd">
          <span class="section-title">每日新增 & 活跃用户趋势</span>
        </div>
        <div ref="growthRef" style="height:280px;margin-top:12px" />
      </div>

      <!-- 留存漏斗 + 年级分布 -->
      <div class="two-cols">

        <div class="surface chart-card">
          <div class="section-hd">
            <span class="section-title">用户留存漏斗</span>
          </div>
          <div class="funnel-list">
            <div v-for="item in data?.retention_funnel" :key="item.stage" class="funnel-row">
              <span class="funnel-stage">{{ item.stage }}</span>
              <div class="funnel-bar-wrap">
                <div class="funnel-bar" :style="{ width: item.pct + '%' }" />
              </div>
              <span class="funnel-count num">{{ item.count.toLocaleString() }}</span>
              <span class="funnel-pct num">{{ item.pct }}%</span>
            </div>
          </div>
        </div>

        <div class="surface chart-card">
          <div class="section-hd">
            <span class="section-title">年级分布</span>
          </div>
          <div ref="gradeRef" style="height:220px;margin-top:12px" />
        </div>

      </div>

      <!-- 学科偏好 -->
      <div class="surface chart-card">
        <div class="section-hd">
          <span class="section-title">学科偏好分布</span>
          <span style="font-size:12.5px;color:var(--text-3)">学生可多选</span>
        </div>
        <div class="subject-bars">
          <div v-for="sub in data?.subject_preference" :key="sub.subject" class="subject-row">
            <span class="subject-name">{{ sub.subject }}</span>
            <div class="subject-track">
              <div class="subject-fill" :style="{ width: sub.pct + '%' }" />
            </div>
            <span class="subject-pct num">{{ sub.pct }}%</span>
          </div>
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
const data = ref<Record<string, unknown> | null>(null)

const growthRef = ref<HTMLElement>()
const gradeRef  = ref<HTMLElement>()
let growthChart: echarts.ECharts | undefined
let gradeChart:  echarts.ECharts | undefined

const CHART_TEXT = '#94A3B8'
const CHART_SPLIT = 'rgba(79,70,229,0.06)'

async function loadData() {
  loading.value = true
  try {
    data.value = await dashboardApi.getUserGrowthDetail(days.value)
    await nextTick()
    renderGrowthChart()
    renderGradeChart()
  } finally { loading.value = false }
}

function renderGrowthChart() {
  if (!growthRef.value || !data.value) return
  if (!growthChart) growthChart = echarts.init(growthRef.value)
  const daily = data.value.daily_new_users as { date: string; new_users: number; active_users: number }[]
  growthChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1E293B', borderColor: 'transparent', textStyle: { color: '#F8FAFC', fontSize: 12 }, extraCssText: 'border-radius:12px;padding:12px 16px' },
    legend: { data: ['新增用户', '活跃用户'], top: 0, right: 0, textStyle: { color: CHART_TEXT, fontSize: 12 }, icon: 'roundRect', itemWidth: 10, itemHeight: 10 },
    grid: { left: 40, right: 16, top: 36, bottom: 28 },
    xAxis: { type: 'category', data: daily.map(d => d.date.slice(5)), axisLine: { lineStyle: { color: 'rgba(79,70,229,0.12)' } }, axisLabel: { color: CHART_TEXT, fontSize: 11 }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: CHART_TEXT, fontSize: 11 }, splitLine: { lineStyle: { color: CHART_SPLIT } }, axisLine: { show: false } },
    series: [
      { name: '新增用户', type: 'line', smooth: true, showSymbol: false, data: daily.map(d => d.new_users), itemStyle: { color: '#4F46E5' }, lineStyle: { color: '#4F46E5', width: 2.5 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(79,70,229,0.14)'},{offset:1,color:'rgba(79,70,229,0)'}]) } },
      { name: '活跃用户', type: 'line', smooth: true, showSymbol: false, data: daily.map(d => d.active_users), itemStyle: { color: '#22C55E' }, lineStyle: { color: '#22C55E', width: 2.5 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(34,197,94,0.10)'},{offset:1,color:'rgba(34,197,94,0)'}]) } },
    ],
  })
}

function renderGradeChart() {
  if (!gradeRef.value || !data.value) return
  if (!gradeChart) gradeChart = echarts.init(gradeRef.value)
  const grades = data.value.grade_distribution as { grade: string; count: number; pct: number }[]
  const colors = ['#4F46E5', '#8B5CF6', '#0D9488', '#F59E0B', '#EF4444', '#10B981']
  gradeChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', backgroundColor: '#1E293B', borderColor: 'transparent', textStyle: { color: '#F8FAFC', fontSize: 12 }, extraCssText: 'border-radius:12px;padding:10px 14px', formatter: '{b}: {c}人 ({d}%)' },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '55%'],
      avoidLabelOverlap: false,
      label: { show: true, color: CHART_TEXT, fontSize: 11, formatter: '{b}\n{d}%' },
      data: grades.map((g, i) => ({ value: g.count, name: g.grade, itemStyle: { color: colors[i % colors.length] } })),
    }],
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

// 留存漏斗
.funnel-list { display: flex; flex-direction: column; gap: 14px; margin-top: 16px; }

.funnel-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.funnel-stage {
  font-size: 13px;
  color: var(--text-2);
  min-width: 100px;
}

.funnel-bar-wrap {
  flex: 1;
  height: 10px;
  background: var(--bg-muted);
  border-radius: 5px;
  overflow: hidden;
}

.funnel-bar {
  height: 100%;
  background: linear-gradient(90deg, #4F46E5, #8B5CF6);
  border-radius: 5px;
  transition: width 0.6s ease;
}

.funnel-count {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-1);
  min-width: 60px;
  text-align: right;
}

.funnel-pct {
  font-size: 12px;
  color: var(--text-3);
  min-width: 40px;
  text-align: right;
}

// 学科偏好
.subject-bars { display: flex; flex-direction: column; gap: 16px; margin-top: 16px; }

.subject-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.subject-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-1);
  min-width: 40px;
}

.subject-track {
  flex: 1;
  height: 12px;
  background: var(--bg-muted);
  border-radius: 6px;
  overflow: hidden;
}

.subject-fill {
  height: 100%;
  background: var(--indigo);
  border-radius: 6px;
  opacity: 0.8;
  transition: width 0.6s ease;
}

.subject-pct {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-2);
  min-width: 40px;
  text-align: right;
}
</style>

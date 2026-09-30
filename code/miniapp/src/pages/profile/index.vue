<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { profileApi } from '@/api'
import { useAuthStore } from '@/store'
import { PAGES, FIVE_POWERS, FIVE_POWER_LABELS, FIVE_POWER_COLORS } from '@/constants'
import { getPowerLevel, formatDate } from '@/utils'
import type { FivePowerProfile } from '@/api/profile'

const authStore = useAuthStore()

// ── 数据状态 ──────────────────────────────────────────────────────────────
const fivePower = ref<FivePowerProfile | null>(null)
const loading = ref(true)
const showGrowthTrend = ref(false)

// ── 是否可以重测（≥30天） ─────────────────────────────────────────────────
// 这里简化：实际应对比 profile 的 created_at
const canRetest = ref(true) // 实际应从接口获取创建时间比对

// ── 五力雷达图配置（SVG） ──────────────────────────────────────────────────
const SVG_CX = 375
const SVG_CY = 375
const SVG_R = 260

function calcRadarPoints(scores: number[]): string {
  return scores
    .map((score, i) => {
      const angle = ((i * 72 - 90) * Math.PI) / 180
      const r = (score / 100) * SVG_R
      return `${SVG_CX + r * Math.cos(angle)},${SVG_CY + r * Math.sin(angle)}`
    })
    .join(' ')
}

const bgGridPoints = [1.0, 0.6, 0.3].map((ratio) =>
  calcRadarPoints([100, 100, 100, 100, 100].map((v) => v * ratio))
)

const axisPoints = FIVE_POWERS.map((_, i) => {
  const angle = ((i * 72 - 90) * Math.PI) / 180
  return { x2: SVG_CX + SVG_R * Math.cos(angle), y2: SVG_CY + SVG_R * Math.sin(angle) }
})

const labelPositions = FIVE_POWERS.map((_, i) => {
  const angle = ((i * 72 - 90) * Math.PI) / 180
  const r = SVG_R + 52
  return { x: SVG_CX + r * Math.cos(angle), y: SVG_CY + r * Math.sin(angle) }
})

// ── 计算分数 ──────────────────────────────────────────────────────────────
const scores = computed(() => {
  if (!fivePower.value?.profile) return FIVE_POWERS.map(() => 0)
  const forces = fivePower.value.profile.forces
  return FIVE_POWERS.map((p) => Math.round((forces[p]?.final ?? 0) * 100))
})

const radarPoints = computed(() => calcRadarPoints(scores.value))

// 维度详细信息列表
const dimensionRows = computed(() =>
  FIVE_POWERS.map((power, idx) => ({
    power,
    label: FIVE_POWER_LABELS[power],
    color: FIVE_POWER_COLORS[power],
    score: scores.value[idx],
    level: getPowerLevel(scores.value[idx]),
    abilityScore: fivePower.value?.profile
      ? Math.round((fivePower.value.profile.forces[power]?.ability ?? 0) * 100)
      : 0,
    preferScore: fivePower.value?.profile
      ? Math.round((fivePower.value.profile.forces[power]?.preference ?? 0) * 100)
      : 0,
  }))
)

// 整体评级
const overallScore = computed(() => {
  if (!scores.value.length) return 0
  return Math.round(scores.value.reduce((a, b) => a + b, 0) / scores.value.length)
})

onMounted(async () => {
  try {
    fivePower.value = await profileApi.getFivePower()
  } catch {
    fivePower.value = { has_profile: false, profile: null, training_profile: null }
  } finally {
    loading.value = false
  }
})

function goToTest() {
  uni.navigateTo({ url: PAGES.TEST_HOME })
}

function goToWrongAnswers() {
  uni.navigateTo({ url: PAGES.WRONG_ANSWERS })
}

function goToTraining() {
  uni.switchTab({ url: PAGES.TRAINING_HOME })
}
</script>

<template>
  <view class="profile-page">
    <!-- ── 顶部用户信息 + 重测按钮 ─────────────────────────── -->
    <view class="user-header">
      <view class="user-info">
        <view class="avatar">
          <text class="avatar__icon">🧑‍🎓</text>
        </view>
        <view class="user-detail">
          <text class="user-name">{{ authStore.userInfo?.nickname || '同学' }}</text>
          <text class="user-grade">
            {{ authStore.userInfo?.grade || '--' }}
            {{ authStore.userInfo?.semester === 'S1' ? '上学期' : authStore.userInfo?.semester === 'S2' ? '下学期' : '' }}
          </text>
        </view>
      </view>
      <button v-if="canRetest" class="retest-btn" @tap="goToTest">
        <text class="retest-btn__text">重测五力</text>
      </button>
    </view>

    <!-- ── 加载骨架 ─────────────────────────────────────────── -->
    <view v-if="loading" class="skeleton-card">
      <view class="skel-block skel-block--radar" />
      <view class="skel-lines">
        <view v-for="i in 5" :key="i" class="skel-line" />
      </view>
    </view>

    <!-- ── 无画像空态 ──────────────────────────────────────── -->
    <view v-else-if="!fivePower?.has_profile" class="no-profile-card">
      <text class="no-profile-icon">🧬</text>
      <text class="no-profile-title">尚未完成五力测试</text>
      <text class="no-profile-desc">完成测试后，这里将展示你的五力认知画像</text>
      <button class="go-test-btn" @tap="goToTest">立即测试</button>
    </view>

    <template v-else>
      <!-- ── 综合分数 ─────────────────────────────────────── -->
      <view class="overall-card">
        <view class="overall-score-wrap">
          <text class="overall-score">{{ overallScore }}</text>
          <text class="overall-unit">/100</text>
        </view>
        <view class="overall-info">
          <text class="overall-label">综合五力评分</text>
          <view
            class="overall-level"
            :style="{
              background: getPowerLevel(overallScore).color + '20',
              color: getPowerLevel(overallScore).color,
            }"
          >
            <text class="overall-level__text">{{ getPowerLevel(overallScore).label }}</text>
          </view>
        </view>
      </view>

      <!-- ── 五力雷达图 SVG ──────────────────────────────── -->
      <view class="radar-card">
        <text class="card-title">五力分布图</text>
        <view class="radar-wrap">
          <svg class="radar-svg" viewBox="0 0 750 750" xmlns="http://www.w3.org/2000/svg">
            <!-- 背景网格 -->
            <polygon
              v-for="(pts, gi) in bgGridPoints"
              :key="gi"
              :points="pts"
              fill="none"
              stroke="#E2E8F0"
              stroke-width="2"
            />
            <!-- 轴线 -->
            <line
              v-for="(ax, ai) in axisPoints"
              :key="ai"
              :x1="SVG_CX" :y1="SVG_CY"
              :x2="ax.x2" :y2="ax.y2"
              stroke="#E2E8F0" stroke-width="2"
            />
            <!-- 数据多边形 -->
            <polygon
              :points="radarPoints"
              fill="rgba(79, 70, 229, 0.15)"
              stroke="#4F46E5"
              stroke-width="4"
              stroke-linejoin="round"
            />
            <!-- 维度标签 -->
            <text
              v-for="(lp, li) in labelPositions"
              :key="li"
              :x="lp.x" :y="lp.y"
              font-size="28"
              text-anchor="middle"
              dominant-baseline="middle"
              :fill="FIVE_POWER_COLORS[FIVE_POWERS[li]]"
              font-weight="600"
            >{{ FIVE_POWER_LABELS[FIVE_POWERS[li]] }}</text>
            <!-- 数据点（分开循环避免 v-if + v-for 混用） -->
            <template v-for="(score, si) in scores" :key="si">
              <circle
                :cx="SVG_CX + (score / 100) * SVG_R * Math.cos(((si * 72 - 90) * Math.PI) / 180)"
                :cy="SVG_CY + (score / 100) * SVG_R * Math.sin(((si * 72 - 90) * Math.PI) / 180)"
                r="10"
                :fill="FIVE_POWER_COLORS[FIVE_POWERS[si]]"
              />
            </template>
          </svg>
        </view>
      </view>

      <!-- ── 五力维度详情 ─────────────────────────────────── -->
      <view class="dimension-card">
        <text class="card-title">五力详细评分</text>
        <view class="dimension-list">
          <view
            v-for="row in dimensionRows"
            :key="row.power"
            class="dimension-row"
          >
            <view class="dim-left">
              <view class="color-dot" :style="{ background: row.color }" />
              <text class="dim-name">{{ row.label }}</text>
            </view>
            <view class="dim-bar-wrap">
              <view class="dim-bar" :style="{ width: `${row.score}%`, background: row.color }" />
            </view>
            <view class="dim-right">
              <text class="dim-score" :style="{ color: row.color }">{{ row.score }}</text>
              <view class="dim-level" :style="{ background: row.level.color + '20', color: row.level.color }">
                <text class="dim-level__text">{{ row.level.label }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- ── 成长趋势（可折叠） ──────────────────────────── -->
      <view class="trend-card">
        <view class="trend-header" @tap="showGrowthTrend = !showGrowthTrend">
          <text class="card-title">成长趋势</text>
          <text class="trend-toggle">{{ showGrowthTrend ? '收起 ▲' : '展开 ▼' }}</text>
        </view>
        <view v-if="showGrowthTrend" class="trend-content">
          <!-- 折线图占位 —— 实际可使用 echarts 或 canvas -->
          <view class="trend-placeholder">
            <text class="trend-placeholder__icon">📈</text>
            <text class="trend-placeholder__text">连续训练后，成长曲线将在此展示</text>
          </view>
        </view>
      </view>

      <!-- ── AI 分析文本 ──────────────────────────────────── -->
      <view v-if="fivePower?.profile?.ai_analysis_text" class="ai-analysis-card">
        <view class="ai-analysis-header">
          <text class="ai-icon">🤖</text>
          <text class="card-title">AI 画像分析</text>
        </view>
        <text class="ai-analysis-text">{{ fivePower.profile.ai_analysis_text }}</text>
      </view>
    </template>

    <!-- ── 底部导航按钮 ──────────────────────────────────── -->
    <view class="nav-btns">
      <view class="nav-btn" @tap="goToWrongAnswers">
        <text class="nav-btn__icon">📋</text>
        <text class="nav-btn__text">错题集</text>
      </view>
      <view class="nav-btn nav-btn--primary" @tap="goToTraining">
        <text class="nav-btn__icon">🚀</text>
        <text class="nav-btn__text">开始训练</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>

.profile-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-4;
  padding-bottom: 160rpx;
}

// 用户头部
.user-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-4;
}

.user-info {
  display: flex;
  align-items: center;
  gap: $space-3;
}

.avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: $primary-light;
  display: flex;
  align-items: center;
  justify-content: center;

  &__icon { font-size: 52rpx; }
}

.user-detail {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.user-name {
  font-size: $font-size-lg;
  color: $text-1;
  font-weight: 700;
}

.user-grade {
  font-size: $font-size-sm;
  color: $text-3;
}

.retest-btn {
  height: 68rpx;
  padding: 0 $space-3;
  background: $primary-light;
  border: 2rpx solid $primary;
  border-radius: $r-pill;

  &::after { border: none; }

  &__text {
    font-size: $font-size-sm;
    color: $primary;
    font-weight: 600;
  }
}

// 骨架屏
.skeleton-card {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  margin-bottom: $space-4;
  box-shadow: $shadow-sm;
}

.skel-block {
  background: $bg-muted;
  border-radius: $r-md;
  animation: shimmer 1.2s ease-in-out infinite;

  &--radar {
    width: 100%;
    height: 400rpx;
    margin-bottom: $space-4;
  }
}

.skel-lines {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.skel-line {
  height: 48rpx;
  background: $bg-muted;
  border-radius: $r-md;
  animation: shimmer 1.2s ease-in-out infinite;
}

// 无画像
.no-profile-card {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-6;
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
  margin-bottom: $space-4;
}

.no-profile-icon { font-size: 80rpx; }

.no-profile-title {
  font-size: $font-size-lg;
  color: $text-1;
  font-weight: 700;
}

.no-profile-desc {
  font-size: $font-size-sm;
  color: $text-3;
  text-align: center;
  line-height: 1.7;
}

.go-test-btn {
  height: 88rpx;
  padding: 0 $space-5;
  background: $pink;
  border-radius: $r-pill;
  border: none;
  font-size: $font-size-base;
  color: #fff;
  font-weight: 700;

  &::after { border: none; }
}

// 综合分卡
.overall-card {
  background: linear-gradient(135deg, $primary 0%, #7C3AED 100%);
  border-radius: $r-xl;
  padding: $space-4;
  display: flex;
  align-items: center;
  gap: $space-4;
  margin-bottom: $space-4;
  box-shadow: $shadow-md;
}

.overall-score-wrap {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.overall-score {
  font-size: 80rpx;
  color: #fff;
  font-weight: 800;
  line-height: 1;
}

.overall-unit {
  font-size: $font-size-sm;
  color: rgba(255,255,255,0.7);
}

.overall-info {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.overall-label {
  font-size: $font-size-sm;
  color: rgba(255,255,255,0.85);
}

.overall-level {
  display: inline-flex;
  padding: 4rpx 20rpx;
  border-radius: $r-pill;
  align-self: flex-start;

  &__text {
    font-size: $font-size-xs;
    font-weight: 700;
  }
}

// 通用卡片
.radar-card,
.dimension-card,
.trend-card,
.ai-analysis-card {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  margin-bottom: $space-4;
  box-shadow: $shadow-sm;
}

.card-title {
  font-size: $font-size-lg;
  color: $text-1;
  font-weight: 700;
  display: block;
  margin-bottom: $space-3;
}

// 雷达图
.radar-wrap {
  display: flex;
  justify-content: center;
}

.radar-svg {
  width: 560rpx;
  height: 560rpx;
}

// 维度列表
.dimension-list {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.dimension-row {
  display: flex;
  align-items: center;
  gap: $space-2;
}

.dim-left {
  display: flex;
  align-items: center;
  gap: $space-2;
  width: 120rpx;
  flex-shrink: 0;
}

.color-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.dim-name {
  font-size: $font-size-sm;
  color: $text-2;
  font-weight: 500;
}

.dim-bar-wrap {
  flex: 1;
  height: 16rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  overflow: hidden;
}

.dim-bar {
  height: 100%;
  border-radius: $r-pill;
  transition: width 0.6s ease;
}

.dim-right {
  display: flex;
  align-items: center;
  gap: $space-2;
  width: 160rpx;
  justify-content: flex-end;
  flex-shrink: 0;
}

.dim-score {
  font-size: $font-size-lg;
  font-weight: 800;
  min-width: 60rpx;
  text-align: right;
}

.dim-level {
  padding: 4rpx 12rpx;
  border-radius: $r-pill;

  &__text {
    font-size: $font-size-xs;
    font-weight: 600;
  }
}

// 趋势卡
.trend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.trend-toggle {
  font-size: $font-size-xs;
  color: $primary;
}

.trend-content {
  margin-top: $space-3;
}

.trend-placeholder {
  height: 200rpx;
  background: $bg-muted;
  border-radius: $r-lg;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $space-2;
}

.trend-placeholder__icon { font-size: 48rpx; }

.trend-placeholder__text {
  font-size: $font-size-xs;
  color: $text-3;
}

// AI 分析
.ai-analysis-header {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-3;
}

.ai-icon { font-size: 36rpx; }

.ai-analysis-text {
  font-size: $font-size-base;
  color: $text-2;
  line-height: 1.9;
}

// 底部导航
.nav-btns {
  display: flex;
  gap: $space-3;
}

.nav-btn {
  flex: 1;
  height: 88rpx;
  background: $bg-surface;
  border: 2rpx solid $border;
  border-radius: $r-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;
  box-shadow: $shadow-sm;

  &--primary {
    background: $primary;
    border-color: $primary;

    .nav-btn__text { color: #fff; }
  }

  &__icon { font-size: 36rpx; }

  &__text {
    font-size: $font-size-base;
    color: $text-1;
    font-weight: 600;
  }
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

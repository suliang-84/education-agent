<script setup lang="ts">
import { useTheme } from '@/hooks/useTheme'
import { ref, computed, onMounted } from 'vue'
import { profileApi } from '@/api'
import { useAuthStore } from '@/store'
import { PAGES, FIVE_POWERS, FIVE_POWER_LABELS, FIVE_POWER_META } from '@/constants'
import { formatDate } from '@/utils'
import type { FivePowerProfile } from '@/api/profile'
import RadarChart from '@/components/charts/RadarChart.vue'
import SvgIcon from '@/components/SvgIcon.vue'


const { pageStyle, theme, hl, powerColors, isDark } = useTheme()

const themeOptions = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
] as const
const authStore = useAuthStore()

// ── 数据状态 ──────────────────────────────────────────────────────────────
const fivePower = ref<FivePowerProfile | null>(null)
const loading = ref(true)
const showGrowthTrend = ref(false)

// ── 是否可以重测（≥30天） ─────────────────────────────────────────────────
// 这里简化：实际应对比 profile 的 created_at
const canRetest = ref(true) // 实际应从接口获取创建时间比对

// ── 计算分数 ──────────────────────────────────────────────────────────────
const scores = computed(() => {
  if (!fivePower.value?.profile) return FIVE_POWERS.map(() => 0)
  const forces = fivePower.value.profile.forces
  return FIVE_POWERS.map((p) => Math.round(forces[p]?.final ?? 0))
})

// 五力详细评分列表：与测试结果页一致——按分数由高到低排序（分数相同保持五力原有顺序）
const powerRows = computed(() =>
  FIVE_POWERS.map((power, idx) => ({
    power,
    label: FIVE_POWER_LABELS[power],
    color: powerColors.value[power],
    score: scores.value[idx],
  })).sort((a, b) => b.score - a.score)
)

// 雷达图尺寸：与测试结果页一致，占满卡片内宽（页面左右各 16px + 卡片内边距各 16px），高度为宽的 90%，标签不带分数
const chartW = Math.min(uni.getSystemInfoSync().windowWidth - 64, 420)
const chartH = Math.round(chartW * 0.9)

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
  <page-meta :page-style="pageStyle" />
  <view class="profile-page">
    <!-- ── 顶部用户信息 + 重测按钮 ─────────────────────────── -->
    <view class="user-header" :style="hl('user-header')">
      <view class="user-info">
        <view class="avatar">
          <SvgIcon name="brain" :size="52" />
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
    <view v-if="loading" class="skeleton-card" :style="hl('skeleton')">
      <view class="skel-block skel-block--radar" />
      <view class="skel-lines">
        <view v-for="i in 5" :key="i" class="skel-line" />
      </view>
    </view>

    <!-- ── 无画像空态 ──────────────────────────────────────── -->
    <view v-else-if="!fivePower?.has_profile" class="no-profile-card" :style="hl('no-profile')">
      <view class="no-profile-icon"><SvgIcon name="atom" :size="64" /></view>
      <text class="no-profile-title">尚未完成五力测试</text>
      <text class="no-profile-desc">完成测试后，这里将展示你的五力认知画像</text>
      <button class="go-test-btn" @tap="goToTest">立即测试</button>
    </view>

    <template v-else>
      <!-- ── 五力雷达图 ──────────────────────────────────── -->
      <view class="radar-card" :style="hl('radar')">
        <view class="card-title">
          <view class="card-title__bar" />
          <text class="card-title__text">五力分布图</text>
        </view>
        <view class="radar-wrap">
          <RadarChart
            canvas-id="profileRadar"
            :scores="scores"
            :labels="FIVE_POWERS.map(p => FIVE_POWER_LABELS[p])"
            :colors="FIVE_POWERS.map(p => powerColors[p])"
            :size="chartW"
            :height="chartH"
            :show-value="false"
          />
        </view>
      </view>

      <!-- ── 五力维度详情 ─────────────────────────────────── -->
      <view class="dimension-card" :style="hl('dimension')">
        <view class="card-title">
          <view class="card-title__bar" />
          <text class="card-title__text">五力详细评分</text>
        </view>
        <!-- 样式同测试结果页：图标块 + 彩色名称 + 简介，分数在最右，行间分割线；按分数由高到低 -->
        <view class="power-list">
          <view v-for="row in powerRows" :key="row.power" class="power-row">
            <view class="power-row__icon" :style="{ background: row.color + '1A' }">
              <SvgIcon :name="FIVE_POWER_META[row.power].icon" :size="32" :color="row.color" />
            </view>
            <view class="power-row__info">
              <text class="power-row__name" :style="{ color: row.color }">{{ row.label }}</text>
              <text class="power-row__desc" :class="{ 'power-row__desc--dark': isDark }">{{ FIVE_POWER_META[row.power].desc }}</text>
            </view>
            <text class="power-row__score" :style="{ color: row.color }">{{ row.score }}</text>
          </view>
        </view>
      </view>

      <!-- ── 成长趋势（可折叠） ──────────────────────────── -->
      <view class="trend-card" :style="hl('trend')">
        <view class="trend-header" @tap="showGrowthTrend = !showGrowthTrend">
          <view class="card-title">
            <view class="card-title__bar" />
            <text class="card-title__text">成长趋势</text>
          </view>
          <text class="trend-toggle">{{ showGrowthTrend ? '收起 ▲' : '展开 ▼' }}</text>
        </view>
        <view v-if="showGrowthTrend" class="trend-content">
          <!-- 折线图占位 —— 实际可使用 echarts 或 canvas -->
          <view class="trend-placeholder">
            <view class="trend-placeholder__icon"><SvgIcon name="branch" :size="48" /></view>
            <text class="trend-placeholder__text">连续训练后，成长曲线将在此展示</text>
          </view>
        </view>
      </view>

      <!-- ── AI 分析文本 ──────────────────────────────────── -->
      <view v-if="fivePower?.profile?.ai_analysis_text" class="ai-analysis-card" :style="hl('ai-analysis')">
        <view class="ai-analysis-header">
          <view class="card-title">
            <view class="card-title__bar" />
            <text class="card-title__text">AI 画像分析</text>
          </view>
        </view>
        <text class="ai-analysis-text">{{ fivePower.profile.ai_analysis_text }}</text>
      </view>
    </template>

    <!-- ── 外观主题 ──────────────────────────────────────── -->
    <view class="theme-card" :style="hl('theme')">
      <view class="card-title">
        <view class="card-title__bar" />
        <text class="card-title__text">外观</text>
      </view>
      <view class="theme-seg">
        <view
          v-for="o in themeOptions"
          :key="o.value"
          class="theme-seg__item"
          :class="{ 'theme-seg__item--active': theme.mode === o.value }"
          @tap="theme.setMode(o.value)"
        >
          <text class="theme-seg__text">{{ o.label }}</text>
        </view>
      </view>
    </view>

    <!-- ── 底部导航按钮 ──────────────────────────────────── -->
    <view class="nav-btns">
      <view class="nav-btn" @tap="goToWrongAnswers">
        <view class="nav-btn__icon"><SvgIcon name="book" :size="36" /></view>
        <text class="nav-btn__text">错题集</text>
      </view>
      <view class="nav-btn nav-btn--primary" @tap="goToTraining">
        <view class="nav-btn__icon"><SvgIcon name="rocket" :size="36" color="on-primary" /></view>
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

// 用户头部卡
.user-header {
  @include glass-panel;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-4;
  padding: $space-4;
  border: 1rpx solid $border;
}

.user-info {
  display: flex;
  align-items: center;
  gap: $space-3;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: $primary-light;
  border: 4rpx solid $bg-surface;
  box-shadow: 0 0 0 4rpx $primary-border, $shadow-sm;
  display: flex;
  align-items: center;
  justify-content: center;
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
  height: 64rpx;
  padding: 0 $space-3;
  background: $primary-light;
  border: 1rpx solid $primary-border;
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
  @include glass-panel(false);
  border: 1rpx solid $border;
  padding: $space-4;
  margin-bottom: $space-4;
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
  border-radius: $r-pill;
  animation: shimmer 1.2s ease-in-out infinite;
}

// 无画像
.no-profile-card {
  @include glass-panel;
  border: 1rpx solid $border;
  padding: $space-6;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
  margin-bottom: $space-4;
}

.no-profile-icon {
  width: 128rpx;
  height: 128rpx;
  border-radius: $r-xl;
  background: $primary-light;
  display: flex;
  align-items: center;
  justify-content: center;
}

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
  line-height: 88rpx;
  padding: 0 $space-6;
  background: $cta-gradient;
  box-shadow: $shadow-cta;
  border-radius: $r-pill;
  border: none;
  font-size: $font-size-base;
  color: $on-primary;
  font-weight: 700;

  &::after { border: none; }
}

// 通用卡片
.radar-card,
.dimension-card,
.trend-card,
.ai-analysis-card {
  @include glass-panel;
  border: 1rpx solid $border;
  padding: $space-4;
  margin-bottom: $space-4;
}

.radar-wrap {
  display: flex;
  justify-content: center;
}

// 趋势卡
.trend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .card-title { margin-bottom: 0; }
}

.trend-toggle {
  font-size: $font-size-xs;
  color: $primary;
  padding: 6rpx $space-2;
  background: $primary-light;
  border-radius: $r-pill;
}

.trend-content {
  margin-top: $space-3;
}

.trend-placeholder {
  height: 200rpx;
  background: $bg-muted;
  border: 1rpx dashed $border-hover;
  border-radius: $r-lg;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $space-2;
}

.trend-placeholder__icon {
  display: flex;
  align-items: center;
}

.trend-placeholder__text {
  font-size: $font-size-xs;
  color: $text-3;
}

// AI 分析
.ai-analysis-header {
  display: flex;
  align-items: center;
  margin-bottom: $space-3;

  .card-title { margin-bottom: 0; }
}

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

.theme-card {
  @include glass-panel;
  border: 1rpx solid $border;
  padding: $space-4;
  margin-bottom: $space-4;
  display: flex;
  flex-direction: column;
  gap: $space-3;

  .card-title { margin-bottom: 0; }   // 间距由 gap 统一控制，避免与标题自带的下边距叠加
}

.theme-seg {
  display: flex;
  background: $bg-muted;
  border-radius: $r-pill;
  padding: 6rpx;

  &__item {
    flex: 1;
    height: 72rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $r-pill;
    transition: $transition-fast;

    &--active {
      background: $primary-light;
      box-shadow: inset 0 0 0 1rpx $primary-border;
    }
  }

  &__text {
    font-size: $font-size-sm;
    color: $text-2;
    font-weight: 500;

    .theme-seg__item--active & { color: $primary; font-weight: 700; }
  }
}

.nav-btn {
  flex: 1;
  height: 88rpx;
  background: $bg-surface;
  border: 1rpx solid $border;
  border-radius: $r-pill;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;
  box-shadow: $shadow-sm;

  &--primary {
    background: $cta-gradient;
    border-color: transparent;
    box-shadow: $shadow-cta;

    .nav-btn__text { color: $on-primary; }
  }

  &__icon {
    display: flex;
    align-items: center;
  }

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

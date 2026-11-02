<script setup lang="ts">
import { useTheme } from '@/hooks/useTheme'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { testApi } from '@/api'
import { useAuthStore } from '@/store'
import { PAGES, FIVE_POWER_LABELS, FIVE_POWERS, FIVE_POWER_META } from '@/constants'
import type { TestProfile } from '@/api/test'
import RadarChart from '@/components/charts/RadarChart.vue'
import SvgIcon from '@/components/SvgIcon.vue'


const { pageStyle, hl, powerColors, isDark } = useTheme()
const authStore = useAuthStore()

// ── 数据状态 ──────────────────────────────────────────────────────────────
const profileId = ref<number>(0)
const profile = ref<TestProfile | null>(null)
const aiText = ref<string | null>(null)
const aiStatus = ref<string>('pending')
const pollCount = ref(0)
const MAX_POLLS = 10
let pollTimer: ReturnType<typeof setTimeout> | null = null

// 五力分数数组（按 FIVE_POWERS 顺序排列，final 已是 0-100 整数）
const scores = computed(() =>
  profile.value
    ? FIVE_POWERS.map((p) => Math.round(profile.value!.forces[p]?.final ?? 0))
    : [0, 0, 0, 0, 0]
)

// 分数列表：按分数由高到低排序（分数相同保持五力原有顺序）；雷达图本身仍按固定的五力顺序排列
const powerRows = computed(() =>
  FIVE_POWERS.map((key, i) => ({ key, label: FIVE_POWER_LABELS[key], score: scores.value[i] }))
    .sort((a, b) => b.score - a.score)
)

// 雷达图尺寸：占满卡片内宽（页面左右各 16px + 卡片内边距各 16px），高度略小于宽度以减少上下空白
const chartW = Math.min(uni.getSystemInfoSync().windowWidth - 64, 420)
const chartH = Math.round(chartW * 0.9)

// ── 数据加载 ──────────────────────────────────────────────────────────────
onMounted(() => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const options = (current as any)?.options || {}
  profileId.value = parseInt(options.profile_id || '0')
  pollResult()

  const cachedProfile = uni.getStorageSync('mesh_test_profile')
  if (cachedProfile) {
    try {
      profile.value = JSON.parse(cachedProfile)
      authStore.setProfileFlag(true)
      uni.removeStorageSync('mesh_test_profile')
    } catch { /* ignore */ }
  }
})

async function pollResult() {
  if (!profileId.value) return
  try {
    const res = await testApi.getResult(profileId.value)
    aiStatus.value = res.ai_analysis_status
    aiText.value = res.ai_analysis_text
    if (res.ai_analysis_status !== 'completed' && pollCount.value < MAX_POLLS) {
      pollCount.value++
      pollTimer = setTimeout(pollResult, 3000)
    }
  } catch { /* ignore */ }
}

onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
})

function goToTraining() { uni.switchTab({ url: PAGES.TRAINING_HOME }) }
function goToAssistant() { uni.switchTab({ url: PAGES.ASSISTANT_HOME }) }
</script>

<template>
  <page-meta :page-style="pageStyle" />
  <view class="result-page">
    <!-- 顶部庆祝标题 -->
    <view class="result-header">
      <text class="result-title">测试完成！</text>
      <text class="result-sub">你的五力认知画像已生成</text>
    </view>

    <!-- ── Section 1: 雷达图 ─────────────────────────────── -->
    <view class="radar-card" :style="hl('radar')">
      <text class="card-title">五力雷达图</text>
      <view class="radar-wrap">
        <RadarChart
          canvas-id="radarChart"
          :scores="scores"
          :labels="FIVE_POWERS.map(p => FIVE_POWER_LABELS[p])"
          :colors="FIVE_POWERS.map(p => powerColors[p])"
          :size="chartW"
          :height="chartH"
          :show-value="false"
        />
      </view>

      <!-- 分数列表：样式同测试首页「测试将评估以下五力」，按分数由高到低排序 -->
      <view class="power-list">
        <view v-for="row in powerRows" :key="row.key" class="power-row">
          <view class="power-row__icon" :style="{ background: powerColors[row.key] + '1A' }">
            <SvgIcon :name="FIVE_POWER_META[row.key].icon" :size="32" :color="powerColors[row.key]" />
          </view>
          <view class="power-row__info">
            <text class="power-row__name" :style="{ color: powerColors[row.key] }">{{ row.label }}</text>
            <text class="power-row__desc" :class="{ 'power-row__desc--dark': isDark }">{{ FIVE_POWER_META[row.key].desc }}</text>
          </view>
          <text class="power-row__score" :style="{ color: powerColors[row.key] }">{{ profile ? row.score : '--' }}</text>
        </view>
      </view>
    </view>

    <!-- ── Section 2: AI 分析卡 ──────────────────────────── -->
    <view class="ai-card" :style="hl('ai')">
      <view class="ai-card__header">
        <view class="ai-card__icon"><SvgIcon name="brain" :size="32" /></view>
        <text class="card-title">AI 个性化分析</text>
      </view>

      <!-- 加载骨架 -->
      <view v-if="aiStatus !== 'completed'" class="ai-skeleton">
        <view class="ai-skeleton__dots">
          <view class="ai-dot" />
          <view class="ai-dot" />
          <view class="ai-dot" />
        </view>
        <text class="ai-skeleton__text">AI 正在分析你的认知特质...</text>
        <view class="skel-lines">
          <view v-for="i in 5" :key="i" class="skel-line" :style="{ width: `${90 - i * 6}%` }" />
        </view>
      </view>

      <!-- AI 文本 -->
      <text v-else class="ai-analysis-text">{{ aiText || '分析完成，暂无详细文字报告。' }}</text>
    </view>

    <!-- ── Section 3: CTA 按钮 ────────────────────────────── -->
    <view class="cta-area">
      <button class="cta-btn cta-btn--primary" @tap="goToTraining">
        <view class="cta-btn__icon"><SvgIcon name="rocket" :size="36" color="on-primary" /></view>
        <text class="cta-btn__text">开始个性化训练</text>
      </button>
      <button class="cta-btn cta-btn--secondary" @tap="goToAssistant">
        <view class="cta-btn__icon"><SvgIcon name="sparkles" :size="36" /></view>
        <text class="cta-btn__text">先和 AI 聊聊</text>
      </button>
    </view>
  </view>
</template>

<style lang="scss" scoped>

.result-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-4;
}

.result-header {
  text-align: center;
  margin-bottom: $space-4;
}

.result-title {
  display: block;
  font-size: $font-size-2xl;
  color: $text-1;
  font-weight: 800;
  margin-bottom: $space-2;
}

.result-sub {
  font-size: $font-size-base;
  color: $text-2;
}

// 通用卡片
.radar-card,
.ai-card {
  @include glass-panel;
  padding: $space-4;
  margin-bottom: $space-4;
  border: 1rpx solid $border;
}

.card-title {
  font-size: $font-size-lg;
  color: $text-1;
  font-weight: 700;
  display: block;
  margin-bottom: $space-3;
  padding-left: $space-2;
  border-left: 8rpx solid $primary;
  line-height: 1.2;
}

// 雷达图
.radar-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: $space-2;
}


// 分数列表：同测试首页五力预览（图标块 + 彩色名称 + 简介），行间用分割线；分数在最右
.power-list {
  display: flex;
  flex-direction: column;
}

.power-row {
  display: flex;
  align-items: center;
  gap: $space-3;
  padding: 28rpx 0;
  border-top: 1rpx solid $border;   // 第一行的上边线同时把列表与雷达图隔开
}

.power-row__icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: $r-md;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.power-row__info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: $space-2;
}

.power-row__name {
  font-size: $font-size-sm;
  font-weight: 700;
  flex-shrink: 0;
}

.power-row__desc {
  font-size: $font-size-xs;
  color: $text-3;

  // 暗色下用白色，亮色保持浅灰（同测试首页）
  &--dark { color: #ffffff; }
}

.power-row__score {
  font-size: $font-size-lg;
  font-weight: 800;
  min-width: 60rpx;
  text-align: right;
  flex-shrink: 0;
}

// AI 卡
.ai-card__header {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-3;
}

.ai-card__icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: $r-md;
  background: $primary-light;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-skeleton {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
}

.ai-skeleton__dots {
  display: flex;
  gap: 12rpx;
}

.ai-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: $primary;
  animation: bounce 0.9s ease-in-out infinite;

  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.ai-skeleton__text {
  font-size: $font-size-sm;
  color: $text-3;
}

.skel-lines {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.skel-line {
  height: 24rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  animation: shimmer 1.2s ease-in-out infinite;
}

.ai-analysis-text {
  font-size: $font-size-base;
  color: $text-2;
  line-height: 1.9;
}

// CTA 按钮区
.cta-area {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.cta-btn {
  height: 96rpx;
  border-radius: $r-pill;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;

  &::after { border: none; }

  &--primary {
    background: $cta-gradient;
    box-shadow: $shadow-cta;
  }

  &--secondary {
    background: $primary-light;
    border: 1rpx solid $primary-border;
  }

  &__icon { display: flex; align-items: center; }

  &__text {
    font-size: $font-size-lg;
    font-weight: 700;
    color: $on-primary;

    .cta-btn--secondary & { color: $primary; }
  }
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

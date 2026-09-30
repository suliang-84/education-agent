<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { testApi } from '@/api'
import { useAuthStore } from '@/store'
import { PAGES, FIVE_POWER_LABELS, FIVE_POWER_COLORS, FIVE_POWERS } from '@/constants'
import { getPowerLevel } from '@/utils'
import type { TestProfile } from '@/api/test'

const authStore = useAuthStore()

// ── 五力雷达图 SVG 配置 ────────────────────────────────────────────────────
// 五边形中心 (375, 375)，最大半径 260
const SVG_CX = 375
const SVG_CY = 375
const SVG_R_MAX = 260
const SVG_R_BG = 260 // 背景网格半径

// 根据 5 个分数（0-100）生成雷达多边形 points
function calcRadarPoints(scores: number[], radius = SVG_R_MAX): string {
  return scores
    .map((score, i) => {
      const angle = ((i * 72 - 90) * Math.PI) / 180
      const r = (score / 100) * radius
      return `${SVG_CX + r * Math.cos(angle)},${SVG_CY + r * Math.sin(angle)}`
    })
    .join(' ')
}

// 背景正五边形 points（三圈：100%, 60%, 30%）
const bgGridPoints = [1.0, 0.6, 0.3].map((ratio) =>
  calcRadarPoints([100, 100, 100, 100, 100], SVG_R_BG * ratio)
)

// 轴线终点（从中心到各顶点）
const axisPoints = FIVE_POWERS.map((_, i) => {
  const angle = ((i * 72 - 90) * Math.PI) / 180
  return {
    x2: SVG_CX + SVG_R_BG * Math.cos(angle),
    y2: SVG_CY + SVG_R_BG * Math.sin(angle),
  }
})

// 标签位置（略微外扩）
const labelPositions = FIVE_POWERS.map((_, i) => {
  const angle = ((i * 72 - 90) * Math.PI) / 180
  const r = SVG_R_BG + 50
  return {
    x: SVG_CX + r * Math.cos(angle),
    y: SVG_CY + r * Math.sin(angle),
  }
})

// ── 数据状态 ──────────────────────────────────────────────────────────────
const profileId = ref<number>(0)
const profile = ref<TestProfile | null>(null)
const aiText = ref<string | null>(null)
const aiStatus = ref<string>('pending')
const pollCount = ref(0)
const MAX_POLLS = 10
let pollTimer: ReturnType<typeof setTimeout> | null = null

// 五力分数数组（按 FIVE_POWERS 顺序排列）
const scores = computed(() => {
  if (!profile.value) return [0, 0, 0, 0, 0]
  const forces = profile.value.forces
  return FIVE_POWERS.map((p) => Math.round((forces[p]?.final ?? 0) * 100))
})

const radarPoints = computed(() => calcRadarPoints(scores.value))

onMounted(() => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const options = (current as any)?.options || {}
  profileId.value = parseInt(options.profile_id || '0')
  pollResult()
})

// ── 轮询结果（AI 分析最多 10 次，每 3 秒） ───────────────────────────────
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
  } catch {
    // 忽略轮询错误
  }
}

// 初次进入时从路由传过来的 profile 数据（completeTest 返回的）
// 同时保存 authStore 的 profileFlag
onMounted(() => {
  // 尝试从本地存储获取 profile（completeTest 返回值应由 questions.vue redirect 时传入）
  const cachedProfile = uni.getStorageSync('mesh_test_profile')
  if (cachedProfile) {
    try {
      profile.value = JSON.parse(cachedProfile)
      authStore.setProfileFlag(true)
    } catch { /* ignore */ }
  }
})

onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
})

function goToTraining() {
  uni.switchTab({ url: PAGES.TRAINING_HOME })
}

function goToAssistant() {
  uni.switchTab({ url: PAGES.ASSISTANT_HOME })
}
</script>

<template>
  <view class="result-page">
    <!-- 顶部庆祝标题 -->
    <view class="result-header">
      <text class="result-title">测试完成！🎉</text>
      <text class="result-sub">你的五力认知画像已生成</text>
    </view>

    <!-- ── Section 1: 雷达图 ─────────────────────────────── -->
    <view class="radar-card">
      <text class="card-title">五力雷达图</text>
      <view class="radar-wrap">
        <svg
          class="radar-svg"
          :viewBox="`0 0 750 750`"
          xmlns="http://www.w3.org/2000/svg"
        >
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
            :x1="SVG_CX"
            :y1="SVG_CY"
            :x2="ax.x2"
            :y2="ax.y2"
            stroke="#E2E8F0"
            stroke-width="2"
          />
          <!-- 数据多边形 -->
          <polygon
            v-if="profile"
            :points="radarPoints"
            fill="rgba(79, 70, 229, 0.15)"
            stroke="#4F46E5"
            stroke-width="4"
            stroke-linejoin="round"
          />
          <!-- 骨架（无数据时） -->
          <polygon
            v-else
            :points="calcRadarPoints([50, 50, 50, 50, 50])"
            fill="rgba(203, 213, 225, 0.3)"
            stroke="#CBD5E1"
            stroke-width="2"
          />
          <!-- 标签 -->
          <text
            v-for="(lp, li) in labelPositions"
            :key="li"
            :x="lp.x"
            :y="lp.y"
            font-size="28"
            text-anchor="middle"
            dominant-baseline="middle"
            :fill="FIVE_POWER_COLORS[FIVE_POWERS[li]]"
            font-weight="600"
          >{{ FIVE_POWER_LABELS[FIVE_POWERS[li]] }}</text>
          <!-- 数据点 -->
          <template v-if="profile">
            <circle
              v-for="(score, si) in scores"
              :key="si"
              :cx="SVG_CX + (score / 100) * SVG_R_MAX * Math.cos(((si * 72 - 90) * Math.PI) / 180)"
              :cy="SVG_CY + (score / 100) * SVG_R_MAX * Math.sin(((si * 72 - 90) * Math.PI) / 180)"
              r="10"
              :fill="FIVE_POWER_COLORS[FIVE_POWERS[si]]"
            />
          </template>
        </svg>
      </view>

      <!-- 分数列表 -->
      <view class="score-list">
        <view
          v-for="(power, idx) in FIVE_POWERS"
          :key="power"
          class="score-row"
          :style="{ '--pc': FIVE_POWER_COLORS[power] }"
        >
          <view class="score-row__left">
            <view class="color-dot" :style="{ background: FIVE_POWER_COLORS[power] }" />
            <text class="score-row__name">{{ FIVE_POWER_LABELS[power] }}</text>
          </view>
          <view class="score-row__right">
            <text class="score-value">{{ profile ? scores[idx] : '--' }}</text>
            <view
              v-if="profile"
              class="level-tag"
              :style="{
                background: getPowerLevel(scores[idx]).color + '20',
                color: getPowerLevel(scores[idx]).color,
              }"
            >
              <text class="level-tag__text">{{ getPowerLevel(scores[idx]).label }}</text>
            </view>
            <view v-else class="skel-block" />
          </view>
        </view>
      </view>
    </view>

    <!-- ── Section 2: AI 分析卡 ──────────────────────────── -->
    <view class="ai-card">
      <view class="ai-card__header">
        <text class="ai-card__icon">🤖</text>
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
        <text class="cta-btn__icon">🚀</text>
        <text class="cta-btn__text">开始个性化训练</text>
      </button>
      <button class="cta-btn cta-btn--secondary" @tap="goToAssistant">
        <text class="cta-btn__icon">💬</text>
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
  margin-bottom: $space-4;
}

.radar-svg {
  width: 560rpx;
  height: 560rpx;
}

// 分数列表
.score-list {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $space-2 $space-3;
  border-radius: $r-md;
  background: $bg-muted;

  &__left {
    display: flex;
    align-items: center;
    gap: $space-2;
  }

  &__right {
    display: flex;
    align-items: center;
    gap: $space-2;
  }
}

.color-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.score-row__name {
  font-size: $font-size-sm;
  color: $text-2;
  font-weight: 500;
}

.score-value {
  font-size: $font-size-lg;
  font-weight: 800;
  color: var(--pc, $text-1);
  min-width: 60rpx;
  text-align: right;
}

.level-tag {
  padding: 4rpx 16rpx;
  border-radius: $r-pill;

  &__text {
    font-size: $font-size-xs;
    font-weight: 600;
  }
}

.skel-block {
  width: 80rpx;
  height: 32rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  animation: shimmer 1.2s ease-in-out infinite;
}

// AI 卡
.ai-card__header {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-3;
}

.ai-card__icon {
  font-size: 36rpx;
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
    background: $pink;
  }

  &--secondary {
    background: $primary-light;
    border: 2rpx solid $primary;
  }

  &__icon { font-size: 36rpx; }

  &__text {
    font-size: $font-size-lg;
    font-weight: 700;
    color: #fff;

    .cta-btn--secondary & { color: $primary; }
  }
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

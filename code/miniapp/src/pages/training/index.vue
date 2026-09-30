<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { profileApi, trainingApi } from '@/api'
import { useTrainingStore, useAuthStore } from '@/store'
import {
  PAGES, FIVE_POWER_LABELS, FIVE_POWER_COLORS,
  SUBJECT_LABELS, SUBJECT_ICONS, TRAINING_DIMENSION_LABELS,
} from '@/constants'
import type { FivePowerProfile } from '@/api/profile'
import type { TrainingDimension } from '@/constants'

const trainingStore = useTrainingStore()
const authStore = useAuthStore()

// ── 五力画像状态 ───────────────────────────────────────────────────────────
const fivePower = ref<FivePowerProfile | null>(null)
const loadingProfile = ref(true)

// ── 选科 & 维度 ────────────────────────────────────────────────────────────
const selectedSubject = ref<string | null>(null)
const dimensionsVisible = ref(false)
const creatingSession = ref(false)
const wrongCount = ref(0)

// ── 训练维度配置 ───────────────────────────────────────────────────────────
const dimensions: Array<{
  key: TrainingDimension
  icon: string
  desc: string
}> = [
  { key: 'KNOWLEDGE_POINT', icon: '🎯', desc: '精准练习单个知识点，快速补强' },
  { key: 'UNIT',            icon: '📚', desc: '以单元为单位，系统强化训练' },
  { key: 'SEMESTER',        icon: '🗓️', desc: '学期范围综合练习，查漏补缺' },
  { key: 'ERROR_QUESTIONS', icon: '🔁', desc: '专项复盘错题，彻底突破弱点' },
  { key: 'RANDOM',          icon: '🎲', desc: '随机出题，保持训练广度' },
]

const subjects = Object.keys(SUBJECT_LABELS).map((k) => ({
  code: k,
  label: SUBJECT_LABELS[k],
  icon: SUBJECT_ICONS[k],
}))

// ── 最弱两力（用于状态卡片） ──────────────────────────────────────────────
const weakestPowers = computed(() => {
  const profile = fivePower.value?.profile
  if (!profile) return []
  const forces = profile.forces
  return Object.entries(forces)
    .map(([key, val]) => ({ key, score: Math.round(val.final * 100) }))
    .sort((a, b) => a.score - b.score)
    .slice(0, 2)
})

onMounted(async () => {
  try {
    fivePower.value = await profileApi.getFivePower()
  } catch {
    fivePower.value = { has_profile: false, profile: null, training_profile: null }
  } finally {
    loadingProfile.value = false
  }
})

// 选择科目
async function selectSubject(code: string) {
  selectedSubject.value = code
  dimensionsVisible.value = true
  // 获取该科目错题数
  try {
    const res = await trainingApi.getWrongSummary(code)
    const sub = res.subjects?.find((s) => s.subject_code === code)
    wrongCount.value = sub?.pending_count ?? 0
  } catch {
    wrongCount.value = 0
  }
}

// 点击训练维度 → 创建会话并进入训练
async function startTraining(dim: TrainingDimension) {
  if (creatingSession.value) return
  if (!selectedSubject.value) return
  creatingSession.value = true
  try {
    const resp = await trainingApi.createSession({
      training_dimension: dim,
      subject_code: selectedSubject.value,
    })
    trainingStore.initSession(resp)
    uni.navigateTo({ url: PAGES.TRAINING_SESSION })
  } catch {
    uni.showToast({ title: '创建训练失败，请重试', icon: 'none' })
  } finally {
    creatingSession.value = false
  }
}

function goToTest() {
  uni.navigateTo({ url: PAGES.TEST_HOME })
}
</script>

<template>
  <view class="training-page">
    <!-- ── 五力状态卡 ───────────────────────────────────────── -->
    <view class="power-card">
      <!-- Loading skeleton -->
      <view v-if="loadingProfile" class="power-card__skeleton">
        <view class="skel-line skel-line--title" />
        <view class="skel-row">
          <view class="skel-block" />
          <view class="skel-block" />
        </view>
      </view>

      <!-- 无画像 -->
      <view v-else-if="!fivePower?.has_profile" class="power-card__empty">
        <text class="power-card__empty-icon">🧬</text>
        <view class="power-card__empty-info">
          <text class="power-card__empty-title">尚未完成五力测试</text>
          <text class="power-card__empty-desc">先完成测试，解锁专属训练方案</text>
        </view>
        <button class="go-test-btn" @tap="goToTest">去测试</button>
      </view>

      <!-- 有画像 -->
      <view v-else class="power-card__content">
        <view class="power-card__header">
          <text class="power-card__title">重点强化</text>
          <text class="power-card__sub">当前最弱两力</text>
        </view>
        <view class="power-card__powers">
          <view
            v-for="p in weakestPowers"
            :key="p.key"
            class="power-item"
            :style="{ '--pc': FIVE_POWER_COLORS[p.key as keyof typeof FIVE_POWER_COLORS] }"
          >
            <view class="power-item__bar-wrap">
              <view
                class="power-item__bar"
                :style="{ width: `${p.score}%`, background: FIVE_POWER_COLORS[p.key as keyof typeof FIVE_POWER_COLORS] }"
              />
            </view>
            <view class="power-item__meta">
              <text class="power-item__name">{{ FIVE_POWER_LABELS[p.key as keyof typeof FIVE_POWER_LABELS] }}</text>
              <text class="power-item__score">{{ p.score }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- ── Step 1: 选择科目 ──────────────────────────────────── -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">选择科目</text>
        <text class="section-step">Step 1</text>
      </view>
      <view class="subject-grid">
        <view
          v-for="s in subjects"
          :key="s.code"
          class="subject-card"
          :class="{ 'subject-card--active': selectedSubject === s.code }"
          @tap="selectSubject(s.code)"
        >
          <text class="subject-card__icon">{{ s.icon }}</text>
          <text class="subject-card__label">{{ s.label }}</text>
        </view>
      </view>
    </view>

    <!-- ── Step 2: 选择训练维度（选科后滑入） ────────────────── -->
    <view
      class="section dimension-section"
      :class="{ 'dimension-section--visible': dimensionsVisible }"
    >
      <view class="section-header">
        <text class="section-title">选择训练方式</text>
        <text class="section-step">Step 2</text>
      </view>
      <view class="dimension-list">
        <view
          v-for="dim in dimensions"
          :key="dim.key"
          class="dim-card"
          @tap="startTraining(dim.key)"
        >
          <text class="dim-card__icon">{{ dim.icon }}</text>
          <view class="dim-card__info">
            <view class="dim-card__name-row">
              <text class="dim-card__name">{{ TRAINING_DIMENSION_LABELS[dim.key] }}</text>
              <!-- 错题数徽标 -->
              <view v-if="dim.key === 'ERROR_QUESTIONS' && wrongCount > 0" class="badge">
                <text class="badge__text">{{ wrongCount }}题待复盘</text>
              </view>
            </view>
            <text class="dim-card__desc">{{ dim.desc }}</text>
          </view>
          <text class="dim-card__arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 全屏创建中遮罩 -->
    <view v-if="creatingSession" class="creating-mask">
      <view class="creating-inner">
        <view class="spinner" />
        <text class="creating-text">正在准备训练题目...</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>

.training-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-4;
  padding-bottom: 160rpx; // tabbar 空间
}

// ── 五力状态卡 ──────────────────────────────────────────────────────────────
.power-card {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  margin-bottom: $space-4;
  box-shadow: $shadow-sm;
  min-height: 160rpx;
}

.power-card__skeleton {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.skel-line {
  background: $bg-muted;
  border-radius: $r-pill;
  animation: shimmer 1.2s ease-in-out infinite;

  &--title {
    height: 32rpx;
    width: 40%;
  }
}

.skel-row {
  display: flex;
  gap: $space-3;
}

.skel-block {
  flex: 1;
  height: 80rpx;
  background: $bg-muted;
  border-radius: $r-md;
  animation: shimmer 1.2s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.power-card__empty {
  display: flex;
  align-items: center;
  gap: $space-3;
}

.power-card__empty-icon {
  font-size: 56rpx;
  flex-shrink: 0;
}

.power-card__empty-info {
  flex: 1;
}

.power-card__empty-title {
  display: block;
  font-size: $font-size-base;
  color: $text-1;
  font-weight: 600;
  margin-bottom: 4rpx;
}

.power-card__empty-desc {
  font-size: $font-size-xs;
  color: $text-3;
}

.go-test-btn {
  flex-shrink: 0;
  height: 64rpx;
  padding: 0 $space-3;
  background: $pink;
  border-radius: $r-pill;
  border: none;
  font-size: $font-size-sm;
  color: #fff;
  font-weight: 600;

  &::after { border: none; }
}

.power-card__header {
  display: flex;
  align-items: baseline;
  gap: $space-2;
  margin-bottom: $space-3;
}

.power-card__title {
  font-size: $font-size-lg;
  color: $text-1;
  font-weight: 700;
}

.power-card__sub {
  font-size: $font-size-xs;
  color: $text-3;
}

.power-card__powers {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.power-item {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.power-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.power-item__name {
  font-size: $font-size-sm;
  color: $text-2;
}

.power-item__score {
  font-size: $font-size-sm;
  color: var(--pc);
  font-weight: 700;
}

.power-item__bar-wrap {
  height: 12rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  overflow: hidden;
}

.power-item__bar {
  height: 100%;
  border-radius: $r-pill;
  transition: width 0.6s ease;
}

// ── 通用 Section ────────────────────────────────────────────────────────────
.section {
  margin-bottom: $space-4;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-3;
}

.section-title {
  font-size: $font-size-lg;
  color: $text-1;
  font-weight: 700;
}

.section-step {
  font-size: $font-size-xs;
  color: $primary;
  background: $primary-light;
  padding: 4rpx 16rpx;
  border-radius: $r-pill;
  font-weight: 600;
}

// ── 科目卡片 ────────────────────────────────────────────────────────────────
.subject-grid {
  display: flex;
  gap: $space-3;
}

.subject-card {
  flex: 1;
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-4 $space-2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-2;
  box-shadow: $shadow-sm;
  border: 2rpx solid transparent;
  transition: $transition-base;

  &--active {
    border-color: $primary;
    background: $primary-light;
    box-shadow: $shadow-md;
  }

  &__icon {
    font-size: 64rpx;
  }

  &__label {
    font-size: $font-size-sm;
    color: $text-2;
    font-weight: 500;

    .subject-card--active & {
      color: $primary;
      font-weight: 700;
    }
  }
}

// ── 训练维度列表 ────────────────────────────────────────────────────────────
.dimension-section {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transform: translateY(20rpx);
  transition: max-height 0.4s ease, opacity 0.3s ease, transform 0.3s ease;

  &--visible {
    max-height: 1000rpx;
    opacity: 1;
    transform: translateY(0);
  }
}

.dimension-list {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.dim-card {
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  display: flex;
  align-items: center;
  gap: $space-3;
  box-shadow: $shadow-sm;
  transition: $transition-fast;

  &:active {
    opacity: 0.8;
    transform: scale(0.99);
  }

  &__icon {
    font-size: 44rpx;
    flex-shrink: 0;
  }

  &__info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6rpx;
  }

  &__name-row {
    display: flex;
    align-items: center;
    gap: $space-2;
  }

  &__name {
    font-size: $font-size-base;
    color: $text-1;
    font-weight: 600;
  }

  &__desc {
    font-size: $font-size-xs;
    color: $text-3;
  }

  &__arrow {
    font-size: 36rpx;
    color: $text-3;
    flex-shrink: 0;
  }
}

// 错题徽标
.badge {
  background: $danger-light;
  border-radius: $r-pill;
  padding: 4rpx 12rpx;

  &__text {
    font-size: $font-size-xs;
    color: $danger;
    font-weight: 600;
  }
}

// ── 创建遮罩 ────────────────────────────────────────────────────────────────
.creating-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.creating-inner {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-5;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
}

.creating-text {
  font-size: $font-size-base;
  color: $text-2;
}

.spinner {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  border: 6rpx solid $bg-muted;
  border-top-color: $primary;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

<script setup lang="ts">
import { ref } from 'vue'
import { trainingApi } from '@/api'
import { useTrainingStore } from '@/store'
import {
  PAGES, SUBJECT_LABELS, SUBJECT_ICONS, TRAINING_DIMENSION_LABELS,
} from '@/constants'
import type { InterruptRecord } from '@/api/training'
import type { TrainingDimension } from '@/constants'

const trainingStore = useTrainingStore()

// ── 选科 & 维度 ────────────────────────────────────────────────────────────
const selectedSubject = ref<string | null>(null)
const dimensionsVisible = ref(false)
const creatingSession = ref(false)
const wrongCount = ref(0)

// ── 中断恢复弹窗 ────────────────────────────────────────────────────────────
const interruptRecord = ref<InterruptRecord | null>(null)
const showResumeDialog = ref(false)
const pendingDimension = ref<TrainingDimension | null>(null)
const checkingInterrupt = ref(false)

// ── 训练维度配置 ───────────────────────────────────────────────────────────
const dimensions: Array<{
  key: TrainingDimension
  icon: string
  desc: string
}> = [
  { key: 'KNOWLEDGE_POINT', icon: '🎯', desc: '精准练习单个知识点，AI 从你擅长的角度引导入门' },
  { key: 'UNIT',            icon: '📚', desc: '以单元为单位，系统贯通知识脉络' },
  { key: 'SEMESTER',        icon: '🗓️', desc: '学期范围综合练习，查漏补缺' },
  { key: 'ERROR_QUESTIONS', icon: '🔁', desc: '复盘错题，AI 借你的优势帮你攻克薄弱环节' },
  { key: 'RANDOM',          icon: '🎲', desc: '随机出题，保持训练广度' },
]

const subjects = Object.keys(SUBJECT_LABELS).map((k) => ({
  code: k,
  label: SUBJECT_LABELS[k],
  icon: SUBJECT_ICONS[k],
}))

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

// 点击训练维度 → 先检查中断，再创建会话
async function startTraining(dim: TrainingDimension) {
  if (creatingSession.value || checkingInterrupt.value) return
  if (!selectedSubject.value) return

  checkingInterrupt.value = true
  try {
    const res = await trainingApi.getInterrupt(selectedSubject.value, dim)
    if (res.has_interrupt && res.interrupt) {
      interruptRecord.value = res.interrupt
      pendingDimension.value = dim
      showResumeDialog.value = true
      return
    }
  } catch {
    // 查询失败不阻断正常流程
  } finally {
    checkingInterrupt.value = false
  }

  await doCreateSession(dim)
}

async function doCreateSession(dim: TrainingDimension) {
  if (creatingSession.value) return
  creatingSession.value = true
  try {
    const resp = await trainingApi.createSession({
      training_dimension: dim,
      subject_code: selectedSubject.value!,
    })
    trainingStore.initSession(resp, selectedSubject.value!)
    uni.navigateTo({ url: PAGES.TRAINING_SESSION })
  } catch {
    uni.showToast({ title: '创建训练失败，请重试', icon: 'none' })
  } finally {
    creatingSession.value = false
  }
}

async function handleResume() {
  showResumeDialog.value = false
  if (!interruptRecord.value) return
  trainingStore.restoreFromInterrupt(interruptRecord.value)
  uni.navigateTo({ url: PAGES.TRAINING_SESSION })
}

async function handleStartNew() {
  showResumeDialog.value = false
  if (!interruptRecord.value || !pendingDimension.value) return
  // 删除旧中断记录
  try {
    await trainingApi.deleteInterrupt(
      interruptRecord.value.subject_code,
      interruptRecord.value.training_dimension
    )
  } catch { /* 忽略 */ }
  interruptRecord.value = null
  await doCreateSession(pendingDimension.value)
}

</script>

<template>
  <view class="training-page">
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

    <!-- 中断恢复弹窗 -->
    <view v-if="showResumeDialog" class="resume-mask">
      <view class="resume-dialog">
        <text class="resume-dialog__title">检测到未完成的训练</text>
        <text class="resume-dialog__desc">
          {{ interruptRecord?.scope_label || '上次训练' }} · 已完成
          {{ interruptRecord?.answers_snapshot.length }}/{{ interruptRecord?.total_questions }} 题
        </text>
        <text class="resume-dialog__time">
          中断于 {{ interruptRecord?.interrupted_at ? new Date(interruptRecord.interrupted_at).toLocaleDateString('zh-CN') : '' }}
        </text>
        <view class="resume-dialog__btns">
          <button class="resume-btn resume-btn--new" @tap="handleStartNew">放弃，重新开始</button>
          <button class="resume-btn resume-btn--resume" @tap="handleResume">继续上次训练</button>
        </view>
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

// ── 中断恢复弹窗 ──────────────────────────────────────────────────────────────
.resume-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: $space-6;
}

.resume-dialog {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-5;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: $space-3;

  &__title {
    font-size: $font-size-lg;
    color: $text-1;
    font-weight: 700;
    text-align: center;
  }

  &__desc {
    font-size: $font-size-base;
    color: $text-2;
    text-align: center;
  }

  &__time {
    font-size: $font-size-xs;
    color: $text-3;
    text-align: center;
  }

  &__btns {
    display: flex;
    flex-direction: column;
    gap: $space-2;
    margin-top: $space-2;
  }
}

.resume-btn {
  height: 88rpx;
  border-radius: $r-lg;
  font-size: $font-size-base;
  font-weight: 600;
  border: none;

  &::after { border: none; }

  &--new {
    background: $bg-muted;
    color: $text-2;
  }

  &--resume {
    background: $primary;
    color: #fff;
  }
}
</style>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { wrongAnswerApi, assistantApi } from '@/api'
import { PAGES, FIVE_POWER_COLORS, FIVE_POWER_LABELS, WRONG_STATUS_LABELS, DIFFICULTY_LABELS } from '@/constants'
import { fromNow } from '@/utils'
import type { WrongAnswer } from '@/api/profile'

// ── 标签定义 ──────────────────────────────────────────────────────────────
const tabs = [
  { key: '', label: '全部' },
  { key: 'unreview', label: '未复盘' },
  { key: 'reviewing', label: '复盘中' },
  { key: 'aha_achieved', label: '已突破' },
]

const activeTab = ref('')
const list = ref<WrongAnswer[]>([])
const loading = ref(true)
const startingReview = ref<string | null>(null) // 正在发起复盘的 wrong_id

// ── 加载错题列表 ──────────────────────────────────────────────────────────
async function loadList() {
  loading.value = true
  try {
    const resp = await wrongAnswerApi.getList(activeTab.value || undefined)
    list.value = resp.list
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadList()
})

function switchTab(key: string) {
  if (activeTab.value === key) return
  activeTab.value = key
  loadList()
}

// ── 发起 AI 复盘 ──────────────────────────────────────────────────────────
async function startReview(item: WrongAnswer) {
  if (startingReview.value) return
  startingReview.value = item.wrong_id
  try {
    const resp = await wrongAnswerApi.startReview(item.wrong_id)
    // 进入对话页，附带 session_id
    uni.navigateTo({
      url: `${PAGES.ASSISTANT_CHAT}?session_id=${resp.chat_session_id}&mode=wrong_review`,
    })
  } catch {
    uni.showToast({ title: '发起复盘失败，请重试', icon: 'none' })
  } finally {
    startingReview.value = null
  }
}

// ── 状态颜色映射 ──────────────────────────────────────────────────────────
const statusColors: Record<string, string> = {
  unreview: '#64748B',
  reviewing: '#D97706',
  pending_consolidation: '#3B82F6',
  aha_achieved: '#10B981',
}

// ── 统计数量 ──────────────────────────────────────────────────────────────
const tabCounts = computed(() => {
  const all = list.value
  return {
    '': all.length,
    unreview: all.filter((i) => i.review_status === 'unreview').length,
    reviewing: all.filter((i) => i.review_status === 'reviewing').length,
    aha_achieved: all.filter((i) => i.review_status === 'aha_achieved').length,
  }
})

// ── 当前 tab 对应的空态文案 ────────────────────────────────────────────────
const emptyMessages: Record<string, { icon: string; title: string; desc: string }> = {
  '': { icon: '🎉', title: '暂无错题', desc: '坚持训练，保持零错题的好成绩！' },
  unreview: { icon: '✅', title: '没有待复盘的错题', desc: '所有错题都已开始复盘，继续加油！' },
  reviewing: { icon: '💪', title: '暂无复盘中的错题', desc: '开始 AI 复盘，突破你的薄弱点' },
  aha_achieved: { icon: '🏆', title: '还没有突破记录', desc: '坚持复盘，等待 aha moment！' },
}

const emptyState = computed(() => emptyMessages[activeTab.value] || emptyMessages[''])

// ── 题干截断 ──────────────────────────────────────────────────────────────
function truncate(text: string, len = 60): string {
  return text.length > len ? text.slice(0, len) + '...' : text
}
</script>

<template>
  <view class="wrong-answers-page">
    <!-- ── 页面顶部 ──────────────────────────────────────── -->
    <view class="page-header">
      <text class="page-title">错题集</text>
      <text class="total-count">共 {{ list.length }} 题</text>
    </view>

    <!-- ── Tab 栏 ─────────────────────────────────────────── -->
    <scroll-view class="tab-scroll" scroll-x>
      <view class="tab-bar">
        <view
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ 'tab-item--active': activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text class="tab-label">{{ tab.label }}</text>
          <view v-if="tabCounts[tab.key] > 0" class="tab-badge">
            <text class="tab-badge__text">{{ tabCounts[tab.key] }}</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- ── 骨架屏 ────────────────────────────────────────── -->
    <view v-if="loading" class="skeleton-list">
      <view v-for="i in 4" :key="i" class="skel-card">
        <view class="skel-power-tag" />
        <view class="skel-content">
          <view class="skel-line skel-line--title" />
          <view class="skel-line skel-line--desc" />
        </view>
        <view class="skel-btn" />
      </view>
    </view>

    <!-- ── 空状态 ────────────────────────────────────────── -->
    <view v-else-if="list.length === 0" class="empty-state">
      <text class="empty-icon">{{ emptyState.icon }}</text>
      <text class="empty-title">{{ emptyState.title }}</text>
      <text class="empty-desc">{{ emptyState.desc }}</text>
    </view>

    <!-- ── 错题列表 ───────────────────────────────────────── -->
    <view v-else class="wrong-list">
      <view
        v-for="item in list"
        :key="item.wrong_id"
        class="wrong-card"
      >
        <!-- 顶部：五力色标签 + 状态 + 难度 -->
        <view class="wrong-card__header">
          <view
            class="power-tag"
            :style="{
              background: (FIVE_POWER_COLORS[item.question.primary_power as keyof typeof FIVE_POWER_COLORS] || '#64748B') + '18',
              color: FIVE_POWER_COLORS[item.question.primary_power as keyof typeof FIVE_POWER_COLORS] || '#64748B',
            }"
          >
            <text class="power-tag__text">
              {{ FIVE_POWER_LABELS[item.question.primary_power as keyof typeof FIVE_POWER_LABELS] || '未分类' }}
            </text>
          </view>

          <view class="wrong-card__badges">
            <!-- 难度 -->
            <view class="difficulty-badge">
              <text class="difficulty-badge__text">{{ DIFFICULTY_LABELS[item.question.difficulty] || item.question.difficulty }}</text>
            </view>

            <!-- 复盘状态 -->
            <view
              class="status-badge"
              :style="{
                background: (statusColors[item.review_status] || '#64748B') + '18',
                color: statusColors[item.review_status] || '#64748B',
              }"
            >
              <text class="status-badge__text">{{ WRONG_STATUS_LABELS[item.review_status] || item.review_status }}</text>
            </view>
          </view>
        </view>

        <!-- 题干预览 -->
        <text class="wrong-card__stem">{{ truncate(item.question.stem) }}</text>

        <!-- 我的答案（如果有） -->
        <view v-if="item.student_answer" class="my-answer">
          <text class="my-answer__label">我的答案：</text>
          <text class="my-answer__text">{{ truncate(item.student_answer, 40) }}</text>
        </view>

        <!-- 底部：时间 + 操作 -->
        <view class="wrong-card__footer">
          <text class="wrong-time">{{ fromNow(item.created_at) }}</text>
          <view class="wrong-actions">
            <!-- 已突破状态：仅显示标记 -->
            <view v-if="item.review_status === 'aha_achieved'" class="aha-badge">
              <text class="aha-badge__text">🏆 已突破</text>
            </view>
            <!-- 其他状态：显示复盘按钮 -->
            <button
              v-else
              class="review-btn"
              :class="{ 'review-btn--loading': startingReview === item.wrong_id }"
              :disabled="!!startingReview"
              @tap="startReview(item)"
            >
              <view v-if="startingReview === item.wrong_id" class="spinner" />
              <text class="review-btn__text">
                {{ startingReview === item.wrong_id
                  ? '准备中...'
                  : item.review_status === 'reviewing' ? '继续复盘' : 'AI 复盘'
                }}
              </text>
            </button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>

.wrong-answers-page {
  min-height: 100vh;
  background: $bg-page;
  padding-bottom: 80rpx;
}

// 页面顶部
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $space-4 $space-4 0;
  margin-bottom: $space-3;
}

.page-title {
  font-size: $font-size-2xl;
  color: $text-1;
  font-weight: 800;
}

.total-count {
  font-size: $font-size-sm;
  color: $text-3;
}

// Tab 栏
.tab-scroll {
  padding: 0 $space-4;
  margin-bottom: $space-3;
}

.tab-bar {
  display: flex;
  gap: $space-2;
  min-width: max-content;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: $space-1;
  height: 68rpx;
  padding: 0 $space-3;
  border-radius: $r-pill;
  background: $bg-surface;
  border: 2rpx solid transparent;
  transition: $transition-fast;
  flex-shrink: 0;

  &--active {
    background: $primary-light;
    border-color: $primary;
  }
}

.tab-label {
  font-size: $font-size-sm;
  color: $text-2;
  font-weight: 500;

  .tab-item--active & {
    color: $primary;
    font-weight: 700;
  }
}

.tab-badge {
  min-width: 36rpx;
  height: 36rpx;
  background: $danger;
  border-radius: $r-pill;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 10rpx;

  &__text {
    font-size: $font-size-xs;
    color: #fff;
    font-weight: 700;
  }
}

// 骨架屏
.skeleton-list {
  padding: 0 $space-4;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.skel-card {
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  display: flex;
  align-items: center;
  gap: $space-3;
  box-shadow: $shadow-sm;
}

.skel-power-tag {
  width: 100rpx;
  height: 40rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  flex-shrink: 0;
  animation: shimmer 1.2s ease-in-out infinite;
}

.skel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.skel-line {
  height: 24rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  animation: shimmer 1.2s ease-in-out infinite;

  &--title { width: 80%; }
  &--desc { width: 55%; }
}

.skel-btn {
  width: 120rpx;
  height: 56rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  flex-shrink: 0;
  animation: shimmer 1.2s ease-in-out infinite;
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
  padding: 120rpx $space-4;
}

.empty-icon { font-size: 100rpx; }
.empty-title {
  font-size: $font-size-lg;
  color: $text-2;
  font-weight: 600;
}
.empty-desc {
  font-size: $font-size-sm;
  color: $text-3;
  text-align: center;
  line-height: 1.7;
}

// 错题列表
.wrong-list {
  padding: 0 $space-4;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.wrong-card {
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.wrong-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.power-tag {
  padding: 6rpx 20rpx;
  border-radius: $r-pill;

  &__text {
    font-size: $font-size-xs;
    font-weight: 700;
  }
}

.wrong-card__badges {
  display: flex;
  align-items: center;
  gap: $space-2;
}

.difficulty-badge {
  padding: 4rpx 14rpx;
  background: $bg-muted;
  border-radius: $r-pill;

  &__text {
    font-size: $font-size-xs;
    color: $text-3;
  }
}

.status-badge {
  padding: 4rpx 16rpx;
  border-radius: $r-pill;

  &__text {
    font-size: $font-size-xs;
    font-weight: 600;
  }
}

.wrong-card__stem {
  font-size: $font-size-base;
  color: $text-1;
  line-height: 1.6;
  display: block;
}

.my-answer {
  display: flex;
  gap: $space-1;
  padding: $space-2 $space-3;
  background: $danger-light;
  border-radius: $r-md;
  flex-wrap: wrap;
}

.my-answer__label {
  font-size: $font-size-xs;
  color: $danger;
  font-weight: 600;
  flex-shrink: 0;
}

.my-answer__text {
  font-size: $font-size-xs;
  color: $text-2;
}

.wrong-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: $space-1;
}

.wrong-time {
  font-size: $font-size-xs;
  color: $text-3;
}

.wrong-actions {
  display: flex;
  align-items: center;
  gap: $space-2;
}

.aha-badge {
  padding: 6rpx 20rpx;
  background: #ECFDF5;
  border-radius: $r-pill;

  &__text {
    font-size: $font-size-xs;
    color: $success;
    font-weight: 600;
  }
}

.review-btn {
  height: 64rpx;
  padding: 0 $space-3;
  background: $primary;
  border-radius: $r-pill;
  border: none;
  display: flex;
  align-items: center;
  gap: $space-1;

  &::after { border: none; }

  &--loading {
    background: $primary;
    opacity: 0.75;
  }

  &__text {
    font-size: $font-size-xs;
    color: #fff;
    font-weight: 600;
  }
}

.spinner {
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  border: 3rpx solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

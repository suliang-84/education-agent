<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { assistantApi } from '@/api'
import { PAGES, SESSION_MODE_LABELS } from '@/constants'
import { fromNow } from '@/utils'
import type { ChatSession } from '@/api/assistant'

const sessions = ref<ChatSession[]>([])
const loading = ref(true)
const creating = ref(false)

onMounted(async () => {
  await loadSessions()
})

async function loadSessions() {
  loading.value = true
  try {
    sessions.value = await assistantApi.getSessions()
  } catch {
    sessions.value = []
  } finally {
    loading.value = false
  }
}

// ── 创建新对话（自由聊天） ────────────────────────────────────────────────
async function createFreeChat() {
  if (creating.value) return
  creating.value = true
  try {
    const resp = await assistantApi.createSession({ session_mode: 'free_chat' })
    uni.navigateTo({
      url: `${PAGES.ASSISTANT_CHAT}?session_id=${resp.session_id}&mode=${resp.session_mode}`,
    })
  } catch {
    uni.showToast({ title: '创建对话失败', icon: 'none' })
  } finally {
    creating.value = false
  }
}

// ── 创建错题复盘对话 ──────────────────────────────────────────────────────
async function createWrongReview() {
  if (creating.value) return
  creating.value = true
  try {
    const resp = await assistantApi.createSession({ session_mode: 'wrong_review' })
    uni.navigateTo({
      url: `${PAGES.ASSISTANT_CHAT}?session_id=${resp.session_id}&mode=${resp.session_mode}`,
    })
  } catch {
    uni.showToast({ title: '创建对话失败', icon: 'none' })
  } finally {
    creating.value = false
  }
}

// ── 进入历史对话 ──────────────────────────────────────────────────────────
function enterSession(s: ChatSession) {
  uni.navigateTo({
    url: `${PAGES.ASSISTANT_CHAT}?session_id=${s.session_id}&mode=${s.session_mode}`,
  })
}

// 获取会话模式标签样式颜色
const modeColors: Record<string, string> = {
  free_chat: '#4F46E5',
  wrong_review: '#E11D48',
  training_error_guidance: '#D97706',
}

// 获取状态标签
const statusLabels: Record<string, string> = {
  active: '进行中',
  ended: '已结束',
}
</script>

<template>
  <view class="assistant-page">
    <!-- ── 页面标题 ──────────────────────────────────────────── -->
    <view class="page-header">
      <text class="page-title">AI 助教</text>
      <button class="new-chat-btn" :disabled="creating" @tap="createFreeChat">
        <text class="new-chat-icon">+</text>
        <text class="new-chat-text">{{ creating ? '创建中...' : '新对话' }}</text>
      </button>
    </view>

    <!-- ── 快捷入口 ──────────────────────────────────────────── -->
    <view class="quick-actions">
      <view class="quick-card" @tap="createWrongReview">
        <text class="quick-icon">🔁</text>
        <view class="quick-info">
          <text class="quick-title">错题复盘</text>
          <text class="quick-desc">AI 带你突破错题</text>
        </view>
        <text class="quick-arrow">›</text>
      </view>
      <view class="quick-card" @tap="createFreeChat">
        <text class="quick-icon">💬</text>
        <view class="quick-info">
          <text class="quick-title">随便问问</text>
          <text class="quick-desc">自由提问，解惑答疑</text>
        </view>
        <text class="quick-arrow">›</text>
      </view>
    </view>

    <!-- ── 历史会话列表 ─────────────────────────────────────── -->
    <view class="section-header">
      <text class="section-title">历史对话</text>
      <text class="session-count">{{ sessions.length }} 个会话</text>
    </view>

    <!-- 加载骨架 -->
    <view v-if="loading" class="skeleton-list">
      <view v-for="i in 3" :key="i" class="skel-card">
        <view class="skel-badge" />
        <view class="skel-content">
          <view class="skel-line skel-line--title" />
          <view class="skel-line skel-line--desc" />
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="sessions.length === 0" class="empty-state">
      <text class="empty-icon">🗨️</text>
      <text class="empty-title">还没有对话记录</text>
      <text class="empty-desc">点击右上角「新对话」开始你的第一次 AI 对话</text>
    </view>

    <!-- 会话列表 -->
    <view v-else class="session-list">
      <view
        v-for="s in sessions"
        :key="s.session_id"
        class="session-card"
        @tap="enterSession(s)"
      >
        <!-- 模式徽标 -->
        <view
          class="mode-badge"
          :style="{ background: (modeColors[s.session_mode] || '#64748B') + '15', color: modeColors[s.session_mode] || '#64748B' }"
        >
          <text class="mode-badge__text">{{ SESSION_MODE_LABELS[s.session_mode] || s.session_mode }}</text>
        </view>

        <view class="session-info">
          <!-- 话题摘要 -->
          <text class="session-summary">
            {{ s.session_summary || '新对话' }}
          </text>

          <!-- 元数据行 -->
          <view class="session-meta">
            <view
              class="status-dot"
              :class="s.status === 'active' ? 'status-dot--active' : 'status-dot--ended'"
            />
            <text class="session-status">{{ statusLabels[s.status] || s.status }}</text>
            <text class="session-sep">·</text>
            <text class="session-turns">{{ s.aha_count }} 个 aha</text>
            <text class="session-sep">·</text>
            <text class="session-time">{{ fromNow(s.started_at) }}</text>
          </view>
        </view>

        <text class="session-arrow">›</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>

.assistant-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-4;
  padding-bottom: 160rpx;
}

// 页面标题
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-4;
}

.page-title {
  font-size: $font-size-2xl;
  color: $text-1;
  font-weight: 800;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  height: 68rpx;
  padding: 0 $space-3;
  background: $primary;
  border-radius: $r-pill;
  border: none;

  &::after { border: none; }
}

.new-chat-icon {
  font-size: 36rpx;
  color: #fff;
  font-weight: 300;
  line-height: 1;
}

.new-chat-text {
  font-size: $font-size-sm;
  color: #fff;
  font-weight: 600;
}

// 快捷入口
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: $space-2;
  margin-bottom: $space-4;
}

.quick-card {
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  display: flex;
  align-items: center;
  gap: $space-3;
  box-shadow: $shadow-sm;
  transition: $transition-fast;

  &:active {
    opacity: 0.85;
    transform: scale(0.99);
  }
}

.quick-icon {
  font-size: 44rpx;
  flex-shrink: 0;
}

.quick-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.quick-title {
  font-size: $font-size-base;
  color: $text-1;
  font-weight: 600;
}

.quick-desc {
  font-size: $font-size-xs;
  color: $text-3;
}

.quick-arrow {
  font-size: 36rpx;
  color: $text-3;
  flex-shrink: 0;
}

// section 头
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

.session-count {
  font-size: $font-size-xs;
  color: $text-3;
}

// 骨架屏
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.skel-card {
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  display: flex;
  gap: $space-3;
  box-shadow: $shadow-sm;
}

.skel-badge {
  width: 120rpx;
  height: 40rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  animation: shimmer 1.2s ease-in-out infinite;
  flex-shrink: 0;
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

  &--title { width: 70%; }
  &--desc { width: 50%; }
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
  padding: 100rpx $space-4;
}

.empty-icon {
  font-size: 100rpx;
}

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

// 会话列表
.session-list {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.session-card {
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  display: flex;
  align-items: flex-start;
  gap: $space-3;
  box-shadow: $shadow-sm;
  transition: $transition-fast;

  &:active {
    opacity: 0.85;
    transform: scale(0.99);
  }
}

.mode-badge {
  flex-shrink: 0;
  padding: 6rpx 20rpx;
  border-radius: $r-pill;
  margin-top: 4rpx;

  &__text {
    font-size: $font-size-xs;
    font-weight: 600;
  }
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.session-summary {
  font-size: $font-size-base;
  color: $text-1;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: $space-1;
  flex-wrap: wrap;
}

.status-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;

  &--active {
    background: $success;
  }

  &--ended {
    background: $text-3;
  }
}

.session-status,
.session-turns,
.session-time,
.session-sep {
  font-size: $font-size-xs;
  color: $text-3;
}

.session-arrow {
  font-size: 36rpx;
  color: $text-3;
  flex-shrink: 0;
  margin-top: 4rpx;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { assistantApi } from '@/api'
import { SESSION_MODE_LABELS } from '@/constants'
import { fromNow } from '@/utils'
import type { ChatSession } from '@/api/assistant'

const sessions = ref<ChatSession[]>([])
const loading = ref(true)

const modeColors: Record<string, string> = {
  free_chat: '#4F46E5',
  wrong_review: '#E11D48',
  training_error_guidance: '#D97706',
}

onMounted(async () => {
  try {
    sessions.value = await assistantApi.getSessions()
  } catch {
    sessions.value = []
  } finally {
    loading.value = false
  }
})

function enterSession(s: ChatSession) {
  // 将选中的会话信息存入缓存，index.vue 读取后进入该会话
  uni.setStorageSync('mesh_resume_session', JSON.stringify({
    session_id: s.session_id,
    session_mode: s.session_mode,
    status: s.status,
  }))
  uni.switchTab({ url: '/pages/assistant/index' })
}
</script>

<template>
  <view class="history-page">
    <view v-if="loading" class="skeleton-list">
      <view v-for="i in 5" :key="i" class="skel-card" />
    </view>

    <view v-else-if="sessions.length === 0" class="empty-state">
      <text class="empty-icon">🗨️</text>
      <text class="empty-title">暂无历史对话</text>
    </view>

    <scroll-view v-else scroll-y class="session-list">
      <view
        v-for="s in sessions"
        :key="s.session_id"
        class="session-card"
        @tap="enterSession(s)"
      >
        <view class="session-left">
          <view
            class="mode-dot"
            :style="{ background: modeColors[s.session_mode] || '#64748B' }"
          />
          <view class="session-info">
            <text class="session-summary">{{ s.session_summary || '新对话' }}</text>
            <view class="session-meta">
              <text class="meta-tag">{{ SESSION_MODE_LABELS[s.session_mode] || s.session_mode }}</text>
              <text class="meta-sep">·</text>
              <text class="meta-time">{{ fromNow(s.started_at) }}</text>
              <template v-if="s.aha_count > 0">
                <text class="meta-sep">·</text>
                <text class="meta-aha">💡 {{ s.aha_count }}</text>
              </template>
            </view>
          </view>
        </view>
        <view class="session-right">
          <view v-if="s.status === 'active'" class="active-dot" />
          <text class="arrow">›</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<style lang="scss" scoped>
.history-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-4;
  padding-bottom: 80rpx;
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.skel-card {
  height: 120rpx;
  background: $bg-surface;
  border-radius: $r-lg;
  animation: shimmer 1.2s ease-in-out infinite;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 200rpx;
  gap: $space-3;
}

.empty-icon { font-size: 100rpx; }

.empty-title {
  font-size: $font-size-lg;
  color: $text-2;
  font-weight: 600;
}

.session-list {
  height: calc(100vh - 120rpx);
}

.session-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  margin-bottom: $space-2;
  box-shadow: $shadow-sm;

  &:active { opacity: 0.85; }
}

.session-left {
  display: flex;
  align-items: center;
  gap: $space-3;
  flex: 1;
  min-width: 0;
}

.mode-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
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
}

.meta-tag, .meta-sep, .meta-time, .meta-aha {
  font-size: $font-size-xs;
  color: $text-3;
}

.session-right {
  display: flex;
  align-items: center;
  gap: $space-2;
  flex-shrink: 0;
}

.active-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: $success;
}

.arrow {
  font-size: 36rpx;
  color: $text-3;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

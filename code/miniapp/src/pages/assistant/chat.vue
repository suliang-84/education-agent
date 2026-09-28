<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { assistantApi, profileApi } from '@/api'
import { PAGES, FIVE_POWER_LABELS, FIVE_POWER_COLORS, SESSION_MODE_LABELS } from '@/constants'
import { fromNow } from '@/utils'
import type { ChatMessage } from '@/api/assistant'
import type { FivePowerProfile } from '@/api/profile'

// ── 页面参数 ──────────────────────────────────────────────────────────────
const sessionId = ref('')
const sessionMode = ref('')
const messages = ref<ChatMessage[]>([])
const loading = ref(true)
const sending = ref(false)
const inputText = ref('')
const sessionEnded = ref(false)

// ── 五力状态（可折叠） ────────────────────────────────────────────────────
const fivePower = ref<FivePowerProfile | null>(null)
const showPowerCard = ref(false)

// ── 消息评分状态（记录每条消息的评分） ────────────────────────────────────
const ratings = ref<Record<number, 'like' | 'dislike'>>({})

const modeTitle = computed(() => SESSION_MODE_LABELS[sessionMode.value] || '对话')

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const options = (current as any)?.options || {}
  sessionId.value = options.session_id || ''
  sessionMode.value = options.mode || 'free_chat'

  // 并行加载：历史消息 + 五力画像
  await Promise.all([loadMessages(), loadFivePower()])
  loading.value = false
  scrollToBottom()
})

async function loadMessages() {
  if (!sessionId.value) return
  try {
    messages.value = await assistantApi.getMessages(sessionId.value)
  } catch {
    messages.value = []
  }
}

async function loadFivePower() {
  try {
    fivePower.value = await profileApi.getFivePower()
  } catch {
    fivePower.value = null
  }
}

// ── 发送消息 ──────────────────────────────────────────────────────────────
async function sendMessage() {
  const content = inputText.value.trim()
  if (!content || sending.value || sessionEnded.value) return
  sending.value = true
  inputText.value = ''

  // 乐观更新：先在本地追加学生消息
  const tempMsg: ChatMessage = {
    message_id: Date.now(), // 临时 ID
    role: 'student',
    content,
    is_aha_trigger: false,
    created_at: new Date().toISOString(),
  }
  messages.value.push(tempMsg)
  scrollToBottom()

  try {
    const aiResp = await assistantApi.sendMessage(sessionId.value, content)
    // 追加 AI 回复
    messages.value.push(aiResp)
    scrollToBottom()
  } catch {
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
    // 回滚乐观更新
    messages.value.pop()
    inputText.value = content
  } finally {
    sending.value = false
  }
}

// ── 消息评分 ──────────────────────────────────────────────────────────────
async function rateMessage(msg: ChatMessage, rating: 'like' | 'dislike') {
  if (ratings.value[msg.message_id] === rating) return // 防重复
  ratings.value[msg.message_id] = rating
  try {
    await assistantApi.rateMessage(msg.message_id, rating)
  } catch {
    delete ratings.value[msg.message_id]
  }
}

// ── 结束会话 ──────────────────────────────────────────────────────────────
function confirmEnd() {
  uni.showModal({
    title: '结束对话',
    content: '确认结束本次对话？对话记录将会保留。',
    confirmText: '结束对话',
    success: async (res) => {
      if (res.confirm) {
        try {
          await assistantApi.endSession(sessionId.value)
          sessionEnded.value = true
          uni.showToast({ title: '对话已结束', icon: 'success' })
        } catch {
          uni.showToast({ title: '操作失败', icon: 'none' })
        }
      }
    },
  })
}

// ── 自动滚动到底部 ────────────────────────────────────────────────────────
const scrollViewId = `msg-bottom-${Date.now()}`
function scrollToBottom() {
  nextTick(() => {
    // 通过设置 scroll-into-view 实现滚动
  })
}

// 五力分数（取 final × 100）
const weakestPowers = computed(() => {
  if (!fivePower.value?.profile) return []
  return Object.entries(fivePower.value.profile.forces)
    .map(([k, v]) => ({ key: k, score: Math.round(v.final * 100) }))
    .sort((a, b) => a.score - b.score)
    .slice(0, 3)
})
</script>

<template>
  <view class="chat-page">
    <!-- ── 自定义导航栏 ──────────────────────────────────────── -->
    <view class="nav-bar">
      <view class="nav-back" @tap="uni.navigateBack()">
        <text class="nav-back__icon">‹</text>
      </view>
      <view class="nav-center">
        <text class="nav-title">{{ modeTitle }}</text>
        <view v-if="sessionEnded" class="ended-tag">
          <text class="ended-tag__text">已结束</text>
        </view>
      </view>
      <button
        v-if="!sessionEnded"
        class="end-btn"
        @tap="confirmEnd"
      >
        <text class="end-btn__text">结束对话</text>
      </button>
    </view>

    <!-- ── 五力状态折叠卡 ──────────────────────────────────── -->
    <view class="power-mini-card" @tap="showPowerCard = !showPowerCard">
      <view class="power-mini-header">
        <text class="power-mini-title">🧠 五力状态</text>
        <text class="power-mini-toggle">{{ showPowerCard ? '收起 ▲' : '展开 ▼' }}</text>
      </view>
      <!-- 展开内容 -->
      <view v-if="showPowerCard && weakestPowers.length > 0" class="power-mini-content">
        <view
          v-for="p in weakestPowers"
          :key="p.key"
          class="power-mini-item"
        >
          <view
            class="power-mini-bar-wrap"
          >
            <view
              class="power-mini-bar"
              :style="{ width: `${p.score}%`, background: FIVE_POWER_COLORS[p.key as keyof typeof FIVE_POWER_COLORS] }"
            />
          </view>
          <text class="power-mini-name">{{ FIVE_POWER_LABELS[p.key as keyof typeof FIVE_POWER_LABELS] }}</text>
          <text class="power-mini-score" :style="{ color: FIVE_POWER_COLORS[p.key as keyof typeof FIVE_POWER_COLORS] }">{{ p.score }}</text>
        </view>
      </view>
    </view>

    <!-- ── 消息列表 ────────────────────────────────────────── -->
    <scroll-view
      class="message-list"
      scroll-y
      :scroll-into-view="messages.length > 0 ? `msg-${messages[messages.length - 1]?.message_id}` : ''"
      scroll-with-animation
    >
      <!-- 加载骨架 -->
      <view v-if="loading" class="loading-state">
        <view v-for="i in 3" :key="i" class="skel-msg" :class="i % 2 === 0 ? 'skel-msg--right' : 'skel-msg--left'" />
      </view>

      <template v-else>
        <!-- 空状态 -->
        <view v-if="messages.length === 0" class="empty-chat">
          <text class="empty-chat__icon">🤖</text>
          <text class="empty-chat__text">你好！我是你的 AI 助教 MESH，有什么可以帮你？</text>
        </view>

        <!-- 消息气泡 -->
        <view
          v-for="msg in messages"
          :key="msg.message_id"
          :id="`msg-${msg.message_id}`"
          class="msg-row"
          :class="msg.role === 'student' ? 'msg-row--right' : 'msg-row--left'"
        >
          <!-- AI 头像 -->
          <view v-if="msg.role === 'assistant'" class="ai-avatar">
            <text class="ai-avatar__icon">🤖</text>
          </view>

          <!-- 消息体 -->
          <view class="msg-bubble-wrap" :class="msg.role === 'student' ? 'msg-bubble-wrap--right' : ''">
            <!-- aha 触发标记 -->
            <view v-if="msg.is_aha_trigger" class="aha-tag">
              <text class="aha-tag__text">💡 思维突破</text>
            </view>

            <view class="msg-bubble" :class="msg.role === 'student' ? 'msg-bubble--student' : 'msg-bubble--ai'">
              <text class="msg-text">{{ msg.content }}</text>
            </view>

            <!-- AI 消息底部：时间 + 评分 -->
            <view v-if="msg.role === 'assistant'" class="msg-actions">
              <text class="msg-time">{{ fromNow(msg.created_at) }}</text>
              <view class="rating-bar">
                <view
                  class="rating-btn"
                  :class="{ 'rating-btn--active': ratings[msg.message_id] === 'like' }"
                  @tap="rateMessage(msg, 'like')"
                >
                  <text class="rating-icon">👍</text>
                </view>
                <view
                  class="rating-btn"
                  :class="{ 'rating-btn--active': ratings[msg.message_id] === 'dislike' }"
                  @tap="rateMessage(msg, 'dislike')"
                >
                  <text class="rating-icon">👎</text>
                </view>
              </view>
            </view>

            <!-- 学生消息：只显示时间 -->
            <text v-if="msg.role === 'student'" class="msg-time msg-time--right">{{ fromNow(msg.created_at) }}</text>
          </view>
        </view>

        <!-- AI 正在输入提示 -->
        <view v-if="sending" class="msg-row msg-row--left">
          <view class="ai-avatar">
            <text class="ai-avatar__icon">🤖</text>
          </view>
          <view class="typing-indicator">
            <view class="typing-dot" />
            <view class="typing-dot" />
            <view class="typing-dot" />
          </view>
        </view>
      </template>
    </scroll-view>

    <!-- ── 输入栏 ───────────────────────────────────────────── -->
    <view class="input-bar" :class="{ 'input-bar--ended': sessionEnded }">
      <view v-if="sessionEnded" class="ended-notice">
        <text class="ended-notice__text">对话已结束，无法继续发送消息</text>
      </view>
      <template v-else>
        <textarea
          v-model="inputText"
          class="input-textarea"
          placeholder="输入消息..."
          placeholder-class="input-placeholder"
          :maxlength="1000"
          :auto-height="true"
          :show-confirm-bar="false"
        />
        <button
          class="send-btn"
          :class="{ 'send-btn--disabled': !inputText.trim() || sending }"
          :disabled="!inputText.trim() || sending"
          @tap="sendMessage"
        >
          <text class="send-btn__icon">{{ sending ? '⏳' : '▶' }}</text>
        </button>
      </template>
    </view>
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-page;
}

// 导航栏
.nav-bar {
  display: flex;
  align-items: center;
  height: 100rpx;
  padding: 0 $space-4;
  padding-top: env(safe-area-inset-top);
  background: $bg-surface;
  box-shadow: $shadow-sm;
  flex-shrink: 0;
  z-index: 10;
}

.nav-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &__icon {
    font-size: 48rpx;
    color: $text-1;
    font-weight: 300;
  }
}

.nav-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;
}

.nav-title {
  font-size: $font-size-lg;
  color: $text-1;
  font-weight: 700;
}

.ended-tag {
  background: $bg-muted;
  border-radius: $r-pill;
  padding: 4rpx 16rpx;

  &__text {
    font-size: $font-size-xs;
    color: $text-3;
  }
}

.end-btn {
  flex-shrink: 0;
  height: 60rpx;
  padding: 0 $space-3;
  background: $danger-light;
  border: 2rpx solid $danger;
  border-radius: $r-pill;

  &::after { border: none; }

  &__text {
    font-size: $font-size-xs;
    color: $danger;
    font-weight: 600;
  }
}

// 五力迷你卡
.power-mini-card {
  background: $bg-surface;
  margin: 0;
  padding: $space-3 $space-4;
  border-bottom: 1rpx solid $border;
  flex-shrink: 0;
}

.power-mini-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.power-mini-title {
  font-size: $font-size-sm;
  color: $text-2;
  font-weight: 600;
}

.power-mini-toggle {
  font-size: $font-size-xs;
  color: $primary;
}

.power-mini-content {
  margin-top: $space-2;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.power-mini-item {
  display: flex;
  align-items: center;
  gap: $space-2;
}

.power-mini-bar-wrap {
  flex: 1;
  height: 10rpx;
  background: $bg-muted;
  border-radius: $r-pill;
  overflow: hidden;
}

.power-mini-bar {
  height: 100%;
  border-radius: $r-pill;
}

.power-mini-name {
  font-size: $font-size-xs;
  color: $text-3;
  width: 80rpx;
  flex-shrink: 0;
}

.power-mini-score {
  font-size: $font-size-xs;
  font-weight: 700;
  width: 48rpx;
  text-align: right;
  flex-shrink: 0;
}

// 消息列表
.message-list {
  flex: 1;
  padding: $space-4;
  overflow: hidden;
}

.loading-state {
  display: flex;
  flex-direction: column;
  gap: $space-4;
}

.skel-msg {
  height: 80rpx;
  border-radius: $r-xl;
  background: $bg-muted;
  animation: shimmer 1.2s ease-in-out infinite;
  max-width: 70%;

  &--left { align-self: flex-start; width: 60%; }
  &--right { align-self: flex-end; width: 40%; margin-left: auto; }
}

// 空状态
.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
  padding: $space-6 $space-4;
}

.empty-chat__icon {
  font-size: 80rpx;
}

.empty-chat__text {
  font-size: $font-size-base;
  color: $text-2;
  text-align: center;
  line-height: 1.7;
}

// 消息行
.msg-row {
  display: flex;
  align-items: flex-end;
  gap: $space-2;
  margin-bottom: $space-4;

  &--right {
    flex-direction: row-reverse;
  }
}

.ai-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, $primary, #7C3AED);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &__icon {
    font-size: 36rpx;
  }
}

.msg-bubble-wrap {
  display: flex;
  flex-direction: column;
  max-width: 76%;

  &--right {
    align-items: flex-end;
  }
}

.aha-tag {
  background: $warning-light;
  border-radius: $r-pill;
  padding: 4rpx 16rpx;
  margin-bottom: 8rpx;
  align-self: flex-start;

  &__text {
    font-size: $font-size-xs;
    color: $warning;
    font-weight: 600;
  }
}

.msg-bubble {
  padding: $space-3 $space-4;
  border-radius: $r-xl;
  max-width: 100%;

  &--ai {
    background: $bg-surface;
    border: 1rpx solid $border;
    border-bottom-left-radius: $r-sm;
    box-shadow: $shadow-sm;
  }

  &--student {
    background: $primary;
    border-bottom-right-radius: $r-sm;
  }
}

.msg-text {
  font-size: $font-size-base;
  line-height: 1.7;
  color: $text-1;

  .msg-bubble--student & {
    color: #fff;
  }
}

// 操作栏（时间 + 评分）
.msg-actions {
  display: flex;
  align-items: center;
  gap: $space-3;
  margin-top: $space-1;
}

.msg-time {
  font-size: $font-size-xs;
  color: $text-3;

  &--right {
    display: block;
    text-align: right;
    margin-top: $space-1;
  }
}

.rating-bar {
  display: flex;
  gap: $space-2;
}

.rating-btn {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: $bg-muted;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $transition-fast;

  &--active {
    background: $primary-light;
    box-shadow: 0 0 0 2rpx $primary;
  }
}

.rating-icon {
  font-size: 24rpx;
}

// 正在输入
.typing-indicator {
  display: flex;
  gap: 10rpx;
  padding: $space-3 $space-4;
  background: $bg-surface;
  border-radius: $r-xl;
  border: 1rpx solid $border;
  box-shadow: $shadow-sm;
}

.typing-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: $text-3;
  animation: bounce 0.9s ease-in-out infinite;

  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

// 输入栏
.input-bar {
  background: $bg-surface;
  padding: $space-2 $space-4;
  padding-bottom: calc($space-2 + env(safe-area-inset-bottom));
  border-top: 1rpx solid $border;
  display: flex;
  align-items: flex-end;
  gap: $space-2;
  flex-shrink: 0;

  &--ended {
    justify-content: center;
  }
}

.ended-notice {
  padding: $space-2 0;
}

.ended-notice__text {
  font-size: $font-size-sm;
  color: $text-3;
}

.input-textarea {
  flex: 1;
  min-height: 72rpx;
  max-height: 200rpx;
  font-size: $font-size-base;
  color: $text-1;
  background: $bg-muted;
  border-radius: $r-lg;
  padding: $space-2 $space-3;
  line-height: 1.5;
}

.send-btn {
  flex-shrink: 0;
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: $primary;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;

  &::after { border: none; }

  &--disabled {
    background: $bg-muted;
  }

  &__icon {
    font-size: 32rpx;
    color: #fff;

    .send-btn--disabled & { color: $text-3; }
  }
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

<script setup lang="ts">
import { useTheme } from '@/hooks/useTheme'
import { ref, onMounted } from 'vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { assistantApi } from '@/api'
import { fromNow } from '@/utils'
import type { ChatMessage } from '@/api/assistant'


const { pageStyle, hl } = useTheme()
const sessionId = ref('')
const messages = ref<ChatMessage[]>([])
const loading = ref(true)
const sending = ref(false)
const inputText = ref('')
const ratings = ref<Record<number, 'like' | 'dislike'>>({})

onMounted(async () => {
  loading.value = true
  try {
    const resp = await assistantApi.createSession({ session_mode: 'free_chat' })
    sessionId.value = resp.session_id
    messages.value = await assistantApi.getMessages(resp.session_id)
  } catch {
    messages.value = []
  } finally {
    loading.value = false
    scrollToBottom()
  }
})

async function sendMessage() {
  const content = inputText.value.trim()
  if (!content || sending.value) return
  sending.value = true
  inputText.value = ''

  const tempMsg: ChatMessage = {
    message_id: Date.now(),
    role: 'student',
    content,
    is_aha_trigger: false,
    created_at: new Date().toISOString(),
  }
  messages.value.push(tempMsg)
  scrollToBottom()

  try {
    const aiResp = await assistantApi.sendMessage(sessionId.value, content)
    messages.value.push(aiResp)
    scrollToBottom()
  } catch {
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
    messages.value.pop()
    inputText.value = content
  } finally {
    sending.value = false
  }
}

async function rateMessage(msg: ChatMessage, rating: 'like' | 'dislike') {
  if (ratings.value[msg.message_id] === rating) return
  ratings.value[msg.message_id] = rating
  try {
    await assistantApi.rateMessage(msg.message_id, rating)
  } catch {
    delete ratings.value[msg.message_id]
  }
}

function scrollToBottom() {
  // scroll-into-view 由模板绑定实现
}
</script>

<template>
  <page-meta :page-style="pageStyle" />
  <view class="chat-page">

    <!-- ── 消息列表 ────────────────────────────────────────────── -->
    <scroll-view
      class="message-list"
      scroll-y
      :scroll-into-view="messages.length > 0 ? `msg-${messages[messages.length - 1]?.message_id}` : ''"
      scroll-with-animation
    >
      <view v-if="loading" class="loading-state">
        <view v-for="i in 3" :key="i" class="skel-msg" :class="i % 2 === 0 ? 'skel-msg--right' : 'skel-msg--left'" />
      </view>

      <template v-else>
        <view v-if="messages.length === 0" class="empty-chat">
          <view class="empty-chat__icon"><SvgIcon name="sparkles" :size="72" /></view>
          <text class="empty-chat__title">你好，我是 MESH</text>
          <text class="empty-chat__text">有什么数理化问题，尽管问我～</text>
        </view>

        <view
          v-for="msg in messages"
          :key="msg.message_id"
          :id="`msg-${msg.message_id}`"
          class="msg-row"
          :class="msg.role === 'student' ? 'msg-row--right' : 'msg-row--left'"
        >
          <view v-if="msg.role === 'assistant'" class="ai-avatar">
            <SvgIcon name="sparkles" :size="36" color="on-primary" />
          </view>

          <view class="msg-bubble-wrap" :class="msg.role === 'student' ? 'msg-bubble-wrap--right' : ''">
            <view v-if="msg.is_aha_trigger" class="aha-tag">
              <SvgIcon name="bulb" :size="24" color="#D97706" />
              <text class="aha-tag__text">思维突破</text>
            </view>
            <view class="msg-bubble" :class="msg.role === 'student' ? 'msg-bubble--student' : 'msg-bubble--ai'">
              <text class="msg-text" :class="msg.role === 'student' ? 'msg-text--student' : ''">{{ msg.content }}</text>
            </view>
            <view v-if="msg.role === 'assistant'" class="msg-actions">
              <text class="msg-time">{{ fromNow(msg.created_at) }}</text>
              <view class="rating-bar">
                <view class="rating-btn" :class="{ 'rating-btn--active': ratings[msg.message_id] === 'like' }" @tap="rateMessage(msg, 'like')">
                  <text class="rating-icon">▲</text>
                </view>
                <view class="rating-btn" :class="{ 'rating-btn--active': ratings[msg.message_id] === 'dislike' }" @tap="rateMessage(msg, 'dislike')">
                  <text class="rating-icon">▼</text>
                </view>
              </view>
            </view>
            <text v-if="msg.role === 'student'" class="msg-time msg-time--right">{{ fromNow(msg.created_at) }}</text>
          </view>
        </view>

        <view v-if="sending" class="msg-row msg-row--left">
          <view class="ai-avatar">
            <SvgIcon name="sparkles" :size="36" color="on-primary" />
          </view>
          <view class="typing-indicator">
            <view class="typing-dot" />
            <view class="typing-dot" />
            <view class="typing-dot" />
          </view>
        </view>
      </template>
    </scroll-view>

    <!-- ── 底部输入栏（常驻）──────────────────────────────────── -->
    <view class="input-bar">
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
        <text class="send-btn__icon">{{ sending ? '…' : '▶' }}</text>
      </button>
    </view>

  </view>
</template>

<style lang="scss" scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-page;
}

.message-list {
  flex: 1;
  padding: $space-4;
  overflow: hidden;
}

.loading-state {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.skel-msg {
  height: 80rpx;
  background: $bg-muted;
  border-radius: $r-lg;
  animation: shimmer 1.2s ease-in-out infinite;
  width: 65%;
  &--right { margin-left: auto; }
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 160rpx;
  gap: $space-2;

  &__icon {
    width: 160rpx; height: 160rpx; border-radius: $r-xl;
    background: $primary-light; border: 1rpx solid $primary-border;
    display: flex; align-items: center; justify-content: center;
  }
  &__title { font-size: $font-size-xl; font-weight: 700; color: $text-1; margin-top: $space-2; }
  &__text { font-size: $font-size-sm; color: $text-3; }
}

.msg-row {
  display: flex;
  align-items: flex-end;
  gap: $space-2;
  margin-bottom: $space-4;
  &--right { flex-direction: row-reverse; }
}

.ai-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: $cta-gradient;
  box-shadow: $shadow-cta;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.msg-bubble-wrap {
  max-width: 72%;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  &--right { align-items: flex-end; }
}

.aha-tag {
  background: $warning-light;
  border: 1rpx solid rgba(217, 119, 6, 0.2);
  border-radius: $r-pill;
  padding: 4rpx 20rpx;
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 8rpx;
  &__text { font-size: $font-size-xs; color: $power-adapt; font-weight: 600; }
}

.msg-bubble {
  padding: $space-3 $space-4;
  border-radius: $r-xl;
  line-height: 1.7;

  &--ai {
    background: $bg-surface;
    border: 1rpx solid $border;
    border-bottom-left-radius: $r-sm;
    box-shadow: $shadow-sm;
  }
  &--student {
    background: $cta-gradient;
    border-bottom-right-radius: $r-sm;
    box-shadow: $shadow-cta;
  }
}

.msg-text {
  font-size: $font-size-base;
  color: $text-1;
  &--student { color: $on-primary; }
}

.msg-actions {
  display: flex;
  align-items: center;
  gap: $space-2;
  padding: 0 4rpx;
}

.msg-time {
  font-size: $font-size-xs;
  color: $text-3;
  &--right { display: block; text-align: right; }
}

.rating-bar { display: flex; gap: $space-1; }

.rating-btn {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-muted;
  &--active { background: $primary-light; box-shadow: 0 0 0 2rpx $primary-border; .rating-icon { color: $primary; } }
}

.rating-icon { font-size: 20rpx; color: $text-3; }

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 10rpx;
  padding: $space-3 $space-4;
  background: $bg-surface;
  border: 1rpx solid $border;
  border-radius: $r-xl;
  border-bottom-left-radius: $r-sm;
  box-shadow: $shadow-sm;
}

.typing-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: $primary;
  animation: bounce 0.9s ease-in-out infinite;
  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
}

.input-bar {
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  gap: $space-2;
  padding: $space-3 $space-4;
  padding-bottom: calc(#{$space-3} + env(safe-area-inset-bottom));
  background: $bg-surface;
  box-shadow: $shadow-sm;
  border-top: 1rpx solid $border;
}

.input-textarea {
  flex: 1;
  min-height: 72rpx;
  max-height: 240rpx;
  padding: $space-2 $space-3;
  background: $bg-surface;
  border: 1rpx solid $border;
  border-radius: $r-xl;
  font-size: $font-size-base;
  color: $text-1;
  line-height: 1.6;
}

.send-btn {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: $cta-gradient;
  box-shadow: $shadow-cta;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  flex-shrink: 0;

  &::after { border: none; }
  &--disabled { background: $bg-muted; box-shadow: none; }
  &__icon { font-size: 28rpx; color: $on-primary; .send-btn--disabled & { color: $text-3; } }
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}
</style>

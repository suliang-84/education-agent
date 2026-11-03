<script setup lang="ts">
/**
 * AI 助教（Tab）：单一永久会话
 *
 * - 进入即是同一个会话，历史自动加载（向上翻页），没有「新对话 / 结束对话 / 历史记录」
 * - AI 回复以打字机效果逐字显示（后端一次生成完整回复，前端逐字展示；点气泡可直接显示全部）
 * - 回复下方：复制、点赞、点踩、重新生成（换一种启发策略）；理解突破时 AI 会发一张「✨ 突破」成就感卡片
 * - 对话为空时显示按学生情况生成的快捷提问；输入框左侧相机按钮可拍照 / 选图：图片只上传不解析，和你输入的问题一起发给 AI 助教，由助教回答
 * - 学生说「我自己想」后进入沉默模式（AI 暂停主动引导），输入框上方出现「点击恢复」条
 */
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useTheme } from '@/hooks/useTheme'
import SvgIcon from '@/components/SvgIcon.vue'
import { assistantApi } from '@/api'
import { assetUrl } from '@/utils/request'
import type { ChatMessage } from '@/api/assistant'

const { pageStyle, hl } = useTheme()

const MAX_LEN = 500
const SILENCE_MIN = 10

const sessionId = ref('')
const messages = ref<ChatMessage[]>([])
const loading = ref(true)
const loadFailed = ref(false)
const hasMore = ref(false)
const loadingMore = ref(false)
const sending = ref(false)            // 等待 AI 回复中（显示「思考中」）
const inputText = ref('')
const uploading = ref(false)          // 图片上传中
const pendingImage = ref<{ local: string; remote: string } | null>(null)   // 已选好、等随下一条消息发送的图片
const suggestions = ref<string[]>([])
const silence = ref(false)
const silenceAt = ref(0)
const scrollInto = ref('')

// ── 打字机效果 ────────────────────────────────────────────────────────────
const typingId = ref<number | null>(null)
const typingShown = ref(0)
let typingTimer: ReturnType<typeof setInterval> | null = null

function startTyping(id: number, total: number) {
  stopTyping()
  typingId.value = id
  typingShown.value = 0
  let tick = 0
  typingTimer = setInterval(() => {
    typingShown.value += 3
    if (++tick % 6 === 0) scrollToBottom()
    if (typingShown.value >= total) {
      stopTyping()
      scrollToBottom()
    }
  }, 30)
}
function stopTyping() {
  if (typingTimer) { clearInterval(typingTimer); typingTimer = null }
  typingId.value = null
}
function shownText(m: ChatMessage): string {
  return m.message_id === typingId.value ? m.content.slice(0, typingShown.value) : m.content
}
onUnmounted(stopTyping)

// ── 加载 ──────────────────────────────────────────────────────────────────
async function init() {
  loading.value = true
  loadFailed.value = false
  try {
    const s = await assistantApi.getSession()
    sessionId.value = s.session_id
    setSilence(s.silence)
    const page = await assistantApi.getMessages(s.session_id)
    messages.value = page.messages
    hasMore.value = page.has_more
    loadSuggestions()
  } catch {
    loadFailed.value = true
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function loadSuggestions() {
  try { suggestions.value = (await assistantApi.getSuggestions()).suggestions } catch { suggestions.value = [] }
}

onMounted(init)

async function loadOlder() {
  if (loadingMore.value || !hasMore.value || !messages.value.length) return
  loadingMore.value = true
  const firstId = messages.value[0].message_id
  try {
    const page = await assistantApi.getMessages(sessionId.value, firstId)
    messages.value = [...page.messages, ...messages.value]
    hasMore.value = page.has_more
    await nextTick()
    scrollInto.value = `msg-${firstId}`      // 保持在原来看到的位置
  } catch { /* 静默：下次上滑再试 */ } finally {
    loadingMore.value = false
  }
}

function scrollToBottom() {
  scrollInto.value = ''
  nextTick(() => { scrollInto.value = 'chat-bottom' })
}

// ── 沉默模式 ──────────────────────────────────────────────────────────────
function setSilence(v: boolean) {
  silence.value = v
  silenceAt.value = v ? Date.now() : 0
}
const silenceVisible = computed(() => silence.value && Date.now() - silenceAt.value < SILENCE_MIN * 60 * 1000)

async function resumeSilence() {
  setSilence(false)
  try { await assistantApi.resumeSilence(sessionId.value) } catch { /* 请求层已提示 */ }
}

// ── 发送 ──────────────────────────────────────────────────────────────────
let tempSeq = 0
async function send(text?: string) {
  const content = (text ?? inputText.value).trim()
  const img = text === undefined ? pendingImage.value : null
  if (sending.value || !sessionId.value) return
  if (uploading.value) { uni.showToast({ title: '图片上传中，请稍候', icon: 'none' }); return }
  if (!content && !img) return                                  // 没有内容时什么也不做
  sending.value = true
  if (text === undefined) { inputText.value = ''; pendingImage.value = null }
  const tempId = -(++tempSeq)
  messages.value.push({ message_id: tempId, role: 'student', content, image_url: img?.local ?? null, is_aha_trigger: false, created_at: new Date().toISOString() })
  scrollToBottom()
  try {
    const res = await assistantApi.sendMessage(sessionId.value, content, img?.remote)
    const mine = messages.value.find((m) => m.message_id === tempId)
    if (mine) mine.message_id = res.student_message_id
    setSilence(res.silence)
    messages.value.push({ message_id: res.message_id, role: 'assistant', content: res.content, is_aha_trigger: res.is_aha_trigger, rating: null, created_at: res.created_at })
    startTyping(res.message_id, res.content.length)
  } catch {
    // 失败原因（内容安全、过长、AI 暂不可用、模型不支持看图）已由请求层弹出提示：撤回这条消息，文字和图片放回输入区，方便修改后重发
    messages.value = messages.value.filter((m) => m.message_id !== tempId)
    if (text === undefined) { inputText.value = content; pendingImage.value = img }
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

// ── 消息操作 ──────────────────────────────────────────────────────────────
function copyMsg(m: ChatMessage) {
  uni.setClipboardData({ data: m.content })
}

async function rate(m: ChatMessage, r: 'like' | 'dislike') {
  if (m.rating === r) return
  const old = m.rating
  m.rating = r
  try { await assistantApi.rateMessage(m.message_id, r) } catch { m.rating = old }
}

const regenerating = ref<number | null>(null)
async function regenerate(m: ChatMessage) {
  if (regenerating.value !== null || sending.value) return
  regenerating.value = m.message_id
  try {
    const res = await assistantApi.regenerate(sessionId.value, m.message_id)
    m.content = res.content
    m.rating = null
    startTyping(m.message_id, res.content.length)
  } catch { /* 请求层已提示 */ } finally {
    regenerating.value = null
  }
}
// 最后一条（非成就感）AI 回复默认显示「重新生成」，点踩后任何一条都显示
const lastAiId = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    const m = messages.value[i]
    if (m.role === 'assistant' && !m.is_aha_trigger) return m.message_id
  }
  return null
})

// ── 图片提问 ──────────────────────────────────────────────────────────────
// 选好图片后先上传（只保存，不解析），在输入区显示缩略图；学生可以补充问题，点发送时图片和问题一起发给 AI 助教
function pickImage() {
  if (uploading.value || sending.value) return
  uni.chooseMedia({
    count: 1,
    mediaType: ['image'],
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const f = res.tempFiles?.[0]
      if (!f) return
      if (f.size > 5 * 1024 * 1024) { uni.showToast({ title: '图片太大，请换一张（≤5MB）', icon: 'none' }); return }
      upload(f.tempFilePath, /\.png$/i.test(f.tempFilePath) ? 'image/png' : 'image/jpeg')
    },
  })
}
function upload(path: string, mediaType: string) {
  uploading.value = true
  pendingImage.value = { local: path, remote: '' }
  uni.getFileSystemManager().readFile({
    filePath: path,
    encoding: 'base64',
    success: async (r) => {
      try {
        const res = await assistantApi.uploadImage(r.data as string, mediaType)
        if (pendingImage.value?.local === path) pendingImage.value = { local: path, remote: res.image_url }
      } catch {
        pendingImage.value = null   // 失败原因已由请求层提示
      } finally {
        uploading.value = false
      }
    },
    fail: () => { uploading.value = false; pendingImage.value = null; uni.showToast({ title: '读取图片失败', icon: 'none' }) },
  })
}
function removeImage() {
  if (uploading.value) return
  pendingImage.value = null
}
function imgSrc(m: ChatMessage): string {
  return assetUrl(m.image_url)
}
function previewImg(m: ChatMessage) {
  const u = imgSrc(m)
  if (u) uni.previewImage({ urls: [u], current: u })
}

// ── 展示 ──────────────────────────────────────────────────────────────────
function pad(n: number) { return n < 10 ? `0${n}` : `${n}` }
function timeLabel(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const hm = `${pad(d.getHours())}:${pad(d.getMinutes())}`
  if (d.toDateString() === now.toDateString()) return hm
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${hm}`
}
// 与上一条间隔超过 5 分钟才显示时间
function showTime(i: number): boolean {
  if (i === 0) return true
  return new Date(messages.value[i].created_at).getTime() - new Date(messages.value[i - 1].created_at).getTime() > 5 * 60 * 1000
}

const showSuggestions = computed(() => !loading.value && !loadFailed.value && messages.value.length <= 1 && suggestions.value.length > 0 && !sending.value)
// 输入框只有一行时，两侧按钮与输入框垂直居中；多行时按钮贴底（和常见聊天软件一致）
const multiLine = ref(false)
function onLineChange(e: { detail: { lineCount: number } }) {
  multiLine.value = e.detail.lineCount > 1
}
const lenWarn = computed(() => inputText.value.length >= 400)
</script>

<template>
  <page-meta :page-style="pageStyle" />
  <view class="chat-page">
    <!-- 消息列表 -->
    <scroll-view
      class="message-list"
      scroll-y
      :scroll-into-view="scrollInto"
      :scroll-with-animation="false"
      :upper-threshold="60"
      @scrolltoupper="loadOlder"
    >
      <view v-if="loading" class="skeleton">
        <view v-for="i in 3" :key="i" class="skel" :class="i % 2 === 0 ? 'skel--right' : 'skel--left'" />
      </view>

      <view v-else-if="loadFailed" class="empty-state">
        <text class="empty-state__text">加载失败</text>
        <view class="retry-btn" @tap="init"><text>重试</text></view>
      </view>

      <template v-else>
        <view v-if="loadingMore" class="more-tip"><text>加载更早的消息...</text></view>
        <view v-else-if="!hasMore && messages.length > 1" class="more-tip"><text>没有更早的消息了</text></view>

        <block v-for="(m, i) in messages" :key="m.message_id">
          <view v-if="showTime(i)" class="time-sep"><text>{{ timeLabel(m.created_at) }}</text></view>

          <view :id="`msg-${m.message_id}`" class="row" :class="m.role === 'student' ? 'row--student' : 'row--ai'">
            <view class="col" :class="{ 'col--student': m.role === 'student' }">
              <!-- 理解突破：成就感卡片 -->
              <view v-if="m.is_aha_trigger" class="aha-card">
                <view class="aha-card__tag"><SvgIcon name="bulb" :size="26" color="#D97706" /><text>突破！</text></view>
                <text class="aha-card__text" user-select>{{ shownText(m) }}</text>
              </view>
              <view v-else class="bubble" :class="m.role === 'student' ? 'bubble--student' : 'bubble--ai'" :style="m.role === 'student' ? '' : hl('assistant-bubble')" @tap="m.message_id === typingId && stopTyping()">
                <image v-if="m.image_url" class="bubble__img" :src="imgSrc(m)" mode="widthFix" @tap.stop="previewImg(m)" />
                <text v-if="m.content || !m.image_url" class="bubble__text" :class="{ 'bubble__text--student': m.role === 'student', 'bubble__text--after-img': !!m.image_url }" user-select>{{ shownText(m) }}</text>
              </view>

              <!-- AI 回复的操作：复制 / 点赞 / 点踩 / 重新生成 -->
              <view v-if="m.role === 'assistant' && m.message_id !== typingId" class="actions">
                <view class="act" @tap="copyMsg(m)"><SvgIcon name="copy" :size="30" color="muted" /></view>
                <block v-if="!m.is_aha_trigger">
                  <view class="act" :class="{ 'act--on': m.rating === 'like' }" @tap="rate(m, 'like')">
                    <SvgIcon name="thumb_up" :size="30" :color="m.rating === 'like' ? 'primary' : 'muted'" />
                  </view>
                  <view class="act" :class="{ 'act--on': m.rating === 'dislike' }" @tap="rate(m, 'dislike')">
                    <SvgIcon name="thumb_down" :size="30" :color="m.rating === 'dislike' ? 'primary' : 'muted'" />
                  </view>
                  <view v-if="m.message_id === lastAiId || m.rating === 'dislike'" class="act act--text" @tap="regenerate(m)">
                    <SvgIcon name="refresh" :size="28" color="muted" />
                    <text class="act__label">{{ regenerating === m.message_id ? '生成中...' : '重新生成' }}</text>
                  </view>
                </block>
              </view>
            </view>
          </view>
        </block>

        <!-- 快捷提问 -->
        <view v-if="showSuggestions" class="suggest">
          <text class="suggest__title">你可以试着问我</text>
          <view v-for="(s, i) in suggestions" :key="i" class="suggest__item" :style="hl('sg-' + i)" @tap="send(s)">
            <text class="suggest__text">{{ s }}</text>
          </view>
        </view>

        <!-- 思考中 -->
        <view v-if="sending" class="row row--ai">
          <view class="bubble bubble--ai thinking" :style="hl('assistant-bubble')"><view class="dot" /><view class="dot" /><view class="dot" /></view>
        </view>
      </template>
      <view id="chat-bottom" class="bottom-anchor" />
    </scroll-view>

    <!-- 沉默模式提示 -->
    <view v-if="silenceVisible" class="silence-bar" @tap="resumeSilence">
      <SvgIcon name="volume_off" :size="28" color="muted" />
      <text class="silence-bar__text">沉默中，AI 不会打扰你（点击恢复引导）</text>
    </view>

    <!-- 输入区：尺寸和位置与训练答题页底部按钮栏一致（上下内边距 24rpx、左右 32rpx、控件高 88rpx）；图片 / 发送按钮在输入框内部两侧 -->
    <view class="input-bar">
      <!-- 已选好的图片：缩略图（上传中有遮罩），可以删除；和问题一起发送 -->
      <view v-if="pendingImage" class="img-preview">
        <image class="img-preview__img" :src="pendingImage.local" mode="aspectFill" />
        <view v-if="uploading" class="img-preview__mask"><view class="spin spin--light" /></view>
        <view v-else class="img-preview__close" @tap="removeImage"><text>×</text></view>
      </view>
      <view class="input-box" :class="{ 'input-box--multi': multiLine }">
        <view class="in-btn" @tap="pickImage">
          <view v-if="uploading" class="spin" />
          <view v-else class="in-btn__icon in-btn__icon--cam"><SvgIcon name="camera" :size="48" color="primary" /></view>
        </view>
        <textarea
          v-model="inputText"
          class="input"
          placeholder="想问的问题写在这里..."
          placeholder-class="input-ph"
          :maxlength="MAX_LEN"
          auto-height
          :show-confirm-bar="false"
          :cursor-spacing="24"
          @linechange="onLineChange"
        />
        <text v-if="lenWarn" class="counter" :class="{ 'counter--max': inputText.length >= MAX_LEN }">{{ inputText.length }}/{{ MAX_LEN }}</text>
        <view class="in-btn in-btn--send" @tap="send()">
          <view v-if="sending" class="spin spin--light" />
          <view v-else class="in-btn__icon in-btn__icon--send"><SvgIcon name="send" :size="32" color="on-primary" /></view>
        </view>
      </view>
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

// ── 消息列表 ──
.message-list { flex: 1; min-height: 0; padding: 0 $space-4; box-sizing: border-box; }
.bottom-anchor { height: 24rpx; }

.skeleton { display: flex; flex-direction: column; gap: $space-3; padding-top: $space-4; }
.skel {
  height: 88rpx; width: 62%; border-radius: $r-lg; background: $bg-muted; animation: shimmer 1.2s ease-in-out infinite;
  &--right { margin-left: auto; }
}
@keyframes shimmer { 0%, 100% { opacity: 0.55; } 50% { opacity: 1; } }

.empty-state { display: flex; flex-direction: column; align-items: center; gap: $space-3; padding-top: 200rpx; }
.empty-state__text { font-size: $font-size-base; color: $text-3; }
.retry-btn { padding: 14rpx 36rpx; border-radius: $r-pill; background: $primary-light; color: $primary; font-size: $font-size-sm; font-weight: 600; }

.more-tip { text-align: center; padding: $space-3 0; font-size: $font-size-xs; color: $text-3; }
.time-sep { text-align: center; padding: $space-3 0 $space-2; font-size: $font-size-xs; color: $text-3; }

.row { display: flex; gap: $space-2; margin-bottom: $space-3; align-items: flex-start;
  &--student { justify-content: flex-end; }
}
.col { display: flex; flex-direction: column; align-items: flex-start; max-width: 92%; min-width: 0;
  &--student { align-items: flex-end; }
}

.bubble {
  padding: 20rpx 24rpx;
  border-radius: 16rpx;   // 四个圆角都是 8px
  word-break: break-all;

  // 助手回复：与「训练方式」的训练类型卡片同款玻璃面板（面板底色 + 描边 + 随机位置的边框高亮），圆角改为 8px
  &--ai {
    @include glass-panel(false);
    background: var(--bubble-bg);   // 云晕随气泡大小等比缩放：长回复和短回复（如开场白）看起来一样
    border: 1rpx solid $border;
    border-radius: 16rpx;
  }
  &--student { background: $cta-gradient; }
  &__text { font-size: $font-size-base; color: $text-1; line-height: 1.65; white-space: pre-wrap; }
  &__text--student { color: $on-primary; }
  &__text--after-img { display: block; margin-top: 12rpx; }
  &__img { display: block; width: 360rpx; max-width: 100%; border-radius: 8rpx; }
}

// 理解突破：成就感卡片
.aha-card {
  padding: 20rpx 24rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.18), rgba(245, 158, 11, 0.08));
  border: 1rpx solid rgba(245, 158, 11, 0.45);

  &__tag { display: flex; align-items: center; gap: 8rpx; margin-bottom: 8rpx; font-size: $font-size-sm; font-weight: 700; color: #D97706; }
  &__text { font-size: $font-size-base; color: $text-1; line-height: 1.65; white-space: pre-wrap; word-break: break-all; }
}

.actions { display: flex; align-items: center; gap: 4rpx; margin-top: 6rpx; }
.act {
  min-width: 64rpx; height: 56rpx; display: flex; align-items: center; justify-content: center; border-radius: $r-pill;
  &--text { padding: 0 16rpx; gap: 6rpx; }
  &__label { font-size: $font-size-xs; color: $text-3; }
  &:active { background: $bg-muted; }
}

// 思考中
.thinking { display: flex; align-items: center; gap: 10rpx; padding: 26rpx 28rpx; }
.dot { width: 14rpx; height: 14rpx; border-radius: 50%; background: $text-3; animation: blink 1.2s infinite ease-in-out;
  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
}
@keyframes blink { 0%, 80%, 100% { opacity: 0.25; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-6rpx); } }

// 快捷提问
.suggest { margin: $space-3 0 0; display: flex; flex-direction: column; gap: 14rpx; align-items: flex-start; }
.suggest__title { font-size: $font-size-xs; color: $text-3; }
.suggest__item {
  @include glass-panel;
  border: 1rpx solid $border;
  padding: 16rpx 24rpx;
  max-width: 100%;
  box-sizing: border-box;
  &:active { background: $primary-light; }
}
.suggest__text { font-size: $font-size-sm; color: $text-1; }

// ── 沉默模式 ──
.silence-bar {
  display: flex; align-items: center; justify-content: center; gap: 10rpx;
  padding: 14rpx $space-4; background: $bg-muted; border-top: 1rpx solid $border;
  &__text { font-size: $font-size-xs; color: $text-2; }
}

// ── 输入区 ──（与训练答题页 .action-bar 同样的内边距：24rpx 32rpx；控件高度 88rpx）
.input-bar {
  padding: $space-3 $space-4;
  padding-bottom: calc(#{$space-3} + env(safe-area-inset-bottom));
  background: $bg-surface;
  border-top: 1rpx solid $border;
}
.img-preview {
  position: relative;
  width: 120rpx; height: 120rpx;
  margin-bottom: $space-2;
  border-radius: 8rpx;
  &__img { width: 100%; height: 100%; border-radius: 8rpx; display: block; background: $bg-muted; }
  &__mask { position: absolute; inset: 0; border-radius: 8rpx; background: rgba(0, 0, 0, 0.45); display: flex; align-items: center; justify-content: center; }
  &__close {
    position: absolute; top: -14rpx; right: -14rpx; width: 40rpx; height: 40rpx; border-radius: 50%;
    background: $text-1; color: $bg-surface; display: flex; align-items: center; justify-content: center;
    font-size: 30rpx; line-height: 1;
  }
}
.input-box {
  position: relative;
  display: flex;
  align-items: center;               // 单行：按钮与文字垂直居中
  &--multi { align-items: flex-end; } // 多行：按钮贴底
  gap: 8rpx;
  min-height: 88rpx;                 // 初始高度 = 训练页底部按钮高度；多行时自动长高
  padding: 12rpx;
  box-sizing: border-box;
  background: $bg-muted;
  border-radius: 44rpx;
}
.in-btn {
  width: 64rpx; height: 64rpx; flex-shrink: 0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  &--send { background: $cta-gradient; box-shadow: $shadow-cta; }
  // 图标装在固定大小、行高为 0 的盒子里：自定义组件外层是 inline-block，行高会把外层撑得比图标高，图标就会偏上，不在按钮正中
  &__icon { display: flex; align-items: center; justify-content: center; line-height: 0; &--cam { width: 48rpx; height: 48rpx; } &--send { width: 32rpx; height: 32rpx; } }
}
.input {
  flex: 1; min-width: 0; min-height: 44rpx; max-height: 200rpx;
  padding: 10rpx 0;                  // 单行时文字与两侧 64rpx 的按钮垂直居中
  font-size: $font-size-base; color: $text-1; line-height: 44rpx;
}
.input-ph { color: $text-3; }
.counter { position: absolute; right: 92rpx; bottom: 2rpx; font-size: 20rpx; color: $text-3; &--max { color: $danger; } }
.spin {
  width: 36rpx; height: 36rpx; border-radius: 50%; border: 5rpx solid $bg-muted; border-top-color: $primary; animation: spin 0.7s linear infinite;
  &--light { border-color: rgba(255, 255, 255, 0.4); border-top-color: #fff; }
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { testApi } from '@/api'
import { PAGES } from '@/constants'
import { formatSeconds } from '@/utils'
import type { CogQuestion } from '@/api/test'

// ── 页面参数（session_id, resume标志） ───────────────────────────────────
const sessionId = ref<number>(0)
const questions = ref<CogQuestion[]>([])
const currentIndex = ref(0)
const answers = ref<Array<string | null>>([]) // 每题的选择答案
const loading = ref(true)
const submittingAnswer = ref(false)
const submittingTest = ref(false)
const questionStartTime = ref(Date.now())

// ── 计时相关 ──────────────────────────────────────────────────────────────
const elapsed = ref(0) // 当前题用时（秒）
let timer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const options = (current as any)?.options || {}
  sessionId.value = parseInt(options.session_id || '0')
  const isResume = options.resume === '1'

  // 从本地存储恢复或初始化题目
  const cached = uni.getStorageSync('mesh_test_session')
  if (cached) {
    try {
      const parsed = JSON.parse(cached)
      if (parsed.questions?.length) {
        questions.value = parsed.questions
        if (isResume) {
          currentIndex.value = parsed.current_index || 0
          answers.value = parsed.answers || new Array(parsed.questions.length).fill(null)
        } else {
          answers.value = new Array(parsed.questions.length).fill(null)
        }
        loading.value = false
        startTimer()
        return
      }
    } catch {
      /* 本地数据损坏，重新获取 */
    }
  }

  // 没有缓存时重新获取（防御）
  try {
    const resp = await testApi.getQuestions()
    questions.value = resp.questions
    sessionId.value = resp.session_id
    answers.value = new Array(resp.questions.length).fill(null)
    uni.setStorageSync('mesh_test_session', JSON.stringify({
      session_id: resp.session_id,
      questions: resp.questions,
      current_index: 0,
      answers: answers.value,
    }))
  } catch {
    uni.showToast({ title: '获取题目失败', icon: 'none' })
  } finally {
    loading.value = false
    startTimer()
  }
})

function startTimer() {
  questionStartTime.value = Date.now()
  elapsed.value = 0
  timer = setInterval(() => { elapsed.value++ }, 1000)
}

function stopTimer() {
  if (timer) { clearInterval(timer); timer = null }
}

const currentQuestion = computed<CogQuestion | null>(() => questions.value[currentIndex.value] ?? null)
const isLast = computed(() => currentIndex.value === questions.value.length - 1)
const answeredCount = computed(() => answers.value.filter((a) => a !== null).length)
const currentAnswer = computed(() => answers.value[currentIndex.value])

// ── 选择选项 ──────────────────────────────────────────────────────────────
function selectOption(key: string) {
  answers.value[currentIndex.value] = key
  // 持久化进度
  const cached = uni.getStorageSync('mesh_test_session')
  if (cached) {
    try {
      const parsed = JSON.parse(cached)
      parsed.answers = answers.value
      parsed.current_index = currentIndex.value
      uni.setStorageSync('mesh_test_session', JSON.stringify(parsed))
    } catch { /* ignore */ }
  }
}

// ── 下一题 ────────────────────────────────────────────────────────────────
async function goNext() {
  if (submittingAnswer.value) return
  const q = currentQuestion.value
  if (!q) return
  const selected = answers.value[currentIndex.value]
  if (!selected) {
    uni.showToast({ title: '请先选择一个选项', icon: 'none' })
    return
  }

  // 提交当前题答案
  submittingAnswer.value = true
  try {
    await testApi.submitAnswer({
      session_id: sessionId.value,
      question_id: q.id,
      question_index: currentIndex.value,
      selected_option: selected,
      time_spent_sec: elapsed.value,
    })
  } catch {
    // 答案提交失败不阻断答题流程，后续可重试
  } finally {
    submittingAnswer.value = false
  }

  if (!isLast.value) {
    currentIndex.value++
    // 更新本地存储
    const cached = uni.getStorageSync('mesh_test_session')
    if (cached) {
      try {
        const parsed = JSON.parse(cached)
        parsed.current_index = currentIndex.value
        uni.setStorageSync('mesh_test_session', JSON.stringify(parsed))
      } catch { /* ignore */ }
    }
    stopTimer()
    startTimer()
  } else {
    confirmSubmit()
  }
}

// ── 确认提交测试 ──────────────────────────────────────────────────────────
function confirmSubmit() {
  const unanswered = answers.value.filter((a) => a === null).length
  const msg = unanswered > 0
    ? `还有 ${unanswered} 道题未作答，确认提交？`
    : '确认提交所有题目完成测试？'
  uni.showModal({
    title: '提交测试',
    content: msg,
    confirmText: '确认提交',
    success: async (res) => {
      if (res.confirm) await completeTest()
    },
  })
}

// ── 提交测试 ──────────────────────────────────────────────────────────────
async function completeTest() {
  if (submittingTest.value) return
  submittingTest.value = true
  stopTimer()
  try {
    const profile = await testApi.completeTest(sessionId.value)
    // 清除本地缓存
    uni.removeStorageSync('mesh_test_session')
    uni.redirectTo({
      url: `${PAGES.TEST_RESULT}?profile_id=${profile.profile_id}`,
    })
  } catch {
    uni.showToast({ title: '提交失败，请重试', icon: 'none' })
    submittingTest.value = false
  }
}

onUnmounted(() => {
  stopTimer()
})
</script>

<template>
  <view class="questions-page">
    <!-- ── 自定义导航栏 ──────────────────────────────────────── -->
    <view class="nav-bar">
      <view class="nav-back" @tap="uni.navigateBack()">
        <text class="nav-back__icon">‹</text>
      </view>
      <view class="nav-center">
        <text class="nav-progress-text">{{ currentIndex + 1 }} / {{ questions.length }}</text>
      </view>
      <view class="nav-timer">
        <text class="nav-timer__text">{{ formatSeconds(elapsed) }}</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <view class="loading-spinner" />
      <text class="loading-text">正在加载题目...</text>
    </view>

    <template v-else-if="currentQuestion">
      <!-- ── 进度点 ─────────────────────────────────────────────── -->
      <scroll-view class="progress-scroll" scroll-x>
        <view class="progress-dots">
          <view
            v-for="(_, i) in questions"
            :key="i"
            class="pdot"
            :class="{
              'pdot--answered': answers[i] !== null && i !== currentIndex,
              'pdot--current': i === currentIndex,
            }"
            @tap="currentIndex = i"
          />
        </view>
      </scroll-view>

      <!-- ── 题目卡片 ─────────────────────────────────────────────── -->
      <view class="question-wrap">
        <!-- 参考用时 -->
        <view class="time-hint">
          <text class="time-hint__icon">⏱</text>
          <text class="time-hint__text">参考用时：{{ currentQuestion.reference_time_sec }}秒</text>
          <text class="time-hint__elapsed">已用：{{ formatSeconds(elapsed) }}</text>
        </view>

        <text class="question-stem">{{ currentQuestion.stem }}</text>

        <!-- 题目图片 -->
        <image
          v-if="currentQuestion.image_url"
          class="question-image"
          :src="currentQuestion.image_url"
          mode="widthFix"
        />
      </view>

      <!-- ── 选项卡片 ─────────────────────────────────────────────── -->
      <view class="options-list">
        <view
          v-for="opt in currentQuestion.answers"
          :key="opt.key"
          class="option-card"
          :class="{
            'option-card--selected': currentAnswer === opt.key,
          }"
          @tap="selectOption(opt.key)"
        >
          <view class="option-key-badge" :class="{ 'option-key-badge--selected': currentAnswer === opt.key }">
            <text class="option-key-text">{{ opt.key }}</text>
          </view>
          <text class="option-text">{{ opt.text }}</text>
          <view v-if="currentAnswer === opt.key" class="option-check">
            <text class="option-check__icon">✓</text>
          </view>
        </view>
      </view>

      <!-- ── 底部操作栏 ──────────────────────────────────────────── -->
      <view class="action-bar">
        <!-- 已答题数 -->
        <text class="answered-count">已答 {{ answeredCount }}/{{ questions.length }}</text>

        <button
          class="next-btn"
          :class="{ 'next-btn--disabled': !currentAnswer || submittingAnswer }"
          :disabled="!currentAnswer || submittingAnswer"
          @tap="goNext"
        >
          <view v-if="submittingAnswer" class="spinner" />
          <text class="next-btn__text">{{ isLast ? '提交测试' : '下一题 ›' }}</text>
        </button>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.questions-page {
  min-height: 100vh;
  background: $bg-page;
  padding-bottom: 180rpx;
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
}

.nav-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &__icon {
    font-size: 48rpx;
    color: $text-1;
  }
}

.nav-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.nav-progress-text {
  font-size: $font-size-lg;
  color: $text-1;
  font-weight: 700;
}

.nav-timer {
  width: 100rpx;
  text-align: right;
}

.nav-timer__text {
  font-size: $font-size-sm;
  color: $text-3;
  font-variant-numeric: tabular-nums;
}

// 加载状态
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 80vh;
  gap: $space-4;
}

.loading-spinner {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  border: 6rpx solid $bg-muted;
  border-top-color: $primary;
  animation: spin 0.7s linear infinite;
}

.loading-text {
  font-size: $font-size-base;
  color: $text-3;
}

// 进度点滚动
.progress-scroll {
  padding: $space-3 $space-4;
}

.progress-dots {
  display: flex;
  gap: 10rpx;
  min-width: max-content;
}

.pdot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background: $bg-muted;
  border: 2rpx solid $border;
  flex-shrink: 0;
  transition: $transition-fast;

  &--answered {
    background: $success;
    border-color: $success;
  }

  &--current {
    background: $primary;
    border-color: $primary;
    width: 36rpx;
    border-radius: $r-pill;
  }
}

// 题目区
.question-wrap {
  margin: 0 $space-4 $space-3;
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  box-shadow: $shadow-sm;
}

.time-hint {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-3;
  padding: $space-2 $space-3;
  background: $primary-light;
  border-radius: $r-md;
}

.time-hint__icon {
  font-size: 28rpx;
}

.time-hint__text {
  font-size: $font-size-xs;
  color: $primary;
  flex: 1;
}

.time-hint__elapsed {
  font-size: $font-size-xs;
  color: $text-3;
}

.question-stem {
  font-size: $font-size-lg;
  color: $text-1;
  line-height: 1.7;
  display: block;
}

.question-image {
  width: 100%;
  margin-top: $space-3;
  border-radius: $r-md;
}

// 选项列表
.options-list {
  margin: 0 $space-4;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.option-card {
  background: $bg-surface;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  display: flex;
  align-items: center;
  gap: $space-3;
  box-shadow: $shadow-sm;
  border: 2rpx solid transparent;
  transition: $transition-base;

  &--selected {
    border-color: $primary;
    background: $primary-light;
    box-shadow: $shadow-md;
  }

  &:active {
    transform: scale(0.99);
  }
}

.option-key-badge {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  background: $bg-muted;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: $transition-fast;

  &--selected {
    background: $primary;
  }
}

.option-key-text {
  font-size: $font-size-base;
  color: $text-2;
  font-weight: 700;

  .option-key-badge--selected & {
    color: #fff;
  }
}

.option-text {
  flex: 1;
  font-size: $font-size-base;
  color: $text-1;
  line-height: 1.5;
}

.option-check {
  flex-shrink: 0;

  &__icon {
    font-size: 32rpx;
    color: $primary;
    font-weight: 700;
  }
}

// 底部操作栏
.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: $space-3;
  padding: $space-3 $space-4;
  padding-bottom: calc($space-3 + env(safe-area-inset-bottom));
  background: $bg-surface;
  box-shadow: 0 -4rpx 24rpx rgba(0,0,0,0.06);
}

.answered-count {
  font-size: $font-size-sm;
  color: $text-3;
  flex-shrink: 0;
}

.next-btn {
  flex: 1;
  height: 88rpx;
  background: $primary;
  border-radius: $r-pill;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;

  &::after { border: none; }

  &--disabled {
    background: $bg-muted;
  }

  &__text {
    font-size: $font-size-lg;
    color: #fff;
    font-weight: 700;

    .next-btn--disabled & { color: $text-3; }
  }
}

.spinner {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

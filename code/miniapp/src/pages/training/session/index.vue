<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTrainingStore } from '@/store'
import { trainingApi } from '@/api'
import { useRagPoller } from '@/hooks/useRagPoller'
import { FIVE_POWER_LABELS, FIVE_POWER_COLORS, PAGES } from '@/constants'
import { formatSeconds } from '@/utils'

const trainingStore = useTrainingStore()
const { ragContent, staticSolution, status: ragStatus, canRetry, startPolling, retry, stop: stopRag } = useRagPoller()

// ── 当前题目状态 ───────────────────────────────────────────────────────────
const question = computed(() => trainingStore.currentQuestion())
const currentIndex = computed(() => trainingStore.currentIndex)
const totalQuestions = computed(() => trainingStore.questions.length)
const isLast = computed(() => trainingStore.isLastQuestion())

// ── 答题状态 ───────────────────────────────────────────────────────────────
const studentAnswer = ref('')
const submitting = ref(false)
const submitted = ref(false)
const isCorrect = ref<boolean | null>(null)
const answerRecordId = ref<number | null>(null)
const wrongCount = ref(0) // 累计答错次数（用于触发 AI 主动介入）
const showAiBar = ref(false)

// ── 计时 ──────────────────────────────────────────────────────────────────
const elapsed = ref(0) // 当前题用时（秒）
let timer: ReturnType<typeof setInterval> | null = null

function startTimer() {
  elapsed.value = 0
  timer = setInterval(() => { elapsed.value++ }, 1000)
}

function stopTimer() {
  if (timer) { clearInterval(timer); timer = null }
}

// ── 提示功能 ──────────────────────────────────────────────────────────────
const hintsUsed = ref(0)
const hintContent = ref('')
const showHint = ref(false)

function useHint() {
  hintsUsed.value++
  // 简单提示文本（实际应由后端提供）
  hintContent.value = `提示 ${hintsUsed.value}：请仔细审题，注意题目中的关键条件。`
  showHint.value = true
}

// ── 提交答案 ──────────────────────────────────────────────────────────────
async function submitAnswer() {
  if (submitting.value || !question.value || !studentAnswer.value.trim()) return
  submitting.value = true
  stopTimer()

  try {
    const resp = await trainingApi.submitAnswer({
      session_id: trainingStore.sessionId!,
      question_id: question.value.question_id,
      question_index: question.value.question_index,
      student_answer: studentAnswer.value.trim(),
      time_spent_sec: elapsed.value,
      hint_level_used: hintsUsed.value > 0 ? hintsUsed.value : undefined,
    })

    submitted.value = true
    isCorrect.value = resp.is_correct
    trainingStore.recordAnswer(question.value.question_index, studentAnswer.value.trim(), resp.is_correct)

    if (!resp.is_correct) {
      wrongCount.value++
      // 答错后立刻轮询 RAG 生成
      if (resp.answer_record_id) {
        answerRecordId.value = resp.answer_record_id
        startPolling(resp.answer_record_id)
      }
      // 连续答错 ≥2 次，显示 AI 主动介入提示
      if (wrongCount.value >= 2) {
        showAiBar.value = true
      }
    }
  } catch {
    uni.showToast({ title: '提交失败，请重试', icon: 'none' })
    startTimer() // 恢复计时
  } finally {
    submitting.value = false
  }
}

// ── 下一题 / 完成 ─────────────────────────────────────────────────────────
async function nextOrComplete() {
  stopRag()
  if (isLast.value) {
    // 最后一题 → 完成会话
    try {
      const summary = await trainingApi.completeSession(trainingStore.sessionId!)
      uni.showModal({
        title: '训练完成！',
        content: `共 ${summary.summary.total_questions} 题，正确 ${summary.summary.correct_count} 题，正确率 ${Math.round(summary.summary.accuracy_rate * 100)}%`,
        showCancel: false,
        success: () => {
          trainingStore.reset()
          uni.switchTab({ url: PAGES.TRAINING_HOME })
        },
      })
    } catch {
      trainingStore.reset()
      uni.switchTab({ url: PAGES.TRAINING_HOME })
    }
  } else {
    // 切换下一题，重置答题状态
    trainingStore.nextQuestion()
    resetQuestion()
  }
}

function resetQuestion() {
  studentAnswer.value = ''
  submitted.value = false
  isCorrect.value = null
  answerRecordId.value = null
  hintsUsed.value = 0
  hintContent.value = ''
  showHint.value = false
  ragContent.value = null
  staticSolution.value = null
  ragStatus.value = 'idle'
  startTimer()
}

function goToAssistant() {
  showAiBar.value = false
  uni.navigateTo({ url: PAGES.ASSISTANT_CHAT })
}

// ── 退出确认弹窗 ──────────────────────────────────────────────────────────
const showExitDialog = ref(false)
const savingInterrupt = ref(false)

async function handleExit() {
  showExitDialog.value = true
}

async function confirmExit() {
  if (savingInterrupt.value) return
  savingInterrupt.value = true
  stopTimer()
  stopRag()

  try {
    await trainingApi.saveInterrupt({
      session_id: trainingStore.sessionId!,
      subject_code: trainingStore.subjectCode!,
      training_dimension: trainingStore.dimension!,
      scope_info: trainingStore.scopeInfo,
      scope_label: trainingStore.scopeLabel,
      questions_snapshot: trainingStore.questions,
      answers_snapshot: trainingStore.getAnswersSnapshot(),
      current_question_index: trainingStore.currentIndex,
    })
  } catch {
    // 保存失败不阻断退出
  } finally {
    savingInterrupt.value = false
  }

  showExitDialog.value = false
  trainingStore.reset()
  uni.navigateBack()
}

function cancelExit() {
  showExitDialog.value = false
  if (!submitted.value) startTimer()
}

// ── 答题卡面板 ────────────────────────────────────────────────────────────
const showAnswerCard = ref(false)

function openAnswerCard() {
  showAnswerCard.value = true
}

function closeAnswerCard() {
  showAnswerCard.value = false
}

function jumpToQuestion(index: number) {
  closeAnswerCard()
  trainingStore.jumpToQuestion(index)
  const answered = trainingStore.isAnswered(index)
  if (answered) {
    const snap = trainingStore.answers[index]
    studentAnswer.value = snap.student_answer
    submitted.value = true
    isCorrect.value = snap.is_correct
    ragContent.value = null
    staticSolution.value = null
    ragStatus.value = 'idle'
    stopTimer()
  } else {
    resetQuestion()
  }
}

onMounted(() => {
  startTimer()
})

onUnmounted(() => {
  stopTimer()
  stopRag()
})
</script>

<template>
  <view class="session-page">
    <!-- ── 自定义导航栏 ──────────────────────────────────────── -->
    <view class="nav-bar">
      <!-- 退出按钮（左侧） -->
      <button class="exit-btn" @tap="handleExit">
        <text class="exit-btn__text">✕ 退出</text>
      </button>
      <!-- 进度点（中间） -->
      <view class="progress-dots">
        <view
          v-for="(q, i) in trainingStore.questions"
          :key="i"
          class="dot"
          :class="{
            'dot--done': trainingStore.isAnswered(i),
            'dot--current': i === currentIndex,
          }"
        />
      </view>
      <!-- 答题卡按钮（右侧） -->
      <view class="card-btn" @tap="openAnswerCard">
        <text class="card-btn__text">答题卡</text>
      </view>
    </view>

    <!-- 无题目（防御性空态） -->
    <view v-if="!question" class="empty-state">
      <text class="empty-text">暂无训练题目</text>
    </view>

    <template v-else>
      <!-- ── 借强补弱提示横幅（仅首题且有 tips 时展示） ──────── -->
      <view v-if="currentIndex === 0 && trainingStore.tipsHint" class="tips-banner">
        <text class="tips-banner__icon">✨</text>
        <text class="tips-banner__text">{{ trainingStore.tipsHint }}</text>
      </view>

      <!-- ── 题目元信息 ────────────────────────────────────────── -->
      <view class="question-meta">
        <view
          class="power-badge"
          :style="{ background: FIVE_POWER_COLORS[question.power_type as keyof typeof FIVE_POWER_COLORS] + '20', color: FIVE_POWER_COLORS[question.power_type as keyof typeof FIVE_POWER_COLORS] }"
        >
          <text class="power-badge__text">{{ FIVE_POWER_LABELS[question.power_type as keyof typeof FIVE_POWER_LABELS] || question.power_type }}</text>
        </view>
        <text class="question-index">{{ currentIndex + 1 }}/{{ totalQuestions }}</text>
      </view>

      <!-- ── 题目正文 ────────────────────────────────────────────── -->
      <view class="question-card">
        <text class="question-stem">{{ question.stem }}</text>
        <image
          v-if="question.image_url"
          class="question-image"
          :src="question.image_url"
          mode="widthFix"
        />
      </view>

      <!-- ── 答题区域 ───────────────────────────────────────────── -->
      <view class="answer-area" :class="{ 'answer-area--submitted': submitted }">
        <textarea
          v-if="!submitted"
          v-model="studentAnswer"
          class="answer-textarea"
          placeholder="在此输入你的解题过程和答案..."
          placeholder-class="textarea-placeholder"
          :maxlength="2000"
          auto-height
        />
        <view v-else class="student-answer-display">
          <text class="student-answer-label">你的答案</text>
          <text class="student-answer-text">{{ studentAnswer }}</text>
        </view>
      </view>

      <!-- ── 提示内容 ────────────────────────────────────────────── -->
      <view v-if="showHint" class="hint-card">
        <text class="hint-icon">💡</text>
        <text class="hint-text">{{ hintContent }}</text>
      </view>

      <!-- ── 答题结果反馈 ─────────────────────────────────────────── -->
      <view v-if="submitted" class="result-feedback" :class="isCorrect ? 'result-feedback--correct' : 'result-feedback--wrong'">
        <text class="result-icon">{{ isCorrect ? '🎉' : '❌' }}</text>
        <text class="result-text">{{ isCorrect ? '回答正确！继续保持！' : '答案有误，查看AI解析' }}</text>
      </view>

      <!-- ── RAG 解析卡（答错后） ────────────────────────────────── -->
      <view v-if="submitted && !isCorrect" class="rag-section">
        <!-- 加载骨架屏 -->
        <view v-if="ragStatus === 'pending'" class="rag-skeleton">
          <view class="rag-skeleton__header">
            <text class="rag-skeleton__title">AI 正在生成解析...</text>
          </view>
          <view class="skel-lines">
            <view v-for="i in 4" :key="i" class="skel-line" :style="{ width: `${85 - i * 8}%` }" />
          </view>
        </view>

        <!-- RAG 内容 -->
        <view v-else-if="ragStatus === 'completed' && ragContent" class="rag-card">
          <view class="rag-card__header">
            <text class="rag-icon">🤖</text>
            <text class="rag-card__title">AI 个性化解析</text>
          </view>
          <text class="rag-card__content">{{ ragContent }}</text>
        </view>

        <!-- 降级：静态解析 -->
        <view v-else-if="ragStatus === 'degraded'" class="rag-card rag-card--static">
          <view class="rag-card__header">
            <text class="rag-icon">📖</text>
            <text class="rag-card__title">参考解析</text>
          </view>
          <text class="rag-card__content">{{ staticSolution || '暂无解析' }}</text>
          <button v-if="canRetry" class="retry-btn" @tap="retry(answerRecordId!)">重新生成 AI 解析</button>
        </view>
      </view>

      <!-- ── 底部操作栏 ──────────────────────────────────────────── -->
      <view class="action-bar">
        <!-- 未提交状态 -->
        <template v-if="!submitted">
          <button class="hint-btn" @tap="useHint">
            <text class="hint-btn__icon">💡</text>
            <text class="hint-btn__text">提示{{ hintsUsed > 0 ? `(${hintsUsed})` : '' }}</text>
          </button>
          <button
            class="submit-btn"
            :class="{ 'submit-btn--disabled': !studentAnswer.trim() || submitting }"
            :disabled="!studentAnswer.trim() || submitting"
            @tap="submitAnswer"
          >
            <view v-if="submitting" class="spinner" />
            <text class="submit-btn__text">{{ submitting ? '提交中...' : '提交答案' }}</text>
          </button>
        </template>

        <!-- 已提交状态 -->
        <template v-else>
          <button class="next-btn" @tap="nextOrComplete">
            <text class="next-btn__text">{{ isLast ? '完成训练' : '下一题 ›' }}</text>
          </button>
        </template>
      </view>
    </template>

    <!-- ── AI 主动介入浮动条（连续错≥2次触发） ──────────────── -->
    <view v-if="showAiBar" class="ai-bar">
      <text class="ai-bar__icon">🤖</text>
      <text class="ai-bar__text">遇到困难了？来和 AI 助教聊聊吧</text>
      <button class="ai-bar__btn" @tap="goToAssistant">去聊聊</button>
      <text class="ai-bar__close" @tap="showAiBar = false">✕</text>
    </view>

    <!-- 退出确认弹窗 -->
    <view v-if="showExitDialog" class="dialog-mask">
      <view class="dialog">
        <text class="dialog__title">确认退出训练？</text>
        <text class="dialog__desc">当前训练进度将自动保存，下次可继续</text>
        <view class="dialog__btns">
          <button class="dialog-btn dialog-btn--cancel" @tap="cancelExit">继续训练</button>
          <button class="dialog-btn dialog-btn--confirm" :disabled="savingInterrupt" @tap="confirmExit">
            {{ savingInterrupt ? '保存中...' : '退出并保存' }}
          </button>
        </view>
      </view>
    </view>

    <!-- 答题卡浮层 -->
    <view v-if="showAnswerCard" class="card-mask" @tap.self="closeAnswerCard">
      <view class="answer-card">
        <view class="answer-card__header">
          <text class="answer-card__title">答题卡</text>
          <text class="answer-card__sub">{{ trainingStore.scopeLabel || trainingStore.dimension }}</text>
          <text class="answer-card__close" @tap="closeAnswerCard">×</text>
        </view>
        <text class="answer-card__stat">
          {{ Object.keys(trainingStore.answers).length }}/{{ totalQuestions }} 题已完成
        </text>
        <view class="card-grid">
          <view
            v-for="(q, i) in trainingStore.questions"
            :key="i"
            class="card-item"
            :class="{
              'card-item--done': trainingStore.isAnswered(i),
              'card-item--current': i === currentIndex,
            }"
            @tap="jumpToQuestion(i)"
          >
            <text class="card-item__num">{{ i + 1 }}</text>
            <text v-if="trainingStore.isAnswered(i)" class="card-item__check">✓</text>
          </view>
        </view>
        <!-- 图例 -->
        <view class="card-legend">
          <view class="legend-item">
            <view class="legend-dot legend-dot--done" />
            <text class="legend-text">已答（只读）</text>
          </view>
          <view class="legend-item">
            <view class="legend-dot legend-dot--current" />
            <text class="legend-text">当前题</text>
          </view>
          <view class="legend-item">
            <view class="legend-dot" />
            <text class="legend-text">未答</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>

.session-page {
  min-height: 100vh;
  background: $bg-page;
  display: flex;
  flex-direction: column;
  padding-bottom: 180rpx;
}

// ── 导航栏 ────────────────────────────────────────────────────────────────
.nav-bar {
  display: flex;
  align-items: center;
  height: 100rpx;
  padding: 0 $space-4;
  background: $bg-surface;
  box-shadow: $shadow-sm;
  padding-top: env(safe-area-inset-top);
}

.progress-dots {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  flex-wrap: wrap;
}

.dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: $bg-muted;
  border: 2rpx solid $border;
  transition: $transition-fast;

  &--done {
    background: $success;
    border-color: $success;
  }

  &--current {
    background: $primary;
    border-color: $primary;
    width: 28rpx;
    border-radius: $r-pill;
  }
}

.timer {
  width: 100rpx;
  text-align: right;

  &__text {
    font-size: $font-size-sm;
    color: $text-2;
    font-variant-numeric: tabular-nums;
  }
}

// ── 导航栏按钮 ────────────────────────────────────────────────────────────
.exit-btn {
  flex-shrink: 0;
  height: 64rpx;
  padding: 0 $space-3;
  background: transparent;
  border: 2rpx solid $border;
  border-radius: $r-pill;
  display: flex;
  align-items: center;

  &::after { border: none; }

  &__text {
    font-size: $font-size-xs;
    color: $text-2;
  }
}

.card-btn {
  flex-shrink: 0;
  width: 100rpx;
  text-align: right;

  &__text {
    font-size: $font-size-xs;
    color: $primary;
    font-weight: 600;
  }
}

// ── 空态 ──────────────────────────────────────────────────────────────────
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-text {
  font-size: $font-size-base;
  color: $text-3;
}

// ── 题目元信息 ────────────────────────────────────────────────────────────
.question-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $space-4 $space-4 0;
}

.power-badge {
  padding: 6rpx 20rpx;
  border-radius: $r-pill;

  &__text {
    font-size: $font-size-xs;
    font-weight: 600;
  }
}

.question-index {
  font-size: $font-size-sm;
  color: $text-3;
}

// ── 题目卡 ────────────────────────────────────────────────────────────────
.question-card {
  margin: $space-3 $space-4;
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  box-shadow: $shadow-sm;
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

// ── 答题区 ────────────────────────────────────────────────────────────────
.answer-area {
  margin: 0 $space-4 $space-3;
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-3;
  box-shadow: $shadow-sm;
  border: 2rpx solid transparent;
  transition: $transition-base;

  &:focus-within {
    border-color: $primary;
  }

  &--submitted {
    border-color: transparent;
    background: $bg-muted;
  }
}

.answer-textarea {
  width: 100%;
  min-height: 200rpx;
  font-size: $font-size-base;
  color: $text-1;
  line-height: 1.7;
}

.student-answer-label {
  display: block;
  font-size: $font-size-xs;
  color: $text-3;
  margin-bottom: $space-1;
}

.student-answer-text {
  font-size: $font-size-base;
  color: $text-2;
  line-height: 1.6;
}

// ── 提示卡 ────────────────────────────────────────────────────────────────
.hint-card {
  margin: 0 $space-4 $space-3;
  background: $warning-light;
  border-radius: $r-lg;
  padding: $space-3;
  display: flex;
  gap: $space-2;
  align-items: flex-start;
}

.hint-icon {
  font-size: 32rpx;
  flex-shrink: 0;
}

.hint-text {
  font-size: $font-size-sm;
  color: $text-2;
  line-height: 1.6;
}

// ── 结果反馈 ─────────────────────────────────────────────────────────────
.result-feedback {
  margin: 0 $space-4 $space-3;
  border-radius: $r-lg;
  padding: $space-3;
  display: flex;
  align-items: center;
  gap: $space-2;

  &--correct {
    background: $success-light;
  }

  &--wrong {
    background: $danger-light;
  }
}

.result-icon {
  font-size: 36rpx;
}

.result-text {
  font-size: $font-size-base;
  color: $text-1;
  font-weight: 600;
}

// ── RAG 解析区 ────────────────────────────────────────────────────────────
.rag-section {
  margin: 0 $space-4 $space-3;
}

.rag-skeleton {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  box-shadow: $shadow-sm;
}

.rag-skeleton__header {
  margin-bottom: $space-3;
}

.rag-skeleton__title {
  font-size: $font-size-sm;
  color: $text-3;
}

.skel-lines {
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

.rag-card {
  background: linear-gradient(135deg, #f0f2ff 0%, #fdf2f8 100%);
  border-radius: $r-xl;
  padding: $space-4;
  border: 2rpx solid $border;

  &--static {
    background: $bg-surface;
    border-color: $border;
  }

  &__header {
    display: flex;
    align-items: center;
    gap: $space-2;
    margin-bottom: $space-3;
  }

  &__title {
    font-size: $font-size-base;
    color: $text-1;
    font-weight: 700;
  }

  &__content {
    font-size: $font-size-base;
    color: $text-2;
    line-height: 1.8;
  }
}

.rag-icon {
  font-size: 36rpx;
}

.retry-btn {
  margin-top: $space-3;
  height: 72rpx;
  background: $primary-light;
  border: 2rpx solid $primary;
  border-radius: $r-pill;
  font-size: $font-size-sm;
  color: $primary;
  font-weight: 600;

  &::after { border: none; }
}

// ── 底部操作栏 ───────────────────────────────────────────────────────────
.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: $space-3 $space-4;
  padding-bottom: calc($space-3 + env(safe-area-inset-bottom));
  background: $bg-surface;
  box-shadow: 0 -4rpx 24rpx rgba(0,0,0,0.06);
  display: flex;
  gap: $space-3;
  align-items: center;
}

.hint-btn {
  flex-shrink: 0;
  height: 88rpx;
  padding: 0 $space-3;
  background: $warning-light;
  border: 2rpx solid $warning;
  border-radius: $r-lg;
  display: flex;
  align-items: center;
  gap: $space-1;

  &::after { border: none; }

  &__icon { font-size: 32rpx; }
  &__text { font-size: $font-size-sm; color: $warning; font-weight: 600; }
}

.submit-btn {
  flex: 1;
  height: 88rpx;
  background: $primary;
  border-radius: $r-lg;
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

    .submit-btn--disabled & { color: $text-3; }
  }
}

.next-btn {
  flex: 1;
  height: 88rpx;
  background: $pink;
  border-radius: $r-lg;
  border: none;

  &::after { border: none; }

  &__text {
    font-size: $font-size-lg;
    color: #fff;
    font-weight: 700;
  }
}

// ── AI 主动介入浮动条 ─────────────────────────────────────────────────────
.ai-bar {
  position: fixed;
  bottom: 180rpx;
  left: $space-4;
  right: $space-4;
  background: linear-gradient(135deg, $primary 0%, #7C3AED 100%);
  border-radius: $r-xl;
  padding: $space-3 $space-4;
  display: flex;
  align-items: center;
  gap: $space-2;
  box-shadow: $shadow-md;
  z-index: 100;
  animation: slideUp 0.3s ease;

  &__icon { font-size: 36rpx; flex-shrink: 0; }
  &__text { flex: 1; font-size: $font-size-sm; color: #fff; }
  &__btn {
    flex-shrink: 0;
    height: 56rpx;
    padding: 0 $space-3;
    background: rgba(255,255,255,0.2);
    border: 2rpx solid rgba(255,255,255,0.4);
    border-radius: $r-pill;
    font-size: $font-size-xs;
    color: #fff;
    font-weight: 600;

    &::after { border: none; }
  }

  &__close {
    font-size: 28rpx;
    color: rgba(255,255,255,0.7);
    padding: $space-1;
    flex-shrink: 0;
  }
}

@keyframes slideUp {
  from { transform: translateY(20rpx); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
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

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

// ── 借强补弱提示横幅 ──────────────────────────────────────────────────────
.tips-banner {
  margin: $space-3 $space-4 0;
  padding: $space-3 $space-4;
  background: linear-gradient(135deg, $primary-light 0%, rgba(244, 63, 126, 0.06) 100%);
  border-radius: $r-lg;
  border-left: 6rpx solid $primary;
  display: flex;
  align-items: flex-start;
  gap: $space-2;

  &__icon {
    font-size: 28rpx;
    flex-shrink: 0;
    margin-top: 4rpx;
  }

  &__text {
    font-size: $font-size-sm;
    color: $primary;
    line-height: 1.7;
    flex: 1;
  }
}

// ── 退出确认弹窗 ──────────────────────────────────────────────────────────
.dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: $space-6;
}

.dialog {
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
    font-size: $font-size-sm;
    color: $text-3;
    text-align: center;
  }

  &__btns {
    display: flex;
    gap: $space-3;
    margin-top: $space-2;
  }
}

.dialog-btn {
  flex: 1;
  height: 88rpx;
  border-radius: $r-lg;
  font-size: $font-size-base;
  font-weight: 600;
  border: none;

  &::after { border: none; }

  &--cancel {
    background: $bg-muted;
    color: $text-2;
  }

  &--confirm {
    background: $pink;
    color: #fff;

    &[disabled] {
      opacity: 0.7;
    }
  }
}

// ── 答题卡面板 ────────────────────────────────────────────────────────────
.card-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: flex-end;
  z-index: 200;
}

.answer-card {
  width: 100%;
  background: $bg-surface;
  border-radius: $r-xl $r-xl 0 0;
  padding: $space-4;
  padding-bottom: calc($space-4 + env(safe-area-inset-bottom));
  max-height: 65vh;
  display: flex;
  flex-direction: column;
  gap: $space-3;

  &__header {
    display: flex;
    align-items: center;
    gap: $space-2;
  }

  &__title {
    font-size: $font-size-lg;
    color: $text-1;
    font-weight: 700;
    flex: 1;
  }

  &__sub {
    font-size: $font-size-xs;
    color: $text-3;
  }

  &__close {
    font-size: 44rpx;
    color: $text-3;
    padding: 0 $space-1;
  }

  &__stat {
    font-size: $font-size-sm;
    color: $text-2;
  }
}

.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: $space-2;
}

.card-item {
  width: 100rpx;
  height: 100rpx;
  border-radius: $r-md;
  border: 2rpx solid $border;
  background: $bg-surface;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  position: relative;
  transition: $transition-fast;

  &--done {
    background: $success-light;
    border-color: $success;
  }

  &--current {
    border-color: $primary;
    border-width: 4rpx;
  }

  &__num {
    font-size: $font-size-sm;
    color: $text-1;
    font-weight: 600;
  }

  &__check {
    font-size: $font-size-xs;
    color: $success;
  }
}

.card-legend {
  display: flex;
  gap: $space-4;
  justify-content: center;
  padding-top: $space-2;
  border-top: 1rpx solid $border;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: $space-1;
}

.legend-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: $r-sm;
  border: 2rpx solid $border;
  background: $bg-surface;

  &--done {
    background: $success-light;
    border-color: $success;
  }

  &--current {
    border-color: $primary;
    border-width: 3rpx;
  }
}

.legend-text {
  font-size: $font-size-xs;
  color: $text-3;
}
</style>

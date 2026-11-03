<script setup lang="ts">
import { useTheme } from '@/hooks/useTheme'
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { onReady } from '@dcloudio/uni-app'
import { useTrainingStore } from '@/store'
import { trainingApi, favoriteApi } from '@/api'
import { PAGES, QUESTION_TYPE_META } from '@/constants'
import { formatSeconds } from '@/utils'
import SvgIcon from '@/components/SvgIcon.vue'
import AnswerPanel from '@/components/training/AnswerPanel.vue'
import { answerMode, answerText, buildSubmit, emptyAnswer, restoreAnswer, type AnswerState } from '@/utils/answer'


const { pageStyle, hl, typeColors, isDark } = useTheme()
const trainingStore = useTrainingStore()

// ── 当前题目状态 ───────────────────────────────────────────────────────────
const question = computed(() => trainingStore.currentQuestion())
const currentIndex = computed(() => trainingStore.currentIndex)
const totalQuestions = computed(() => trainingStore.questions.length)
const isLast = computed(() => trainingStore.isLastQuestion())

// 作答结果（对 / 错）：答题框变色 + 右上角图标，不再单独弹出提示框
// 底部分段按钮中间一段（智能解答）的文字 / 图标色：与「选中态」一致，暗色白、亮色深蓝，在渐变中段上清晰可读
const midBtnColor = computed(() => (isDark.value ? '#FFFFFF' : '#2F5FD6'))

const resultColor = computed(() => (isCorrect.value ? (isDark.value ? '#4ADE80' : '#10B981') : (isDark.value ? '#F87171' : '#EF4444')))

// 题目类型（标签用）
const typeKey = computed(() => String(question.value?.question_type || '').toUpperCase())
const typeMeta = computed(() => QUESTION_TYPE_META[typeKey.value] ?? null)
const typeColor = computed(() => typeColors.value[typeKey.value] ?? '#94A3B8')

// ── 答题状态 ───────────────────────────────────────────────────────────────
// 作答状态按题型组织（见 utils/answer.ts）：单选 / 多选 / 判断用 selected，填空用 blanks，应用题用 text + final，其它用 text
const answerState = ref<AnswerState>(emptyAnswer(question.value?.blank_count ?? 0))
const mode = computed(() => answerMode(question.value))
const answerPanelRef = ref<InstanceType<typeof AnswerPanel> | null>(null)

// 标题行右侧的一句话格式提示（与后端判题规则一致：见接口设计说明书 §5.2）
const answerTip = computed(() => {
  const qType = String(question.value?.question_type || '').toUpperCase()
  switch (mode.value) {
    case 'single': return '选择一个答案'
    case 'multi': return '可选多项，选出所有正确答案'
    case 'tf': return '判断对错'
    case 'fill': {
      const n = question.value?.blank_count ?? 0
      return n > 1 ? `共 ${n} 个空，请依次作答` : '填写答案'
    }
    case 'application': return '写出过程，并填写最终答案'
    default:
      if (qType === 'SINGLE_CHOICE') return '只填一个选项字母'
      if (qType === 'MULTIPLE_CHOICE') return '填所有正确选项字母'
      return '写出思路和过程，解析更有针对性'
  }
})

// 点到答题子模块（标题行 / 留白）时自动聚焦第一个输入框；选择类题型没有输入框，不触发。
// 点在输入框、选项上不走这里（组件内部已处理，避免抢走用户刚点的那个输入框的焦点）
function focusAnswer() {
  if (submitted.value) return
  answerPanelRef.value?.focusFirst()
}
// 点击答题区 / 作答容器的留白才聚焦。注意不能用 @tap.self：小程序里 .self 是比较 target.id 与 currentTarget.id，
// 两者都是空串时恒相等，子元素（输入框、选项）冒泡上来的点击也会被当成“点在容器上”，把焦点抢回第一个输入框。
// 这里改为给两个容器各设固定 id，只有 target.id 正好是它们（真正点在留白上）才聚焦。
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onAreaTap(e: any) {
  const id = e?.target?.id
  if (id === 'answer-area' || id === 'answer-body') focusAnswer()
}
// 答题卡浮层：只有点在遮罩本身（面板外）才关闭，点在面板内部不关闭（同样不能用 .self，见上）
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onMaskTap(e: any) {
  if (e?.target?.id === 'card-mask') closeAnswerCard()
}

// 文本框模式要铺满剩余高度：把「底部操作栏顶部的 y（扣掉作答区下方留白）」传给组件，由组件算出文本框最小高度。
// 题目文字 / 图片高度不固定，所以每题切换、提交后和图片加载后都重新量。
const limitBottom = ref(0)
function measureLimit() {
  uni.createSelectorQuery()
    .select('.action-bar')
    .boundingClientRect((r) => {
      const rect = r as { top: number } | null
      if (rect) limitBottom.value = Math.floor(rect.top - uni.upx2px(24 * 2))   // 作答区下内边距 + 与操作栏之间的留白
      nextTick(() => answerPanelRef.value?.refit())
    })
    .exec()
}
const submitting = ref(false)
const submitted = ref(false)
const isCorrect = ref<boolean | null>(null)

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

// ── 提交答案 ──────────────────────────────────────────────────────────────
async function submitAnswer() {
  if (submitting.value || !question.value) return
  submitting.value = true
  stopTimer()

  try {
    const resp = await trainingApi.submitAnswer({
      session_id: trainingStore.sessionId!,
      question_id: question.value.question_id,
      question_index: question.value.question_index,
      ...buildSubmit(mode.value, answerState.value),   // 未作答也可提交（后端按未作答判错）
      time_spent_sec: elapsed.value,
    })

    submitted.value = true
    isCorrect.value = resp.is_correct
    if (resp.already_answered) {
      // 该题此前已经提交过（比如恢复了一个过期的中断快照，当时没有这题的作答）：服务端不会覆盖，也不会报错，
      // 返回的是首次提交的结果。页面改为显示首次提交的作答，避免“显示的作答”和“判题结果”对不上
      answerState.value = restoreAnswer(question.value, resp.student_answer ?? '')
      uni.showToast({ title: '这道题已经提交过了', icon: 'none' })
    }
    trainingStore.recordAnswer(question.value.question_index, answerText(mode.value, answerState.value), resp.is_correct)

    // 注意：答错后不会自动生成解析，也不会弹出任何提示；学生点击「智能解答」才调用大模型（见 askAi）
  } catch {
    uni.showToast({ title: '提交失败，请重试', icon: 'none' })
    startTimer() // 恢复计时
  } finally {
    submitting.value = false
  }
}

// ── 智能解答 ──────────────────────────────────────────────────────────────
// 作答后点击「智能解答」才调用大模型，得出该题的参考解析（不是答错后立即触发）。
// 按题号缓存：来回切题不丢；已生成过的再点只滚动到解析卡片，不重复调用；失败时在卡片里显示静态解析并可「重新生成」
type AnalysisState = { status: 'loading' | 'completed' | 'degraded'; content: string | null; staticSolution: string | null }
const analyses = ref<Record<number, AnalysisState>>({})
const analysis = computed<AnalysisState | null>(() => analyses.value[currentIndex.value] ?? null)

async function askAi(regenerate = false) {
  const q = question.value
  if (!q || !submitted.value) return
  const idx = currentIndex.value
  const cur = analyses.value[idx]
  if (cur?.status === 'loading') return
  if (cur?.status === 'completed' && !regenerate) {
    uni.pageScrollTo({ selector: '.rag-section', duration: 200 })
    return
  }
  analyses.value = { ...analyses.value, [idx]: { status: 'loading', content: null, staticSolution: null } }
  nextTick(() => uni.pageScrollTo({ selector: '.rag-section', duration: 200 }))
  try {
    const res = await trainingApi.generateAnalysis({ session_id: trainingStore.sessionId!, question_id: q.question_id, regenerate })
    analyses.value = { ...analyses.value, [idx]: { status: res.status, content: res.content, staticSolution: res.static_solution } }
  } catch {
    analyses.value = { ...analyses.value, [idx]: { status: 'degraded', content: null, staticSolution: '网络异常，暂时无法生成解析，请稍后重试' } }
  }
}

// ── 上一题 ────────────────────────────────────────────────────────────────
function goPrev() {
  if (currentIndex.value <= 0) {
    uni.showToast({ title: '已经是第一题了', icon: 'none' })
    return
  }
  jumpToQuestion(currentIndex.value - 1)
}

// ── 下一题 / 完成 ─────────────────────────────────────────────────────────
async function nextOrComplete() {
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
    // 切到下一题：已答过的（比如先点了「上一题」回看）显示只读作答，没答过的重置为未作答
    jumpToQuestion(currentIndex.value + 1)
  }
}

function resetQuestion() {
  answerState.value = emptyAnswer(question.value?.blank_count ?? 0)
  submitted.value = false
  isCorrect.value = null
  startTimer()
}

// ── 退出确认弹窗 ──────────────────────────────────────────────────────────
const showExitDialog = ref(false)

function handleExit() {
  showExitDialog.value = true
}

// 退出不保存训练进度：下次进入同样的训练方式会重新抽题。已提交的答案已经记录（错题集归类不受影响）
function confirmExit() {
  stopTimer()
  if (trainingStore.sessionId) trainingApi.abandonSession(trainingStore.sessionId).catch(() => { /* 退出不受影响 */ })
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
    answerState.value = restoreAnswer(question.value, snap.student_answer)
    submitted.value = true
    isCorrect.value = snap.is_correct
    stopTimer()
  } else {
    resetQuestion()
  }
}

onReady(measureLimit)
// 换题 / 提交后回到未提交态时，上方内容高度变了，需要重新量
watch([question, submitted], () => nextTick(() => setTimeout(measureLimit, 50)))

// ── 收藏 ───────────────────────────────────────────────────────────────────
const favorites = ref<Record<number, boolean>>({})
const isFav = computed(() => !!(question.value && favorites.value[question.value.question_id]))
let favBusy = false

async function loadFavorites() {
  const ids = trainingStore.questions.map((q) => q.question_id)
  if (!ids.length) return
  try {
    const res = await favoriteApi.status(ids)
    const map: Record<number, boolean> = {}
    res.favorite_ids.forEach((id) => { map[id] = true })
    favorites.value = map
  } catch { /* 取不到就当都没收藏，点星星时再按结果更新 */ }
}

async function toggleFavorite() {
  const q = question.value
  if (!q || favBusy) return
  favBusy = true
  const id = q.question_id
  const willFav = !favorites.value[id]
  favorites.value = { ...favorites.value, [id]: willFav }   // 先更新图标，失败再回滚
  try {
    if (willFav) await favoriteApi.add(id)
    else await favoriteApi.remove(id)
    uni.showToast({ title: willFav ? '已收藏' : '已取消收藏', icon: 'none', duration: 1000 })
  } catch {
    favorites.value = { ...favorites.value, [id]: !willFav }
  } finally {
    favBusy = false
  }
}

onMounted(() => {
  loadFavorites()
  // 从中断记录恢复时，停留的这一题可能已经答过（服务端会把数据库里的真实作答补进快照）：直接显示只读的作答，不能再提交
  if (trainingStore.isAnswered(currentIndex.value)) jumpToQuestion(currentIndex.value)
  else startTimer()
})

onUnmounted(() => {
  stopTimer()
})
</script>

<template>
  <page-meta :page-style="pageStyle" />
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
      <!-- ── 题目元信息 ────────────────────────────────────────── -->
      <view class="question-meta">
        <!-- 题目类型标签：图标 + 文字，同色淡底 + 描边（与后台「题目类型」列一致） -->
        <view
          v-if="typeMeta"
          class="type-tag"
          :style="{ color: typeColor, background: typeColor + '1F', borderColor: typeColor + '47' }"
        >
          <view class="type-tag__icon"><SvgIcon :name="typeMeta.icon" :size="28" :color="typeColor" /></view>
          <text class="type-tag__text">{{ typeMeta.label }}</text>
        </view>
        <view v-else />
        <!-- 收藏：五角星，点击收藏，再点取消收藏 -->
        <view class="fav-btn" @tap="toggleFavorite">
          <SvgIcon :name="isFav ? 'star_fill' : 'star'" :size="44" :color="isFav ? '#F59E0B' : 'muted'" />
        </view>
      </view>

      <!-- ── 题目正文 ────────────────────────────────────────────── -->
      <view class="question-card" :style="hl('question')">
        <text class="question-stem">{{ question.stem }}</text>
        <image
          v-if="question.image_url"
          class="question-image"
          :src="question.image_url"
          @load="measureLimit"
          mode="widthFix"
        />
      </view>

      <!-- ── 答题区域 ───────────────────────────────────────────── -->
      <view
        id="answer-area"
        class="answer-area"
        :style="hl('answer')"
        :class="{ 'answer-area--submitted': submitted, 'answer-area--correct': submitted && isCorrect === true, 'answer-area--wrong': submitted && isCorrect === false }"
        @tap="onAreaTap"
      >
        <!-- 标题行 -->
        <view class="answer-head" @tap="focusAnswer">
          <view class="answer-head__icon"><SvgIcon name="book" :size="30" /></view>
          <text class="answer-head__title">{{ submitted ? '你的答案' : '我的解答' }}</text>
          <text v-if="!submitted" class="answer-head__tip">{{ answerTip }}</text>
          <!-- 作答结果图标：在标题行最右侧，与左侧图标、标题同在一条居中线上，大小与左侧图标一致 -->
          <view v-if="submitted && isCorrect !== null" class="answer-head__result">
            <SvgIcon :name="isCorrect ? 'result_correct' : 'result_wrong'" :size="30" :color="resultColor" />
          </view>
        </view>

        <!-- 按题型切换的作答组件 -->
        <view id="answer-body" class="answer-body" @tap="onAreaTap">
          <AnswerPanel
            ref="answerPanelRef"
            v-model="answerState"
            :question="question"
            :readonly="submitted"
            :limit-bottom="limitBottom"
          />
        </view>
      </view>

      <!-- ── 智能解答：参考解析卡（点击「智能解答」后出现，答对答错都可以看） ── -->
      <view v-if="submitted && analysis" class="rag-section">
        <!-- 生成中 -->
        <view v-if="analysis.status === 'loading'" class="rag-skeleton" :style="hl('rag-skel')">
          <view class="rag-skeleton__header">
            <text class="rag-skeleton__title">AI 正在生成解析，请稍候...</text>
          </view>
          <view class="skel-lines">
            <view v-for="i in 4" :key="i" class="skel-line" :style="{ width: `${85 - i * 8}%` }" />
          </view>
        </view>

        <!-- 大模型生成的参考解析 -->
        <view v-else-if="analysis.status === 'completed' && analysis.content" class="rag-card" :style="hl('rag')">
          <view class="rag-card__header">
            <text class="rag-icon">🤖</text>
            <text class="rag-card__title">AI 参考解析</text>
          </view>
          <text class="rag-card__content" :class="{ 'rag-card__content--dark': isDark }" user-select>{{ analysis.content }}</text>
        </view>

        <!-- 降级：静态解析（大模型不可用时），可重新生成 -->
        <view v-else class="rag-card rag-card--static" :style="hl('rag-static')">
          <view class="rag-card__header">
            <text class="rag-icon">📖</text>
            <text class="rag-card__title">参考解析</text>
          </view>
          <text class="rag-card__content" :class="{ 'rag-card__content--dark': isDark }">{{ analysis.staticSolution || '暂无解析' }}</text>
          <button class="retry-btn" @tap="askAi(true)">重新生成 AI 解析</button>
        </view>
      </view>

      <!-- ── 底部操作栏 ──────────────────────────────────────────── -->
      <view class="action-bar">
        <!-- 未提交状态 -->
        <template v-if="!submitted">
          <button class="submit-btn" @tap="submitAnswer">
            <view v-if="submitting" class="spinner" />
            <text class="submit-btn__text">{{ submitting ? '提交中...' : '提交答案' }}</text>
          </button>
        </template>

        <!-- 已提交状态 -->
        <template v-else>
          <!-- 三个按钮组成一个整体：两端按钮靠边侧是圆角，相邻的内侧是直角 -->
          <view class="action-group">
            <button class="seg-btn seg-btn--prev" @tap="goPrev">
              <text class="seg-btn__text">‹ 上一题</text>
            </button>
            <button class="seg-btn seg-btn--ai" @tap="askAi()">
              <view v-if="analysis?.status === 'loading'" class="seg-spinner" />
              <SvgIcon v-else name="sparkles" :size="32" :color="midBtnColor" />
              <text class="seg-btn__text">{{ analysis?.status === 'loading' ? '生成中...' : '智能解答' }}</text>
            </button>
            <button class="seg-btn seg-btn--next" @tap="nextOrComplete">
              <text class="seg-btn__text">{{ isLast ? '完成训练' : '下一题 ›' }}</text>
            </button>
          </view>
        </template>
      </view>
    </template>

    <!-- 退出确认弹窗 -->
    <view v-if="showExitDialog" class="dialog-mask">
      <view class="dialog">
        <text class="dialog__title">确认退出训练？</text>
        <text class="dialog__desc">退出后不会保存本次训练，下次进入将重新抽取题目</text>
        <view class="dialog__btns">
          <button class="dialog-btn dialog-btn--cancel" @tap="cancelExit">继续训练</button>
          <button class="dialog-btn dialog-btn--confirm" @tap="confirmExit">退出</button>
        </view>
      </view>
    </view>

    <!-- 答题卡浮层 -->
    <view v-if="showAnswerCard" id="card-mask" class="card-mask" @tap="onMaskTap">
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
  border-bottom: 1rpx solid $border;
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
  border: 1rpx solid $border;
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
  border: 1rpx solid $border;
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

// 题目类型标签：胶囊 + 淡色底 + 同色描边 + 图标 + 文字
.type-tag {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 22rpx 10rpx 16rpx;   // 上下内边距 5px
  border-radius: $r-pill;
  border: 1rpx solid transparent;

  // 图标和文字各占一个高度相同（28rpx）的盒子并垂直居中，才能真正对齐：
  // 自定义组件的外层元素里是 inline-block 的图片，行高会把外层撑得比图标高，图标会偏上
  &__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28rpx;
    height: 28rpx;
    line-height: 0;
    flex-shrink: 0;
  }

  &__text {
    font-size: $font-size-xs;
    font-weight: 500;
    line-height: 28rpx;
    height: 28rpx;
  }
}

.fav-btn {
  width: 72rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

// ── 题目卡 ────────────────────────────────────────────────────────────────
.question-card {
  @include glass-panel;
  margin: $space-3 $space-4;
  padding: $space-4;
  border: 1rpx solid $border;
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
  @include glass-panel(false, false);   // 输入类组件：不要扫光、不要渐变高亮边，聚焦时也不换边框色
  margin: 0 $space-4 $space-3;
  padding: $space-3;
  border: 1rpx solid $border;
  transition: $transition-base;

  // 提交后按对错变色：极淡的同色底（亮色 4% / 暗色 5%，只做淡淡的底，不遮住作答内容）+ 较实的同色描边（40%）；取值见 --result-*
  &--correct {
    background: var(--result-ok-bg);
    border-color: var(--result-ok-border);
  }
  &--wrong {
    background: var(--result-bad-bg);
    border-color: var(--result-bad-border);
  }
}

// 标题行：小图标 + “我的解答” + 右侧按题型给出的一句格式提示
.answer-head {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-2;
  padding: 0 $space-1;

  // 标题行里的三个元素（左图标 / 标题文字 / 右侧结果图标）都放进同样高度（30rpx）的盒子里并垂直居中，才能真正对齐：
  // 图标是自定义组件，外层元素里是 inline-block 图片，会被行高撑高导致图标偏上；文字也固定行高与盒高一致
  &__icon,
  &__result {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30rpx;
    height: 30rpx;
    line-height: 0;
    flex-shrink: 0;
  }

  &__result { margin-left: auto; }

  &__title {
    font-size: $font-size-sm;
    font-weight: 700;
    color: $text-1;
    line-height: 30rpx;
    height: 30rpx;
  }

  &__tip {
    margin-left: auto;
    font-size: $font-size-xs;
    color: $text-3;
  }
}

// 作答组件容器（组件内部自带各题型样式：选项行、填空下划线、应用题两栏、文本框、符号快捷条）
.answer-body {
  padding: 0 $space-1;
}

// ── 提示卡 ────────────────────────────────────────────────────────────────
// ── 结果反馈 ─────────────────────────────────────────────────────────────
// ── RAG 解析区 ────────────────────────────────────────────────────────────
.rag-section {
  margin: 0 $space-4 $space-3;
}

.rag-skeleton {
  @include glass-panel(false);
  padding: $space-4;
  border: 1rpx solid $border;
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
  @include glass-panel;
  padding: $space-4;
  border: 1rpx solid $border;

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

    // 暗色下正文用白色（次要文字色在深色底上偏暗，长段解析不好读）；亮色保持原样
    &--dark { color: #ffffff; }
  }
}

.rag-icon {
  font-size: 36rpx;
}

.retry-btn {
  margin-top: $space-3;
  height: 72rpx;
  background: $primary-light;
  border: 1rpx solid $primary-border;
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
  background: $bg-surface;   // 不透明实色底
  border-top: 1rpx solid $border;
  display: flex;
  gap: $space-3;
  align-items: center;
  // 必须设置层级：玻璃面板的高亮边 / 扫光伪元素是 z-index: 2，底部栏没有 z-index 时会被它们压在下面，
  // 滚到底部栏下面的卡片边框就会从底部栏上「透」出来。100 高于面板伪元素，低于弹窗遮罩（200）
  z-index: 100;
}

.submit-btn {
  flex: 1;
  height: 88rpx;
  background: $cta-gradient;
  box-shadow: $shadow-cta;
  border-radius: $r-pill;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;

  &::after { border: none; }

  &__text {
    font-size: $font-size-lg;
    color: $on-primary;
    font-weight: 700;
  }
}

// 已提交后的操作栏：上一题 | 智能解答 | 下一题，组成一个整体的分段按钮
// 外层容器是胶囊（圆角 + overflow:hidden），所以只有两端靠边侧是圆角，按钮之间的内侧是直角；按钮之间留 2px（4rpx）间距。
// 渐变：三个按钮合起来是一条「从左到右」的连续渐变（灰底 → 主色淡 → 主色）。因为按钮之间有间距，不能再把渐变画在容器上，
// 而是每个按钮各画一份同样的渐变，大小都设成整个按钮组的宽度、再按各自的偏移错开，拼起来就是连续的一条。
// 整个按钮组的宽度固定：操作栏左右内边距各 32rpx（$space-4），所以 = 750rpx − 64rpx = 686rpx；三个按钮平分剩余宽度：(686 − 2×4) / 3 = 226rpx；第 2 / 3 个按钮的渐变偏移 = 前面所有按钮的宽度加间距 = 230rpx / 460rpx
$group-w: 686rpx;
$seg-gap: 4rpx;

.action-group {
  flex: 1;
  display: flex;
  gap: $seg-gap;
  height: 88rpx;
  border-radius: $r-pill;
  overflow: hidden;
}

.seg-btn {
  flex: 1;
  height: 100%;
  border: none;
  border-radius: 0;
  padding: 0;
  background-color: $bg-muted;
  background-image: linear-gradient(90deg, rgba(0, 0, 0, 0) 0%, $primary-border 50%, $primary 100%);
  background-size: $group-w 100%;
  background-repeat: no-repeat;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-1;

  &::after { border: none; }

  &__text {
    font-size: $font-size-base;
    font-weight: 600;
  }

  // 上一题：渐变最左段（灰底），次要文字色
  &--prev { background-position: 0 0; }
  &--prev .seg-btn__text { color: $text-2; }
  // 智能解答：渐变中段，文字色同「选中态」（暗色白 / 亮色深蓝）
  &--ai { background-position: -230rpx 0; }
  &--ai .seg-btn__text { color: var(--option-on-text); }
  // 下一题：渐变最右段（主色），主按钮文字色
  &--next { background-position: -460rpx 0; }
  &--next .seg-btn__text { color: $on-primary; font-weight: 700; }
}

// 智能解答生成中的小转圈（主色）
.seg-spinner {
  width: 30rpx;
  height: 30rpx;
  border-radius: 50%;
  border: 4rpx solid $primary-border;
  border-top-color: $primary;
  animation: spin 0.7s linear infinite;
}

// ── AI 主动介入浮动条 ─────────────────────────────────────────────────────
.spinner {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 4rpx solid $on-primary-line;
  border-top-color: $on-primary;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

// ── 退出确认弹窗 ──────────────────────────────────────────────────────────
.dialog-mask {
  position: fixed;
  inset: 0;
  background: $mask;
  backdrop-filter: blur(6px);
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
  border: 1rpx solid $border;
  box-shadow: $shadow-md;
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
  border-radius: $r-pill;
  font-size: $font-size-base;
  font-weight: 600;
  border: none;

  &::after { border: none; }

  &--cancel {
    background: $bg-surface;
    border: 1rpx solid $border;
    color: $text-2;
  }

  &--confirm {
    background: $cta-gradient;
    box-shadow: $shadow-cta;
    color: $on-primary;
  }
}

// ── 答题卡面板 ────────────────────────────────────────────────────────────
.card-mask {
  position: fixed;
  inset: 0;
  background: $mask;
  backdrop-filter: blur(6px);
  display: flex;
  align-items: flex-end;
  z-index: 200;
}

.answer-card {
  width: 100%;
  background: $bg-surface;
  border-radius: $r-xl $r-xl 0 0;
  border-top: 1rpx solid $border;
  box-shadow: $shadow-md;
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
  border: 1rpx solid $border;
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
    background: $primary-light;
    border-width: 2rpx;
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
  border: 1rpx solid $border;
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

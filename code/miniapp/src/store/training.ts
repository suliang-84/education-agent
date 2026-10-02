/**
 * 训练会话 Store
 * 管理当前进行中的训练状态（题目、答题进度、当前维度）
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TrainingQuestion, TrainingSessionResp, InterruptRecord } from '@/api/training'
import type { TrainingDimension } from '@/constants'

export const useTrainingStore = defineStore('training', () => {
  const sessionId = ref<string | null>(null)
  const dimension = ref<TrainingDimension | null>(null)
  const subjectCode = ref<string | null>(null)
  const scopeInfo = ref<Record<string, unknown>>({})
  const scopeLabel = ref<string>('')
  const questions = ref<TrainingQuestion[]>([])
  const currentIndex = ref(0)
  const correctCount = ref(0)
  const focusPower = ref<string | null>(null)
  const preferredForce = ref<string | null>(null)   // 优势入口力（借强补弱切入点）
  const tipsHint = ref<string | null>(null)          // 借强补弱提示文案
  // 已提交答案快照：key = question_index
  const answers = ref<Record<number, { student_answer: string; is_correct: boolean }>>({})

  function initSession(resp: TrainingSessionResp, subject_code: string) {
    sessionId.value = resp.session_id
    dimension.value = resp.training_dimension
    subjectCode.value = subject_code
    scopeInfo.value = (resp.scope_info as Record<string, unknown>) ?? {}
    scopeLabel.value = (resp.scope_info as Record<string, unknown> & { name?: string })?.name ?? ''
    questions.value = resp.questions
    currentIndex.value = 0
    correctCount.value = 0
    focusPower.value = resp.training_focus_power
    preferredForce.value = resp.preferred_force ?? null
    tipsHint.value = resp.tips?.hint ?? null
    answers.value = {}
  }

  function restoreFromInterrupt(interrupt: InterruptRecord) {
    sessionId.value = interrupt.session_id
    dimension.value = interrupt.training_dimension as TrainingDimension
    subjectCode.value = interrupt.subject_code
    scopeInfo.value = interrupt.scope_info as Record<string, unknown>
    scopeLabel.value = interrupt.scope_label
    questions.value = interrupt.questions_snapshot
    currentIndex.value = interrupt.current_question_index
    correctCount.value = interrupt.answers_snapshot.filter(a => a.is_correct).length
    focusPower.value = null
    preferredForce.value = null
    tipsHint.value = null
    // 还原已答快照
    answers.value = {}
    for (const a of interrupt.answers_snapshot) {
      answers.value[a.question_index] = {
        student_answer: a.student_answer,
        is_correct: a.is_correct,
      }
    }
  }

  function recordAnswer(index: number, student_answer: string, is_correct: boolean) {
    answers.value[index] = { student_answer, is_correct }
    if (is_correct) correctCount.value++
  }

  function getAnswersSnapshot() {
    return Object.entries(answers.value).map(([idx, a]) => ({
      question_index: Number(idx),
      student_answer: a.student_answer,
      is_correct: a.is_correct,
    }))
  }

  function nextQuestion() {
    if (currentIndex.value < questions.value.length - 1) {
      currentIndex.value++
    }
  }

  function jumpToQuestion(index: number) {
    if (index >= 0 && index < questions.value.length) {
      currentIndex.value = index
    }
  }

  function reset() {
    sessionId.value = null
    dimension.value = null
    subjectCode.value = null
    scopeInfo.value = {}
    scopeLabel.value = ''
    questions.value = []
    currentIndex.value = 0
    correctCount.value = 0
    focusPower.value = null
    preferredForce.value = null
    tipsHint.value = null
    answers.value = {}
  }

  const currentQuestion = () => questions.value[currentIndex.value] ?? null
  const isLastQuestion = () => currentIndex.value === questions.value.length - 1
  const isAnswered = (index: number) => index in answers.value
  const progress = () =>
    questions.value.length > 0
      ? Math.round(((currentIndex.value + 1) / questions.value.length) * 100)
      : 0

  return {
    sessionId,
    dimension,
    subjectCode,
    scopeInfo,
    scopeLabel,
    questions,
    currentIndex,
    correctCount,
    focusPower,
    preferredForce,
    tipsHint,
    answers,
    initSession,
    restoreFromInterrupt,
    recordAnswer,
    getAnswersSnapshot,
    nextQuestion,
    jumpToQuestion,
    reset,
    currentQuestion,
    isLastQuestion,
    isAnswered,
    progress,
  }
})

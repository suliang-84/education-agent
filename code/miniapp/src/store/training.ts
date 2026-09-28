/**
 * 训练会话 Store
 * 管理当前进行中的训练状态（题目、答题进度、当前维度）
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TrainingQuestion, TrainingSessionResp } from '@/api/training'
import type { TrainingDimension } from '@/constants'

export const useTrainingStore = defineStore('training', () => {
  const sessionId = ref<string | null>(null)
  const dimension = ref<TrainingDimension | null>(null)
  const questions = ref<TrainingQuestion[]>([])
  const currentIndex = ref(0)
  const correctCount = ref(0)
  const focusPower = ref<string | null>(null)

  function initSession(resp: TrainingSessionResp) {
    sessionId.value = resp.session_id
    dimension.value = resp.training_dimension
    questions.value = resp.questions
    currentIndex.value = 0
    correctCount.value = 0
    focusPower.value = resp.training_focus_power
  }

  function nextQuestion() {
    if (currentIndex.value < questions.value.length - 1) {
      currentIndex.value++
    }
  }

  function markCorrect() {
    correctCount.value++
  }

  function reset() {
    sessionId.value = null
    dimension.value = null
    questions.value = []
    currentIndex.value = 0
    correctCount.value = 0
    focusPower.value = null
  }

  const currentQuestion = () => questions.value[currentIndex.value] ?? null
  const isLastQuestion = () => currentIndex.value === questions.value.length - 1
  const progress = () =>
    questions.value.length > 0
      ? Math.round(((currentIndex.value + 1) / questions.value.length) * 100)
      : 0

  return {
    sessionId,
    dimension,
    questions,
    currentIndex,
    correctCount,
    focusPower,
    initSession,
    nextQuestion,
    markCorrect,
    reset,
    currentQuestion,
    isLastQuestion,
    progress,
  }
})

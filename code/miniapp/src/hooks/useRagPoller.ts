/**
 * RAG 生成状态轮询 Hook
 * 答错后轮询 RAG 状态，最多 15 次（每 3 秒），超时降级
 */
import { ref } from 'vue'
import { trainingApi } from '@/api/training'

export function useRagPoller() {
  const ragContent = ref<string | null>(null)
  const staticSolution = ref<string | null>(null)
  const status = ref<'idle' | 'pending' | 'completed' | 'degraded'>('idle')
  const canRetry = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null
  let retryCount = 0
  const MAX_RETRIES = 15

  function startPolling(answerRecordId: number) {
    status.value = 'pending'
    ragContent.value = null
    staticSolution.value = null
    retryCount = 0
    poll(answerRecordId)
  }

  function poll(answerRecordId: number) {
    timer = setTimeout(async () => {
      try {
        const res = await trainingApi.getRagStatus(answerRecordId)
        if (res.rag_status === 'completed') {
          status.value = 'completed'
          ragContent.value = res.rag_content
          return
        }
        if (res.rag_status === 'degraded') {
          status.value = 'degraded'
          staticSolution.value = res.static_solution
          canRetry.value = res.can_retry
          return
        }
        retryCount++
        if (retryCount >= MAX_RETRIES) {
          status.value = 'degraded'
          staticSolution.value = '（AI暂时繁忙，请查看参考解析）'
          return
        }
        poll(answerRecordId)
      } catch {
        status.value = 'degraded'
      }
    }, 3000)
  }

  async function retry(answerRecordId: number) {
    await trainingApi.retryRag(answerRecordId)
    startPolling(answerRecordId)
  }

  function stop() {
    if (timer) clearTimeout(timer)
    timer = null
  }

  return { ragContent, staticSolution, status, canRetry, startPolling, retry, stop }
}

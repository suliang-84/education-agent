/**
 * 个性化AI训练模块 API — §5
 */
import { http } from '@/utils/request'
import type { TrainingDimension } from '@/constants'

export interface TrainingQuestion {
  question_id: number
  question_index: number
  stem: string
  image_url: string | null
  difficulty: string
  power_type: string
  answer?: Record<string, unknown>
}

export interface CreateSessionReq {
  training_dimension: TrainingDimension
  knowledge_point_id?: number
  chapter_id?: number
  semester_id?: number
  subject_code?: string
}

export interface TrainingSessionResp {
  session_id: string
  training_dimension: TrainingDimension
  training_mode: string
  training_focus_power: string
  preferred_force: string
  dimension_config: { version_number: string; questions_per_session: number }
  questions: TrainingQuestion[]
  total_questions: number
  tips: { focus_power_name: string; hint: string }
}

export interface WrongSummarySubject {
  subject_code: string
  subject_name: string
  pending_count: number
}

export const trainingApi = {
  /** 获取错题科目统计（进入错题集维度前调用） */
  getWrongSummary: (subject_code?: string) =>
    http.get<{ total_pending: number; subjects: WrongSummarySubject[] }>(
      '/training/wrong-summary',
      subject_code ? { subject_code } : {}
    ),

  /** 创建训练会话 */
  createSession: (data: CreateSessionReq) =>
    http.post<TrainingSessionResp>('/training/session', data),

  /** 提交单题答案 */
  submitAnswer: (data: {
    session_id: string
    question_id: number
    question_index: number
    student_answer?: string
    time_spent_sec: number
    hint_level_used?: number
  }) =>
    http.post<{
      answer_record_id: number
      is_correct: boolean
      rag_status: string | null
      proactive_trigger: boolean
    }>('/training/answer', data),

  /** 查询 RAG 生成状态（前端轮询，≤15次） */
  getRagStatus: (answer_record_id: number) =>
    http.get<{
      rag_status: 'pending' | 'completed' | 'degraded'
      rag_content: string | null
      static_solution: string | null
      retry_count: number
      can_retry: boolean
    }>(`/training/rag-status/${answer_record_id}`),

  /** 重试 RAG 生成 */
  retryRag: (answer_record_id: number) =>
    http.post('/training/rag-retry', { answer_record_id }),

  /** 完成训练会话 */
  completeSession: (session_id: string) =>
    http.post<{
      session_id: string
      summary: { total_questions: number; correct_count: number; accuracy_rate: number }
      profile_update_status: string
      wrong_answer_count: number
    }>('/training/complete', { session_id }),
}

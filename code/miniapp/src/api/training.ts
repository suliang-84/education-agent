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
  question_type?: string | null   // SINGLE_CHOICE / MULTIPLE_CHOICE / TRUE_FALSE / FILL_BLANK / APPLICATION
  options?: Array<{ key: string; text: string }> | null   // 单选 / 多选的选项（服务端从题干拆出；拆分失败为 null，退回文本框）
  blank_count?: number | null     // 填空题的空数（服务端只下发数量，不下发标准答案）
  reason?: { tag: string; label: string }   // 智能训练：推荐理由（如「薄弱知识点」「你提到的困惑」）
}

export interface CreateSessionReq {
  training_dimension: TrainingDimension
  knowledge_point_id?: number
  chapter_id?: number
  semester_id?: number
  subject_code?: string
  wrong_status?: 'pending' | 'mastered'   // 错题集训练：待攻克（默认）/ 已攻克
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
  scope_info?: { knowledge_point_id?: number; name?: string }   // 按知识点训练：知识点信息（答题页顶部范围标签）
  tips: { focus_power_name: string; hint: string }
}

export interface WrongSummarySubject {
  subject_code: string
  subject_name: string
  pending_count: number
}

export interface InterruptRecord {
  interrupt_id: string
  subject_code: string
  training_dimension: string
  scope_label: string
  scope_info: Record<string, unknown>
  questions_snapshot: TrainingQuestion[]
  answers_snapshot: Array<{ question_index: number; student_answer: string; is_correct: boolean }>
  current_question_index: number
  total_questions: number
  session_id: string
  interrupted_at: string
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
    student_answers?: string[]   // 填空题：按空作答
    final_answer?: string        // 应用题：最终答案栏
    time_spent_sec: number
    hint_level_used?: number
  }) =>
    http.post<{
      answer_record_id: number
      is_correct: boolean
      rag_status: string | null
      proactive_trigger: boolean
      already_answered?: boolean         // true：该题此前已提交过，本次没有新增记录（重复提交 / 恢复了过期的中断快照）
      student_answer?: string | null     // already_answered 时为此前提交的作答
    }>('/training/answer', data),

  /**
   * 智能解答：点击「智能解答」时才调用大模型，得出该题的参考解析（见接口设计说明书 §5.3）。
   * 大模型耗时较长，请求超时放宽到 90 秒；失败时服务端降级返回静态解析（status = degraded），不会抛错。
   * silent：失败不弹全局 toast，由页面在解析卡片里提示。
   */
  generateAnalysis: (data: { session_id: string; question_id: number; regenerate?: boolean }) =>
    http.post<{
      status: 'completed' | 'degraded'
      content: string | null
      static_solution: string | null
      cached: boolean
    }>('/training/analysis', data, { timeout: 90000, silent: true } as never),

  /** 退出训练：放弃本次题卷（不保存进度）；失败不影响退出，所以静默 */
  abandonSession: (session_id: string) =>
    http.post('/training/abandon', { session_id }, { silent: true } as never),

  /** 完成训练会话 */
  completeSession: (session_id: string) =>
    http.post<{
      session_id: string
      summary: { total_questions: number; correct_count: number; accuracy_rate: number }
      profile_update_status: string
      wrong_answer_count: number
    }>('/training/complete', { session_id }),

  /** 查询训练中断记录 */
  getInterrupt: (subject_code: string, training_dimension: string) =>
    http.get<{ has_interrupt: boolean; interrupt: InterruptRecord | null }>(
      '/training/interrupt',
      { subject_code, training_dimension }
    ),

  /** 保存训练中断状态 */
  saveInterrupt: (data: {
    session_id: string
    subject_code: string
    training_dimension: string
    scope_info: Record<string, unknown>
    scope_label: string
    questions_snapshot: TrainingQuestion[]
    answers_snapshot: Array<{ question_index: number; student_answer: string; is_correct: boolean }>
    current_question_index: number
  }) =>
    http.post<{ interrupt_id: string; interrupted_at: string }>('/training/interrupt', data),

  /** 删除训练中断记录 */
  deleteInterrupt: (subject_code: string, training_dimension: string) =>
    http.delete('/training/interrupt', { subject_code, training_dimension }),
}

/**
 * 五力认知测试模块 API — §3
 */
import { http } from '@/utils/request'

export interface CogQuestion {
  id: number
  question_no: number
  stem: string
  image_url: string | null
  answers: Array<{ key: string; text: string }>
  reference_time_sec: number
}

export interface ForceScores {
  INSIGHT: number
  CONSTRUCT: number
  DEDUCE: number
  ADAPT: number
  MIGRATE: number
}

export interface TestProfile {
  profile_id: number
  ai_analysis_status: 'pending' | 'processing' | 'completed' | 'failed'
  forces: Record<string, { ability: number; preference: number; final: number }>
  primary_weakness: string
  recommended_mode: string
  ai_analysis_text?: string
}

export const testApi = {
  /** 获取20道测试题卷（同时创建会话） */
  getQuestions: () =>
    http.get<{ session_id: number; questions: CogQuestion[]; total: number }>('/test/questions'),

  /** 提交单题答案 */
  submitAnswer: (data: {
    session_id: number
    question_id: number
    question_index: number
    selected_option?: string
    time_spent_sec: number
    modify_count?: number
  }) => http.post('/test/answer', data),

  /** 提交测试（触发评分） */
  completeTest: (session_id: number) => http.post<TestProfile>('/test/complete', { session_id }),

  /** 轮询测试结果（含 AI 分析） */
  getResult: (profile_id: number) =>
    http.get<{
      profile_id: number
      ai_analysis_status: string
      ai_analysis_text: string | null
    }>(`/test/result/${profile_id}`),

  /** 历史测试记录 */
  getHistory: () =>
    http.get<Array<{ profile_id: number; created_at: string; is_latest: boolean; forces: ForceScores }>>(
      '/test/history'
    ),
}

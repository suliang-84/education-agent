/**
 * 用户画像 + 错题集 模块 API — §6 §8
 */
import { http } from '@/utils/request'

export interface UserProfile {
  student_id: number
  nickname: string
  avatar_url: string | null
  grade: string | null
  semester: string | null
  is_minor: boolean
  phone_masked: string
}

export interface FivePowerProfile {
  has_profile: boolean
  profile: {
    profile_id: number
    forces: Record<string, { ability: number; preference: number; final: number }>
    primary_weakness: string | null
    preferred_force: string | null
    recommended_mode: string | null
    ai_analysis_text: string | null
    ai_analysis_status: string
  } | null
  training_profile: Record<string, number> | null
}

export interface WrongAnswer {
  wrong_id: string
  question: {
    question_id: number
    stem: string
    difficulty: string
    primary_power: string
  }
  student_answer: string | null
  review_status: string
  created_at: string
}

export const profileApi = {
  /** 获取个人信息 */
  getMe: () => http.get<UserProfile>('/profile/me'),

  /** 更新个人信息 */
  updateMe: (data: { nickname?: string; grade?: string; semester?: string }) =>
    http.patch('/profile/me', data),

  /** 获取当前五力画像（综合分 = 训练×0.6 + 测试×0.4） */
  getFivePower: () => http.get<FivePowerProfile>('/profile/five-power'),

  /** 知识点练习统计 */
  getKpStats: (subject_code?: string) =>
    http.get('/profile/kp-stats', subject_code ? { subject_code } : {}),
}

export const wrongAnswerApi = {
  /** 获取错题列表 */
  getList: (review_status?: string, limit = 20) =>
    http.get<{ list: WrongAnswer[]; total: number }>(
      '/wrong-answers',
      review_status ? { review_status, limit } : { limit }
    ),

  /** 发起 AI 复盘 */
  startReview: (wrong_id: string) =>
    http.post<{
      chat_session_id: string
      question_info: { stem: string; student_answer: string | null; primary_power: string | null }
      opening_message: { role: string; content: string }
    }>(`/wrong-answers/${wrong_id}/review`),
}

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

// 错题集统计树：待攻克 / 已攻克 → 单元 → 知识点（只含当前学期）
export interface WrongPoint { id: number; name: string; count: number }
export interface WrongChapter { id: number; name: string; count: number; points: WrongPoint[] }
export interface WrongTree { count: number; chapters: WrongChapter[] }
export interface WrongOutline {
  need_profile: boolean
  grade: { code: string; name: string } | null
  semester: { code: string; name: string } | null
  grade_options: Array<{ code: string; name: string }>
  semester_options: Array<{ code: string; name: string }>
  pending: WrongTree
  mastered: WrongTree
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
  /** 错题集：待攻克 / 已攻克 → 单元 → 知识点的题数统计 */
  getOutline: (subject_code: string) =>
    http.get<WrongOutline>('/wrong-answers/outline', { subject_code }),
}

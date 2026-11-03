/**
 * 题目收藏 / 收藏夹 API
 */
import { http } from '@/utils/request'
import type { WrongTree } from '@/api/profile'

export interface FavoritesOutline {
  need_profile: boolean
  grade: { code: string; name: string } | null
  semester: { code: string; name: string } | null
  grade_options: Array<{ code: string; name: string }>
  semester_options: Array<{ code: string; name: string }>
  tree: WrongTree   // 收藏夹 → 单元 → 知识点（只含当前学期）
}

export const favoriteApi = {
  /** 收藏（幂等） */
  add: (question_id: number) => http.post<{ question_id: number; is_favorite: boolean }>('/favorites', { question_id }),
  /** 取消收藏（幂等） */
  remove: (question_id: number) => http.delete<{ question_id: number; is_favorite: boolean }>(`/favorites/${question_id}`),
  /** 一批题目里哪些已收藏 */
  status: (question_ids: number[]) =>
    http.get<{ favorite_ids: number[] }>('/favorites/status', { question_ids: question_ids.join(',') }),
  /** 该科目的收藏题数（训练页入口卡片） */
  count: (subject_code: string) => http.get<{ count: number }>('/favorites/count', { subject_code }),
  /** 收藏夹统计树 */
  getOutline: (subject_code: string) => http.get<FavoritesOutline>('/favorites/outline', { subject_code }),
}

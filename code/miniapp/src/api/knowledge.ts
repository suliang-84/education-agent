/**
 * 知识点导航模块 API — §4
 */
import { http } from '@/utils/request'

export interface Subject {
  id: number
  name: string
  code: string
}

export interface Grade {
  id: number
  name: string
  code: string
  subject_id: number
}

export interface KnowledgePoint {
  id: number
  name: string
  code: string | null
  chapter_id: number
  chapter_name: string
}

export interface OutlinePoint { id: number; name: string; question_count: number }
export interface OutlineChapter { id: number; name: string; question_count: number; points: OutlinePoint[] }
export interface Outline {
  need_profile: boolean                                  // 学生资料缺年级 / 学期：需要弹窗补充
  grade: { code: string; name: string } | null
  semester: { code: string; name: string } | null
  grade_options: Array<{ code: string; name: string }>
  semester_options: Array<{ code: string; name: string }>
  chapters: OutlineChapter[]                             // 当前年级学期下按单元分组的知识点
}

export const knowledgeApi = {
  /** 按知识点训练：当前年级学期的单元与知识点（带可抽题数） */
  getOutline: (subject_code: string) =>
    http.get<Outline>('/knowledge/outline', { subject_code }),

  /** 获取学科列表 */
  getSubjects: () => http.get<Subject[]>('/knowledge/subjects'),

  /** 获取年级列表 */
  getGrades: (subject_code?: string) =>
    http.get<Grade[]>('/knowledge/grades', subject_code ? { subject_code } : {}),

  /** 获取知识点列表（自动按学生当前学期过滤） */
  getPoints: (subject_code?: string) =>
    http.get<KnowledgePoint[]>('/knowledge/points', subject_code ? { subject_code } : {}),
}

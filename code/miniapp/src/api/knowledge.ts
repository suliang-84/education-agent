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

export const knowledgeApi = {
  /** 获取学科列表 */
  getSubjects: () => http.get<Subject[]>('/knowledge/subjects'),

  /** 获取年级列表 */
  getGrades: (subject_code?: string) =>
    http.get<Grade[]>('/knowledge/grades', subject_code ? { subject_code } : {}),

  /** 获取知识点列表（自动按学生当前学期过滤） */
  getPoints: (subject_code?: string) =>
    http.get<KnowledgePoint[]>('/knowledge/points', subject_code ? { subject_code } : {}),
}

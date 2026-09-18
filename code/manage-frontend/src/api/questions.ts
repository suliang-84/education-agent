/**
 * 题库管理接口模块
 * 接口文档：§9.1（题目管理）
 *
 * 流程：录入题干 → 触发模型分析（异步）→ 审核结果（可修改）→ 发布 / 驳回
 * 状态流：draft → analyzing → pending_review → published / archived
 *
 * v1.2.0：新增 analyze、publish、reject 接口，撤销独立 AI 标注审核
 * v1.3.0：新增知识体系树接口（9.1.0），题目列表支持五级体系节点过滤
 */
import request from './request'
import type { Question, PaginatedResponse } from '@/types'

// ── 知识体系树（五级）────────────────────────────────────────

/** 知识体系树节点类型 */
export interface KnowledgeTreeNode {
  type: 'subject' | 'grade' | 'semester' | 'chapter' | 'knowledge_point'
  id: number
  name: string
  code?: string
  published_count: number
  children?: KnowledgeTreeNode[]
}

export interface KnowledgeTreeResponse {
  tree: KnowledgeTreeNode[]
}

export const knowledgeTreeApi = {
  /**
   * 获取完整五级知识体系树（科目→年级→学期→单元→知识点）
   * 各节点附带已发布题目数量，用于题库管理左侧导航树渲染
   * GET /api/v1/admin/knowledge-tree
   * 接口文档：§9.1.0
   */
  getTree: (params?: { with_counts?: boolean }) =>
    request.get<unknown, KnowledgeTreeResponse>('/knowledge-tree', { params }),
}

// ── 题目列表查询参数 ─────────────────────────────────────────

export interface QuestionListParams {
  // 知识体系节点过滤（五级，互斥使用）
  subject_id?: number
  grade_id?: number
  semester_id?: number
  chapter_id?: number
  knowledge_point_id?: number
  // 其他筛选
  status?: 'draft' | 'analyzing' | 'pending_review' | 'published' | 'archived'
  difficulty?: 'basic' | 'advanced' | 'challenge'
  keyword?: string
  // 页码分页
  page?: number
  limit?: number
}

// ── 发布请求体（审核确认后携带的完整字段）────────────────────

export interface PublishPayload {
  subject_id: number
  grade_id: number
  semester_id: number
  chapter_id: number
  knowledge_point_ids: number[]
  difficulty: 'basic' | 'advanced' | 'challenge'
  solution: string
  common_error?: string
  power_solutions?: Record<string, string>
  five_power_weights: Record<string, number>
  transfer_directions?: string[]
  question_type?: string
  answer?: Record<string, unknown>
}

// ── 题目管理接口 ─────────────────────────────────────────────

export const questionApi = {
  /**
   * 题目列表（支持五级知识体系节点过滤 + 状态 / 难度 / 关键词筛选）
   * GET /api/v1/admin/questions
   * 接口文档：§9.1.1
   */
  getList: (params: QuestionListParams) =>
    request.get<unknown, PaginatedResponse<Question>>('/questions', { params }),

  /**
   * 查询题目详情（含最新 AI 分析结果，用于审核页面渲染）
   * GET /api/v1/admin/questions/{question_id}
   * 接口文档：§9.1.4
   */
  getOne: (questionId: number) =>
    request.get<unknown, Question>(`/questions/${questionId}`),

  /**
   * 录入题干（创建题目）—— 仅需 stem + 可选 image_url
   * 创建后状态为 draft，其余字段由大模型分析后填充
   * POST /api/v1/admin/questions
   * 接口文档：§9.1.2
   */
  create: (data: { stem: string; image_url?: string | null }) =>
    request.post<unknown, { question_id: number; status: string }>('/questions', data),

  /**
   * 触发大模型分析（draft → analyzing）
   * 异步执行，前端轮询详情接口等待状态变为 pending_review
   * POST /api/v1/admin/questions/{question_id}/analyze
   * 接口文档：§9.1.3
   */
  analyze: (questionId: number) =>
    request.post<unknown, { question_id: number; status: string; analysis_round: number }>(
      `/questions/${questionId}/analyze`
    ),

  /**
   * 发布题目（审核通过）
   * 携带管理员确认 / 修改后的完整字段，题目状态变为 published，触发向量化
   * POST /api/v1/admin/questions/{question_id}/publish
   * 接口文档：§9.1.5
   */
  publish: (questionId: number, data: PublishPayload) =>
    request.post<unknown, { question_id: number; status: string; embedding_status: string }>(
      `/questions/${questionId}/publish`,
      data
    ),

  /**
   * 驳回题目（审核不通过，自动重新触发模型分析）
   * 填写驳回意见后系统自动提交重分析，状态变回 analyzing
   * POST /api/v1/admin/questions/{question_id}/reject
   * 接口文档：§9.1.6
   */
  reject: (questionId: number, data: { rejection_reason: string }) =>
    request.post<unknown, { question_id: number; status: string; analysis_round: number }>(
      `/questions/${questionId}/reject`,
      data
    ),

  /**
   * 下架题目（published → archived）
   * PATCH /api/v1/admin/questions/{question_id}/status
   * 接口文档：§9.1.7
   */
  archive: (questionId: number) =>
    request.patch<unknown, { question_id: number; status: string }>(
      `/questions/${questionId}/status`,
      { status: 'archived' }
    ),

  /**
   * 软删除题目（仅 draft 状态允许）
   * DELETE /api/v1/admin/questions/{question_id}
   * 接口文档：§9.1.8
   */
  delete: (questionId: number) =>
    request.delete(`/questions/${questionId}`),

  /**
   * 批量导入题干（文件上传，每条自动触发模型分析）
   * POST /api/v1/admin/questions/batch-import
   * Content-Type: multipart/form-data
   * 接口文档：§9.1.9
   */
  batchImport: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request.post<unknown, { import_task_id: string; total_count: number; status: string }>(
      '/questions/batch-import',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },

  /**
   * 批量导入题干（文本数组形式，兼容当前前端实现）
   * POST /api/v1/admin/questions/batch-import
   */
  batchImportStems: (stems: string[]) =>
    request.post<unknown, { import_task_id: string; total_count: number; status: string }>(
      '/questions/batch-import',
      { stems }
    ),
}

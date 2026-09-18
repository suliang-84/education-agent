/**
 * 五力测试题维护接口模块
 * 接口文档：§9.3
 *
 * v1.2.0：新增题目创建、状态变更（发布/下架）接口
 * v1.3.0：去除 target_power、option_scores，答案统一使用 answers 数组
 * v1.4.0：去除 question_type 和 correct_option，新增 description 字段
 *
 * 状态流：draft → published / archived（PATCH /status 接口统一处理）
 * 历史成绩保护：每次测试会话创建时生成内容快照，后续修改不影响历史成绩
 */
import request from './request'
import type { CognitiveQuestion, FivePower } from '@/types'

// ── 响应类型 ─────────────────────────────────────────────────

/** 测试题列表响应（附带测试状态汇总） */
export interface CognitiveListResponse {
  published_count: number     // 当前已发布数量
  test_available: boolean     // 是否满足测试条件（已发布数 ≥ 10）
  list: CognitiveQuestion[]
}

/** 状态变更响应 */
export interface StatusChangeResponse {
  id: number
  status: string
  published_count: number
  test_available: boolean
}

// ── 答案请求体（前端提交时不含 key，后端自动生成 A/B/C/D…）─

export interface CognitiveAnswerInput {
  text: string
  force_weights: Record<FivePower, number>   // 五项之和须等于 10（非负整数）
}

export interface CognitiveQuestionInput {
  description?: string                       // 管理员元数据，不展示给学生（选填）
  stem: string
  image_url?: string | null
  answers: CognitiveAnswerInput[]            // 最少2条，最多8条
  reference_time_sec: number                 // 参考作答时间（秒）
}

// ── 五力测试题接口 ───────────────────────────────────────────

export const cognitiveApi = {
  /**
   * 获取测试题目列表（附带 published_count 和 test_available 汇总）
   * GET /api/v1/admin/cognitive-questions
   * 接口文档：§9.3.1
   */
  getList: (params?: { status?: string; keyword?: string }) =>
    request.get<unknown, CognitiveListResponse>('/cognitive-questions', { params }),

  /**
   * 新增测试题目（创建后状态为 draft）
   * POST /api/v1/admin/cognitive-questions
   * 接口文档：§9.3.2
   */
  create: (data: CognitiveQuestionInput) =>
    request.post<unknown, { id: number; status: string; created_at: string }>(
      '/cognitive-questions',
      data
    ),

  /**
   * 编辑测试题目（支持 draft、published、archived 三种状态）
   * 所有字段均为可选（仅传需修改的字段）；answers 传入时为全量替换
   * PATCH /api/v1/admin/cognitive-questions/{id}
   * 接口文档：§9.3.3
   */
  update: (id: number, data: Partial<CognitiveQuestionInput>) =>
    request.patch<unknown, { id: number; updated_at: string }>(
      `/cognitive-questions/${id}`,
      data
    ),

  /**
   * 发布题目（draft/archived → published）
   * 当前已发布数 ≥ 20 时拒绝发布，返回 COGQ-001
   * PATCH /api/v1/admin/cognitive-questions/{id}/status  body: { status: "published" }
   * 接口文档：§9.3.4
   */
  publish: (id: number) =>
    request.patch<unknown, StatusChangeResponse>(
      `/cognitive-questions/${id}/status`,
      { status: 'published' }
    ),

  /**
   * 下架题目（published → archived）
   * 下架后可在 archived 状态下继续编辑，编辑完成后重新发布
   * PATCH /api/v1/admin/cognitive-questions/{id}/status  body: { status: "archived" }
   * 接口文档：§9.3.4
   */
  archive: (id: number) =>
    request.patch<unknown, StatusChangeResponse>(
      `/cognitive-questions/${id}/status`,
      { status: 'archived' }
    ),

  /**
   * 删除草稿题目（仅 draft 状态，物理删除）
   * DELETE /api/v1/admin/cognitive-questions/{id}
   * 接口文档：§9.3.5
   */
  delete: (id: number) =>
    request.delete(`/cognitive-questions/${id}`),
}

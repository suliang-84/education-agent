/**
 * 训练参数配置接口模块
 * 接口文档：§9.4
 *
 * v2.1：训练参数配置专注于五维度选题参数（各维度独立版本化管理）
 * 全局算法参数（RAG/EWMA）已移至系统参数管理（§9.5）
 * 五力薄弱加权参数已移除
 *
 * 维度枚举：KNOWLEDGE_POINT / UNIT / SEMESTER / ERROR_QUESTIONS / RANDOM
 * 版本规则：同一维度同时只有一个 is_active=true，新版本生效时旧版本自动关闭
 */
import request from './request'
import type { DimensionTrainingConfig } from '@/types'

// ── 维度枚举（对应接口文档 §9.4.3 query param 可选值）────────

export type TrainingDimension =
  | 'KNOWLEDGE_POINT'    // 按知识点
  | 'UNIT'               // 按单元
  | 'SEMESTER'           // 按学期
  | 'ERROR_QUESTIONS'    // 错题集
  | 'RANDOM'             // 随机练习

// ── 维度配置体 ───────────────────────────────────────────────

export interface DimensionConfigInput {
  questions_per_session: number
  dedup_window_size?: number
  /** 难度比例（各项之和须等于100，ERROR_QUESTIONS 维度传 null） */
  difficulty_ratio: { basic: number; advanced: number; challenge: number } | null
  /** 错题集专属：优先排序方式 */
  wrong_priority?: 'most_failed' | 'recent' | 'least_practiced'
  /** 错题集专属：新题混入比例 (0~0.5) */
  new_question_mix_ratio?: number
  /** 错题集专属：连续答对 N 次后移出错题列表 */
  remove_after_correct?: number
}

// ── 维度训练参数接口 ─────────────────────────────────────────

export const trainingApi = {
  /**
   * 获取指定维度当前生效参数版本
   * GET /api/v1/admin/training/dimension-config/active?dimension=KNOWLEDGE_POINT
   * 接口文档：§9.4.3
   */
  getDimensionActive: (dimension: TrainingDimension) =>
    request.get<unknown, DimensionTrainingConfig>(
      '/training/dimension-config/active',
      { params: { dimension } }
    ),

  /**
   * 获取指定维度参数历史版本列表（只读）
   * GET /api/v1/admin/training/dimension-config/history?dimension=KNOWLEDGE_POINT&limit=10
   * 接口文档：§9.4.5
   */
  getDimensionHistory: (dimension: TrainingDimension, limit = 10) =>
    request.get<unknown, { dimension: string; list: DimensionTrainingConfig[] }>(
      '/training/dimension-config/history',
      { params: { dimension, limit } }
    ),

  /**
   * 创建维度训练参数新版本（创建后立即生效，旧版本自动停用）
   * POST /api/v1/admin/training/dimension-config
   * 接口文档：§9.4.4
   */
  createDimensionVersion: (data: {
    dimension: TrainingDimension
    config: DimensionConfigInput
    description?: string
  }) =>
    request.post<unknown, { config_id: number; dimension: string; version_number: string; is_active: boolean }>(
      '/training/dimension-config',
      data
    ),
}

// ── 向后兼容对象（TrainingConfigView 直接使用，接口已调整为文档规范路径）────

import request from './request'
import type { GlobalAlgoConfig } from '@/types'

/**
 * 兼容别名对象（供现有 TrainingConfigView 不修改代码直接调用）
 * 实际对接后端时，全局算法参数接口路径为 /api/v1/admin/system-configs（§9.5）
 * 维度参数接口路径为 /api/v1/admin/training/dimension-config（§9.4.3~9.4.5）
 */
export const trainingConfigApi = {
  // 全局算法参数（路径对应 v2.1 接口规范）
  getGlobalList: () =>
    request.get<unknown, GlobalAlgoConfig[]>('/training-configs/global'),
  getGlobalActive: () =>
    request.get<unknown, GlobalAlgoConfig>('/training-configs/global/active'),
  createGlobal: (data: Partial<GlobalAlgoConfig>) =>
    request.post<unknown, GlobalAlgoConfig>('/training-configs/global', data),

  // 维度参数（路径对应 v2.1 接口规范）
  getDimensionList: (mode: string) =>
    request.get<unknown, unknown[]>(`/training-configs/dimension/${mode}`),
  getDimensionActive: (mode: string) =>
    request.get<unknown, unknown>(`/training-configs/dimension/${mode}/active`),
  createDimension: (mode: string, data: unknown) =>
    request.post<unknown, unknown>(`/training-configs/dimension/${mode}`, data),
}

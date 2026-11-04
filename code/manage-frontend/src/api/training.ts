/**
 * 训练配置接口模块
 * 接口文档：§9.9（训练配置）
 *
 * - 各训练方式的出题参数：每次题数 / 题型比例 / 难度比例 / 避开最近做过的题数
 * - 智能训练的算法参数
 * - 题目分析（大模型）的并发数与超时
 */
import request from './request'
import type { TrainingConfigList, DimensionConfig, AnalysisConfig } from '@/types'

export const trainingConfigApi = {
  /** GET /api/v1/admin/training-configs */
  getAll: () => request.get<unknown, TrainingConfigList>('/training-configs'),

  /** PUT /api/v1/admin/training-configs/{dimension}（学生下一次开始训练时生效） */
  save: (dimension: string, data: Partial<DimensionConfig>) =>
    request.put<unknown, DimensionConfig>(`/training-configs/${dimension}`, data),

  /** PUT /api/v1/admin/analysis-config（对之后触发的题目分析生效） */
  saveAnalysis: (data: AnalysisConfig) =>
    request.put<unknown, AnalysisConfig>('/analysis-config', data),
}

/**
 * 数据看板接口模块
 * 接口文档：§9.7
 *
 * 所有接口仅 SUPER_ADMIN 可访问
 * 支持统一 days 参数（7 / 30）过滤时间范围
 */
import request from './request'
import type { DashboardStats, TokenTrend, UserGrowthPoint } from '@/types'

export const dashboardApi = {
  /**
   * 概览指标卡（4张KPI卡片数据：用户规模/训练活跃/AI助教/题库健康度）
   * GET /api/v1/admin/dashboard/stats?days=30
   * 接口文档：§9.7.1
   */
  getStats: (days = 30) =>
    request.get<unknown, DashboardStats>('/dashboard/stats', { params: { days } }),

  /**
   * 用户增长趋势（每日新增+活跃，用于主看板折线图）
   * GET /api/v1/admin/dashboard/user-growth?days=30
   * 接口文档：§9.7.2
   */
  getUserGrowth: (days: number) =>
    request.get<unknown, { trend: UserGrowthPoint[]; grade_distribution: unknown[]; subject_preference: unknown[]; retention_funnel: unknown }>(
      '/dashboard/user-growth',
      { params: { days } }
    ),

  /**
   * 五力测试分析（用于主看板薄弱分布柱状图）
   * GET /api/v1/admin/dashboard/five-force-analysis?days=30
   * 接口文档：§9.7.3
   */
  getFiveForceAnalysis: (days: number) =>
    request.get<unknown, Record<string, unknown>>(
      '/dashboard/five-force-analysis',
      { params: { days } }
    ),

  /**
   * 训练分析（正确率趋势、完成率分布、知识点热度）
   * GET /api/v1/admin/dashboard/training-analysis?days=30
   * 接口文档：§9.7.4
   */
  getTrainingAnalysis: (days: number) =>
    request.get<unknown, Record<string, unknown>>(
      '/dashboard/training-analysis',
      { params: { days } }
    ),

  /**
   * AI助教效果分析（理解突破、策略有效性、对话量趋势）
   * GET /api/v1/admin/dashboard/ai-teaching-analysis?days=30
   * 接口文档：§9.7.5
   */
  getAiTeachingAnalysis: (days: number) =>
    request.get<unknown, Record<string, unknown>>(
      '/dashboard/ai-teaching-analysis',
      { params: { days } }
    ),

  /**
   * 错题集分析（复盘状态分布、五力错题分布、高频错题 Top 10）
   * GET /api/v1/admin/dashboard/error-questions-analysis?days=30
   * 接口文档：§9.7.6
   */
  getErrorQuestionsAnalysis: (days: number) =>
    request.get<unknown, Record<string, unknown>>(
      '/dashboard/error-questions-analysis',
      { params: { days } }
    ),

  /**
   * 题库健康度看板（各状态分布、标注进度、向量化进度）
   * GET /api/v1/admin/dashboard/question-bank-health
   * 接口文档：§9.7.7
   */
  getQuestionBankHealth: () =>
    request.get<unknown, Record<string, unknown>>('/dashboard/question-bank-health'),

  /**
   * Token 消耗统计（按日 + 按模块，含成本告警）
   * GET /api/v1/admin/dashboard/token-trend?days=30
   * 接口文档：§9.7.8
   */
  getTokenTrend: (days: number) =>
    request.get<unknown, { summary: unknown; daily_data: TokenTrend[]; downgrade_stats: unknown }>(
      '/dashboard/token-trend',
      { params: { days } }
    ),

  /**
   * 用户增长详情（注册趋势、留存漏斗、年级分布、学科偏好）
   * 用于「用户规模」KPI卡片跳转后的详细分析页
   * GET /api/v1/admin/dashboard/user-growth-detail?days=30
   * 接口文档：§9.7.9
   */
  getUserGrowthDetail: (days: number) =>
    request.get<unknown, Record<string, unknown>>(
      '/dashboard/user-growth-detail',
      { params: { days } }
    ),
}

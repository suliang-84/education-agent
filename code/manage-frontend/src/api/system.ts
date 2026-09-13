/**
 * 系统参数配置接口模块
 * 接口文档：§9.5（系统参数配置）、§9.6（启发策略管理）
 *
 * 系统参数支持热更新（无需重启服务）
 * 启发策略共9种，可调整优先级和启用/禁用状态
 */
import request from './request'
import type { SystemConfig, Strategy } from '@/types'

// ── 系统参数接口 ─────────────────────────────────────────────

export const systemConfigApi = {
  /**
   * 获取所有系统配置参数列表
   * GET /api/v1/admin/system-configs
   * 接口文档：§9.5.1
   */
  getList: () =>
    request.get<unknown, { configs: SystemConfig[] }>('/system-configs'),

  /**
   * 更新单个系统参数（热更新，修改后立即生效无需重启）
   * PATCH /api/v1/admin/system-configs/{key}
   * 接口文档：§9.5.2
   */
  update: (key: string, value: string) =>
    request.patch<unknown, { key: string; old_value: string; new_value: string; updated_at: string }>(
      `/system-configs/${key}`,
      { value }
    ),
}

// ── 启发策略接口 ─────────────────────────────────────────────

export const strategyApi = {
  /**
   * 获取全部启发策略列表（9种苏格拉底式策略）
   * GET /api/v1/admin/strategies
   * 接口文档：§9.6.1
   */
  getList: () =>
    request.get<unknown, { list: Strategy[] }>('/strategies'),

  /**
   * 更新策略配置（优先级、描述、启用状态）
   * PATCH /api/v1/admin/strategies/{strategy_id}
   * 接口文档：§9.6.2
   */
  update: (strategyId: string, data: {
    default_priority?: number
    description?: string
    is_active?: boolean
  }) =>
    request.patch<unknown, Strategy>(`/strategies/${strategyId}`, data),

  /**
   * 批量调整策略优先级顺序
   * POST /api/v1/admin/strategies/reorder
   * （本地扩展，接口文档未单独列出）
   */
  reorder: (orders: Array<{ id: number; priority: number }>) =>
    request.post('/strategies/reorder', { orders }),
}

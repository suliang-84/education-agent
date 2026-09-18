/**
 * 审计日志接口模块
 * 接口文档：§9.9
 *
 * 所有写操作（题目管理、用户管理、参数配置等）由后端自动写入 admin_audit_logs
 * 本模块提供日志查询接口，供管理员追溯操作记录
 */
import request from './request'
import type { AuditLog, PaginatedResponse } from '@/types'

export const auditLogApi = {
  /**
   * 查询审计日志列表（多条件过滤，时间倒序，页码分页）
   * GET /api/v1/admin/audit-logs?admin_id=1&action=CONFIRM_ANNOTATION&page=1&limit=20
   * 接口文档：§9.9.1
   */
  getList: (params: {
    admin_id?: number      // 按操作人筛选
    action?: string        // 操作类型，如 CONFIRM_ANNOTATION、PUBLISH_QUESTION
    start_time?: string    // 开始时间（ISO 8601）
    end_time?: string      // 结束时间（ISO 8601）
    page?: number
    limit?: number
  }) =>
    request.get<unknown, PaginatedResponse<AuditLog>>('/audit-logs', { params }),

  /**
   * 查询单条审计日志详情（含操作前后数据对比）
   * GET /api/v1/admin/audit-logs/{log_id}
   */
  getOne: (logId: number) =>
    request.get<unknown, AuditLog>(`/audit-logs/${logId}`),
}

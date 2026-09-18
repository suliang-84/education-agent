/**
 * 公共接口模块
 * 包含：认证登录（POST /auth/login、/auth/logout）
 *       健康检查（GET /health）
 * 接口文档：§1、§2（管理后台认证部分）、§9.10
 */
import request from './request'

// ── 认证接口 ─────────────────────────────────────────────────

export const authApi = {
  /**
   * 账号 + 密码登录，验证通过后直接返回 access_token（8小时有效）
   * POST /api/v1/admin/auth/login
   */
  login: (data: { username: string; password: string }) =>
    request.post<unknown, { access_token: string; admin: { id: number; username: string; display_name: string; role: string } }>('/auth/login', data),

  /**
   * 退出登录，吊销当前 Token
   * POST /api/v1/admin/auth/logout
   */
  logout: () =>
    request.post('/auth/logout'),
}

// ── 健康检查 ─────────────────────────────────────────────────

export const healthApi = {
  /**
   * 服务健康检查（无需 Token）
   * GET /health
   */
  check: () =>
    request.get<unknown, { status: string; checks: Record<string, string>; timestamp: string }>('/health'),
}

/**
 * 公共接口模块
 * 包含：认证登录（POST /auth/login、/auth/verify-2fa、/auth/logout）
 *       健康检查（GET /health）
 * 接口文档：§1、§2（管理后台认证部分）、§9.10
 */
import request from './request'

// ── 认证接口 ─────────────────────────────────────────────────

export const authApi = {
  /**
   * Step 1：账号 + 密码登录，返回短暂有效的 session_token（用于2FA）
   * POST /api/v1/admin/auth/login
   */
  login: (data: { username: string; password: string }) =>
    request.post<unknown, { session_token: string }>('/auth/login', data),

  /**
   * Step 2：短信验证码二次认证，返回正式 access_token（8小时有效）
   * POST /api/v1/admin/auth/verify-2fa
   */
  verify2fa: (data: { session_token: string; code: string }) =>
    request.post<unknown, { access_token: string; admin: { id: number; username: string; role: string } }>('/auth/verify-2fa', data),

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

/**
 * 用户管理接口模块
 * 接口文档：§9.8
 *
 * v1.2.0：原"学生管理"扩展为"用户管理"，新增家长列表、管理员列表、
 *          绑定/解绑管理、学生知识点练习统计、AI助教提示词摘要等接口
 *
 * 包含：
 * - 学生管理（9.8.1、9.8.7~9.8.14）
 * - 家长管理（9.8.2、9.8.8~9.8.9）
 * - 管理员账号管理（9.8.3~9.8.6）
 */
import request from './request'
import type {
  Student, StudentDetail, Parent, AdminUser, AuditLog,
  StudentKpStat, StudentAiPromptSummary, PromptInsightEntry,
  PaginatedResponse,
} from '@/types'

// ── 学生管理 ─────────────────────────────────────────────────

export const studentApi = {
  /**
   * 学生列表（多条件搜索，页码分页）
   * GET /api/v1/admin/students
   * 接口文档：§9.8.1
   */
  getList: (params: {
    grade?: string          // G7~G12
    has_profile?: boolean
    keyword?: string        // 模糊搜索昵称或手机号
    page?: number
    limit?: number
  }) =>
    request.get<unknown, PaginatedResponse<Student>>('/students', { params }),

  /**
   * 学生画像详情（六大维度：基础信息/五力画像/学习行为/AI互动/错题画像/成长轨迹）
   * GET /api/v1/admin/students/{student_id}?date_range=30d
   * 接口文档：§9.8.7
   */
  getOne: (studentId: number, params?: { date_range?: '7d' | '30d' | 'all' }) =>
    request.get<unknown, StudentDetail>(`/students/${studentId}`, { params }),

  /**
   * 管理员绑定家长到学生
   * 按手机号查找家长账号，不存在则自动创建（is_confirmed=false）并发送激活短信
   * POST /api/v1/admin/students/{student_id}/bind-parent
   * 接口文档：§9.8.8
   */
  bindParent: (studentId: number, data: { parent_phone: string }) =>
    request.post<unknown, { binding_id: number; parent_id: number; parent_created: boolean }>(
      `/students/${studentId}/bind-parent`,
      data
    ),

  /**
   * 从学生维度解除家长绑定（软删除，保留历史记录）
   * POST /api/v1/admin/students/{student_id}/unbind-parent
   * 接口文档：§9.8.9（接口A）
   */
  unbindParent: (studentId: number, parentId: number) =>
    request.post(`/students/${studentId}/unbind-parent`, { parent_id: parentId }),

  /**
   * 学生知识点练习统计（管理员视角）
   * 按当前年级+学期，统计各知识点练习题数和错误率（≥5题才统计错误率）
   * GET /api/v1/admin/students/{student_id}/kp-stats
   * 接口文档：§9.8.10
   */
  getKpStats: (studentId: number, params?: { subject_code?: string; only_valid?: boolean }) =>
    request.get<unknown, { student_id: number; nickname: string; grade: string; semester: string; stat_summary: unknown; subjects: { subject_code: string; subject_name: string; knowledge_points: StudentKpStat[] }[] }>(
      `/students/${studentId}/kp-stats`,
      { params }
    ),

  /**
   * 获取学生 AI 助教提示词摘要（学习信息摘要 + 个人洞察摘要 + Prompt 预览）
   * GET /api/v1/admin/students/{student_id}/ai-prompt-summary
   * 接口文档：§9.8.11
   */
  getAiPromptSummary: (studentId: number) =>
    request.get<unknown, StudentAiPromptSummary>(`/students/${studentId}/ai-prompt-summary`),

  /**
   * 管理员手动编辑个人洞察摘要
   * PUT /api/v1/admin/students/{student_id}/ai-prompt-summary
   * 接口文档：§9.8.12
   */
  updateAiPromptSummary: (studentId: number, data: { personal_insight: string }) =>
    request.put<unknown, { updated_at: string; updated_by: string }>(
      `/students/${studentId}/ai-prompt-summary`,
      data
    ),

  /**
   * 管理员手动新增洞察条目
   * POST /api/v1/admin/students/{student_id}/prompt-insights
   * 接口文档：§9.8.13
   */
  addInsightEntry: (studentId: number, data: {
    content: string
    insight_type?: 'interest' | 'mood' | 'life_event' | 'analogy_pref' | 'family' | 'learning_attitude' | 'other'
    is_sensitive?: boolean
  }) =>
    request.post<unknown, PromptInsightEntry>(`/students/${studentId}/prompt-insights`, data),

  /**
   * 获取洞察条目历史记录
   * GET /api/v1/admin/students/{student_id}/prompt-insights
   * （本地扩展，配合 getAiPromptSummary 使用）
   */
  getInsightEntries: (studentId: number) =>
    request.get<unknown, PromptInsightEntry[]>(`/students/${studentId}/prompt-insights`),

  /**
   * 重新生成学习信息摘要（异步任务，约10秒）
   * POST /api/v1/admin/students/{student_id}/ai-prompt-summary/regenerate
   * 接口文档：§9.8.14
   */
  // 别名保持与视图层一致
  regenerateLearningsummary: (studentId: number) =>
    request.post<unknown, { task_id: string }>(
      `/students/${studentId}/ai-prompt-summary/regenerate`
    ),

  regenerateLearningsSummary: (studentId: number) =>
    request.post<unknown, { task_id: string }>(
      `/students/${studentId}/ai-prompt-summary/regenerate`
    ),
}

// ── 家长管理 ─────────────────────────────────────────────────

export const parentApi = {
  /**
   * 家长列表（含已绑定学生信息）
   * GET /api/v1/admin/parents?keyword=&page=1&limit=20
   * 接口文档：§9.8.2
   */
  getList: (params: { keyword?: string; page?: number; limit?: number }) =>
    request.get<unknown, PaginatedResponse<Parent>>('/parents', { params }),

  /**
   * 从家长维度解除绑定（软删除）
   * POST /api/v1/admin/parents/{parent_id}/unbind
   * 接口文档：§9.8.9（接口B）
   */
  unbind: (parentId: number, studentId: number) =>
    request.post(`/parents/${parentId}/unbind`, { student_id: studentId }),
}

// ── 管理员账号管理 ───────────────────────────────────────────

export const adminUserApi = {
  /**
   * 管理员账号列表（页码分页）
   * GET /api/v1/admin/admin-users?page=1&limit=20
   * 接口文档：§9.8.3
   */
  getList: (params?: { page?: number; limit?: number }) =>
    request.get<unknown, PaginatedResponse<AdminUser>>('/admin-users', { params }),

  /**
   * 创建管理员账号（系统自动生成初始密码发送至手机，首次登录必须修改）
   * POST /api/v1/admin/admin-users
   * 接口文档：§9.8.4
   */
  create: (data: { username: string; display_name: string; phone: string; email?: string; password: string; role?: string }) =>
    request.post<unknown, { id: number; username: string }>('/admin-users', data),

  /**
   * 启用 / 停用管理员账号
   * 停用后当前 Token 立即失效；不得停用自己的账号
   * PUT /api/v1/admin/admin-users/{admin_id}/status
   * 接口文档：§9.8.5
   * is_active: 0=停用, 1=启用
   */
  setActive: (adminId: number, isActive: 0 | 1) =>
    request.put(`/admin-users/${adminId}/status`, { is_active: isActive }),

  /**
   * 重置管理员密码（固定重置为 123456）
   * POST /api/v1/admin/admin-users/{admin_id}/reset-password
   * 接口文档：§9.8.6
   */
  resetPassword: (adminId: number) =>
    request.post(`/admin-users/${adminId}/reset-password`),

  /**
   * 删除管理员账号（软删除，仅 is_active=0 停用状态可删，不可删除自己）
   * DELETE /api/v1/admin/admin-users/{admin_id}
   * 接口文档：§9.8.7
   */
  delete: (adminId: number) =>
    request.delete(`/admin-users/${adminId}`),
}

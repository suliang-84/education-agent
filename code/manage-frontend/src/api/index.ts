import request from './request'
import type {
  Question, CognitiveQuestion, TrainingConfig, GlobalAlgoConfig, DimensionTrainingConfig, TrainingMode,
  SystemConfig, Strategy, Student, StudentDetail, Parent, AdminUser, AuditLog,
  StudentKpStat, StudentAiPromptSummary, PromptInsightEntry,
  DashboardStats, TokenTrend, UserGrowthPoint, PaginatedResponse
} from '@/types'

// 认证
export const authApi = {
  login: (data: { username: string; password: string }) =>
    request.post<unknown, { session_token: string }>('/auth/login', data),
  verify2fa: (data: { session_token: string; code: string }) =>
    request.post<unknown, { access_token: string; admin: { id: number; username: string; role: string } }>('/auth/verify-2fa', data),
  logout: () => request.post('/auth/logout'),
}

// 题库管理（v1.2.0：新增 analyze / reject 接口，撤销独立标注审核）
export const questionApi = {
  getList: (params: Record<string, unknown>) =>
    request.get<unknown, PaginatedResponse<Question>>('/questions', { params }),
  getOne: (id: number) =>
    request.get<unknown, Question>(`/questions/${id}`),
  // 录入题干（仅 stem + image_url）
  create: (data: Pick<Question, 'stem'> & { image_url?: string }) =>
    request.post<unknown, Question>('/questions', data),
  // 触发大模型分析（draft → analyzing → pending_review）
  analyze: (id: number) =>
    request.post<unknown, Question>(`/questions/${id}/analyze`),
  // 更新审核结果字段（pending_review 状态可修改）
  update: (id: number, data: Partial<Question>) =>
    request.put<unknown, Question>(`/questions/${id}`, data),
  // 发布（pending_review → published，触发向量化）
  publish: (id: number) =>
    request.post<unknown, Question>(`/questions/${id}/publish`),
  // 驳回并重新分析（pending_review → analyzing）
  reject: (id: number, data: { rejection_reason: string }) =>
    request.post<unknown, Question>(`/questions/${id}/reject`, data),
  // 下架（published → archived）
  archive: (id: number) =>
    request.post<unknown, Question>(`/questions/${id}/archive`),
  // 软删除（仅 draft 状态）
  delete: (id: number) =>
    request.delete(`/questions/${id}`),
  // 批量导入题干列表，每条自动触发分析
  batchImport: (stems: string[]) =>
    request.post('/questions/batch-import', { stems }),
}

// 五力测试题维护
export const cognitiveApi = {
  getList: (params?: Record<string, unknown>) =>
    request.get<unknown, CognitiveQuestion[]>('/cognitive-questions', { params }),
  create: (data: Partial<CognitiveQuestion>) =>
    request.post<unknown, CognitiveQuestion>('/cognitive-questions', data),
  update: (id: number, data: Partial<CognitiveQuestion>) =>
    request.put<unknown, CognitiveQuestion>(`/cognitive-questions/${id}`, data),
  publish: (id: number) =>
    request.post<unknown, CognitiveQuestion>(`/cognitive-questions/${id}/publish`),
  archive: (id: number) =>
    request.post<unknown, CognitiveQuestion>(`/cognitive-questions/${id}/archive`),
  delete: (id: number) =>
    request.delete(`/cognitive-questions/${id}`),
}

// 训练配置（v2.0：全局算法参数 + 五维度参数独立版本化）
export const trainingConfigApi = {
  // 全局算法参数
  getGlobalList: () =>
    request.get<unknown, GlobalAlgoConfig[]>('/training-configs/global'),
  getGlobalActive: () =>
    request.get<unknown, GlobalAlgoConfig>('/training-configs/global/active'),
  createGlobal: (data: Partial<GlobalAlgoConfig>) =>
    request.post<unknown, GlobalAlgoConfig>('/training-configs/global', data),

  // 各维度训练参数
  getDimensionList: (mode: TrainingMode) =>
    request.get<unknown, DimensionTrainingConfig[]>(`/training-configs/dimension/${mode}`),
  getDimensionActive: (mode: TrainingMode) =>
    request.get<unknown, DimensionTrainingConfig>(`/training-configs/dimension/${mode}/active`),
  createDimension: (mode: TrainingMode, data: Partial<DimensionTrainingConfig>) =>
    request.post<unknown, DimensionTrainingConfig>(`/training-configs/dimension/${mode}`, data),

  // 兼容旧接口
  getList: () =>
    request.get<unknown, TrainingConfig[]>('/training-configs'),
  getActive: () =>
    request.get<unknown, TrainingConfig>('/training-configs/active'),
  create: (data: Partial<TrainingConfig>) =>
    request.post<unknown, TrainingConfig>('/training-configs', data),
}

// 系统参数
export const systemConfigApi = {
  getList: () =>
    request.get<unknown, SystemConfig[]>('/system-configs'),
  update: (key: string, value: string) =>
    request.put(`/system-configs/${key}`, { value }),
}

// 启发策略
export const strategyApi = {
  getList: () =>
    request.get<unknown, Strategy[]>('/strategies'),
  update: (id: number, data: Partial<Strategy>) =>
    request.put<unknown, Strategy>(`/strategies/${id}`, data),
  reorder: (orders: Array<{ id: number; priority: number }>) =>
    request.post('/strategies/reorder', { orders }),
}

// 学生管理
export const studentApi = {
  getList: (params: Record<string, unknown>) =>
    request.get<unknown, PaginatedResponse<Student>>('/students', { params }),
  getOne: (id: number) =>
    request.get<unknown, StudentDetail>(`/students/${id}`),
  bindParent: (studentId: number, data: { parent_phone: string }) =>
    request.post(`/students/${studentId}/bind-parent`, data),
  unbindParent: (studentId: number, parentId: number) =>
    request.post(`/students/${studentId}/unbind-parent`, { parent_id: parentId }),
  // 知识点练习统计
  getKpStats: (studentId: number, params?: { subject?: string }) =>
    request.get<unknown, StudentKpStat[]>(`/students/${studentId}/kp-stats`, { params }),
  // AI助教提示词摘要
  getAiPromptSummary: (studentId: number) =>
    request.get<unknown, StudentAiPromptSummary>(`/students/${studentId}/ai-prompt-summary`),
  updateAiPromptSummary: (studentId: number, data: { personal_insight: string }) =>
    request.put<unknown, StudentAiPromptSummary>(`/students/${studentId}/ai-prompt-summary`, data),
  regenerateLearningsummary: (studentId: number) =>
    request.post<unknown, { message: string }>(`/students/${studentId}/ai-prompt-summary/regenerate`),
  // 个人洞察条目
  getInsightEntries: (studentId: number) =>
    request.get<unknown, PromptInsightEntry[]>(`/students/${studentId}/prompt-insights`),
  addInsightEntry: (studentId: number, data: { content: string }) =>
    request.post<unknown, PromptInsightEntry>(`/students/${studentId}/prompt-insights`, data),
}

// 家长管理
export const parentApi = {
  getList: (params: Record<string, unknown>) =>
    request.get<unknown, PaginatedResponse<Parent>>('/parents', { params }),
  unbind: (parentId: number, studentId: number) =>
    request.post(`/parents/${parentId}/unbind`, { student_id: studentId }),
}

// 管理员账号管理
export const adminUserApi = {
  getList: () =>
    request.get<unknown, AdminUser[]>('/admin-users'),
  create: (data: { username: string; display_name: string; phone: string; email?: string }) =>
    request.post<unknown, AdminUser>('/admin-users', data),
  setActive: (id: number, is_active: boolean) =>
    request.put(`/admin-users/${id}/status`, { is_active }),
  resetPassword: (id: number) =>
    request.post(`/admin-users/${id}/reset-password`),
}

// 审计日志
export const auditLogApi = {
  getList: (params: Record<string, unknown>) =>
    request.get<unknown, PaginatedResponse<AuditLog>>('/audit-logs', { params }),
  getOne: (id: number) =>
    request.get<unknown, AuditLog>(`/audit-logs/${id}`),
}

// 数据看板
export const dashboardApi = {
  getStats: (date?: string) =>
    request.get<unknown, DashboardStats>('/dashboard/stats', { params: { date } }),
  getUserGrowth: (days: number) =>
    request.get<unknown, UserGrowthPoint[]>('/dashboard/user-growth', { params: { days } }),
  getTokenTrend: (days: number) =>
    request.get<unknown, TokenTrend[]>('/dashboard/token-trend', { params: { days } }),
}

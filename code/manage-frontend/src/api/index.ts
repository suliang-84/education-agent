import request from './request'
import type {
  Question, Annotation, CognitiveQuestion, TrainingConfig,
  SystemConfig, Strategy, Student, StudentDetail, Parent, AdminUser, AuditLog,
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

// 题库管理
export const questionApi = {
  getList: (params: Record<string, unknown>) =>
    request.get<unknown, PaginatedResponse<Question>>('/questions', { params }),
  getOne: (id: number) =>
    request.get<unknown, Question>(`/questions/${id}`),
  create: (data: Partial<Question>) =>
    request.post<unknown, Question>('/questions', data),
  update: (id: number, data: Partial<Question>) =>
    request.put<unknown, Question>(`/questions/${id}`, data),
  publish: (id: number) =>
    request.post<unknown, Question>(`/questions/${id}/publish`),
  archive: (id: number) =>
    request.post<unknown, Question>(`/questions/${id}/archive`),
  delete: (id: number) =>
    request.delete(`/questions/${id}`),
  batchImport: (data: Partial<Question>[]) =>
    request.post('/questions/batch-import', data),
}

// AI标注审核
export const annotationApi = {
  getList: (params: Record<string, unknown>) =>
    request.get<unknown, PaginatedResponse<Annotation>>('/annotations', { params }),
  confirm: (id: number, data: { confirmed_primary_power: string }) =>
    request.post(`/annotations/${id}/confirm`, data),
  batchConfirm: (min_confidence: number) =>
    request.post('/annotations/batch-confirm', { min_confidence }),
  reject: (id: number) =>
    request.post(`/annotations/${id}/reject`),
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

// 训练配置
export const trainingConfigApi = {
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

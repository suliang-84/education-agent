/**
 * API 模块 - 使用 Axios 拦截器实现 Mock
 * 所有接口返回 Promise，符合真实 API 结构，可无缝切换真实后端
 */
import type {
  ApiResponse, PageData, LoginStep1Response, LoginStep2Response,
  Question, Annotation, CognitiveQuestion, TrainingConfigVersion,
  SystemConfig, Strategy, DashboardOverview, TokenUsage,
  Student, StudentDetail, AuditLog,
} from '../types'
import {
  mockQuestions, mockAnnotations, mockCognitiveQuestions,
  mockTrainingConfig, mockTrainingConfigHistory,
  mockSystemConfigs, mockStrategies, mockDashboard, mockTokenUsage,
  mockStudents, mockStudentDetail, mockAuditLogs,
} from './mock-data'

// Mock 延迟工具
const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

// 统一成功响应包装
function ok<T>(data: T, msg = '操作成功'): ApiResponse<T> {
  return { status: 'success', code: 0, msg, data }
}

// ==================== Auth 接口 ====================
export const authApi = {
  async login(username: string, password: string): Promise<ApiResponse<LoginStep1Response>> {
    await delay(500)
    if (username === 'admin001' && password === 'admin123') {
      return ok({
        two_fa_required: true,
        phone_masked: '138****8000',
        session_token: 'mock_2fa_session_token_xxx',
      }, '密码验证成功，请完成短信验证')
    }
    return { status: 'fail', code: 1001, msg: '用户名或密码错误', data: null as any }
  },

  async verify2fa(smsCode: string, _sessionToken: string): Promise<ApiResponse<LoginStep2Response>> {
    await delay(400)
    if (smsCode === '123456' || smsCode.length === 6) {
      return ok({
        access_token: 'mock_access_token_eyJ_admin001',
        access_expires_in: 28800,
        admin_info: {
          admin_id: 1,
          username: 'admin001',
          display_name: '系统管理员',
          role: 'SUPER_ADMIN',
          password_expired: false,
        },
      }, '登录成功')
    }
    return { status: 'fail', code: 1002, msg: '验证码错误', data: null as any }
  },
}

// ==================== 题目管理接口 ====================
export const questionsApi = {
  async getList(params?: Record<string, unknown>): Promise<ApiResponse<PageData<Question>>> {
    await delay()
    let list = [...mockQuestions]

    if (params?.primary_power) {
      list = list.filter(q => q.primary_power === params.primary_power)
    }
    if (params?.difficulty) {
      list = list.filter(q => q.difficulty === params.difficulty)
    }
    if (params?.status) {
      list = list.filter(q => q.status === params.status)
    }
    if (params?.keyword) {
      list = list.filter(q => q.stem.includes(params.keyword as string))
    }

    return ok({ list, total: list.length, has_more: false, next_cursor: null })
  },

  async create(_data: Record<string, unknown>): Promise<ApiResponse<{ question_id: number; status: string }>> {
    await delay(600)
    const newId = 5000 + mockQuestions.length + 1
    return ok({ question_id: newId, status: 'draft', embedding_status: 'pending', annotation_status: 'pending' }, '题目创建成功，已触发AI标注')
  },

  async update(questionId: number, data: Record<string, unknown>): Promise<ApiResponse<{ question_id: number; updated_fields: string[] }>> {
    await delay()
    return ok({ question_id: questionId, updated_fields: Object.keys(data) }, '题目已更新')
  },

  async updateStatus(questionId: number, status: string): Promise<ApiResponse<{ question_id: number; status: string }>> {
    await delay()
    const q = mockQuestions.find(q => q.question_id === questionId)
    if (q) q.status = status as any
    return ok({ question_id: questionId, status, embedding_triggered: status === 'published' }, '状态更新成功')
  },

  async delete(questionId: number): Promise<ApiResponse<null>> {
    await delay()
    const idx = mockQuestions.findIndex(q => q.question_id === questionId)
    if (idx >= 0) mockQuestions.splice(idx, 1)
    return ok(null, '题目已删除')
  },
}

// ==================== AI标注审核接口 ====================
export const annotationsApi = {
  async getList(params?: Record<string, unknown>): Promise<ApiResponse<PageData<Annotation>>> {
    await delay()
    let list = [...mockAnnotations]
    if (params?.annotation_status) {
      list = list.filter(a => a.annotation_status === params.annotation_status)
    }
    if (params?.confidence_min) {
      list = list.filter(a => a.ai_annotation.confidence >= Number(params.confidence_min))
    }
    if (params?.confidence_max) {
      list = list.filter(a => a.ai_annotation.confidence <= Number(params.confidence_max))
    }
    return ok({ list, total: list.length, has_more: false, next_cursor: null })
  },

  async confirm(annotationId: number, _data: Record<string, unknown>): Promise<ApiResponse<{ annotation_id: number; annotation_status: string }>> {
    await delay()
    const a = mockAnnotations.find(a => a.annotation_id === annotationId)
    if (a) a.annotation_status = 'confirmed'
    return ok({ annotation_id: annotationId, annotation_status: 'confirmed', confirmed_at: new Date().toISOString() }, '标注已确认')
  },

  async batchConfirm(annotationIds: number[], threshold: number): Promise<ApiResponse<{ confirmed_count: number; skipped_count: number }>> {
    await delay(800)
    let confirmed = 0
    let skipped = 0
    for (const id of annotationIds) {
      const a = mockAnnotations.find(a => a.annotation_id === id)
      if (a && a.ai_annotation.confidence >= threshold) {
        a.annotation_status = 'confirmed'
        confirmed++
      } else {
        skipped++
      }
    }
    return ok({ confirmed_count: confirmed, skipped_count: skipped }, '批量确认成功')
  },
}

// ==================== 五力测试题接口 ====================
export const cognitiveApi = {
  async getList(): Promise<ApiResponse<{ list: CognitiveQuestion[] }>> {
    await delay()
    return ok({ list: [...mockCognitiveQuestions] })
  },

  async update(id: number, data: Record<string, unknown>): Promise<ApiResponse<{ id: number }>> {
    await delay()
    const q = mockCognitiveQuestions.find(q => q.id === id)
    if (q) Object.assign(q, data)
    return ok({ id }, '测试题已更新')
  },
}

// ==================== 训练配置接口 ====================
export const trainingConfigApi = {
  async getActive(): Promise<ApiResponse<TrainingConfigVersion>> {
    await delay()
    return ok(mockTrainingConfig)
  },

  async getHistory(): Promise<ApiResponse<{ list: TrainingConfigVersion[] }>> {
    await delay()
    return ok({ list: mockTrainingConfigHistory })
  },

  async create(_data: { config: Record<string, unknown>; description: string }): Promise<ApiResponse<{ version_id: number; version_number: string; is_active: boolean }>> {
    await delay(800)
    const newVersion = mockTrainingConfigHistory.length + 1
    return ok({ version_id: newVersion, version_number: `v${newVersion}`, is_active: true }, '新配置已生效')
  },
}

// ==================== 系统参数接口 ====================
export const systemConfigApi = {
  async getList(): Promise<ApiResponse<{ configs: SystemConfig[] }>> {
    await delay()
    return ok({ configs: [...mockSystemConfigs] })
  },

  async update(key: string, value: string): Promise<ApiResponse<{ key: string; old_value: string; new_value: string }>> {
    await delay()
    const cfg = mockSystemConfigs.find(c => c.key === key)
    const oldValue = cfg?.value || ''
    if (cfg) cfg.value = value
    return ok({ key, old_value: oldValue, new_value: value, updated_at: new Date().toISOString() }, '参数已更新，立即生效（无需重启）')
  },
}

// ==================== 启发策略接口 ====================
export const strategiesApi = {
  async getList(): Promise<ApiResponse<{ list: Strategy[] }>> {
    await delay()
    return ok({ list: [...mockStrategies].sort((a, b) => a.default_priority - b.default_priority) })
  },

  async update(strategyId: string, data: Partial<Strategy>): Promise<ApiResponse<{ strategy_id: string }>> {
    await delay()
    const s = mockStrategies.find(s => s.strategy_id === strategyId)
    if (s) Object.assign(s, data)
    return ok({ strategy_id: strategyId }, '策略已更新')
  },
}

// ==================== 数据看板接口 ====================
export const dashboardApi = {
  async getOverview(): Promise<ApiResponse<DashboardOverview>> {
    await delay()
    return ok(mockDashboard)
  },

  async getTokenUsage(_params?: Record<string, unknown>): Promise<ApiResponse<TokenUsage>> {
    await delay()
    return ok(mockTokenUsage)
  },
}

// ==================== 学生管理接口 ====================
export const studentsApi = {
  async getList(params?: Record<string, unknown>): Promise<ApiResponse<PageData<Student>>> {
    await delay()
    let list = [...mockStudents]
    if (params?.grade) list = list.filter(s => s.grade === params.grade)
    if (params?.keyword) list = list.filter(s => s.nickname.includes(params.keyword as string))
    if (params?.has_profile === 'true') list = list.filter(s => s.has_five_power_profile)
    return ok({ list, total: list.length, has_more: false, next_cursor: null })
  },

  async getDetail(_studentId: number): Promise<ApiResponse<StudentDetail>> {
    await delay()
    return ok(mockStudentDetail)
  },

  async bindParent(_studentId: number, _parentId: number): Promise<ApiResponse<{ binding_id: number }>> {
    await delay()
    return ok({ binding_id: 101 }, '绑定成功')
  },
}

// ==================== 审计日志接口 ====================
export const auditLogsApi = {
  async getList(params?: Record<string, unknown>): Promise<ApiResponse<PageData<AuditLog>>> {
    await delay()
    let list = [...mockAuditLogs]
    if (params?.action) list = list.filter(l => l.action === params.action)
    if (params?.admin_id) list = list.filter(l => l.admin_id === Number(params.admin_id))
    return ok({ list, total: list.length, has_more: false, next_cursor: null })
  },
}

// ==================== 别名导出（兼容视图中的导入名称）====================
export const questionApi = {
  list: (primary_power?: string, difficulty?: string, status?: string, page = 1, size = 15) =>
    questionsApi.getList({ primary_power, difficulty, status, page, size }),
  create: (data: Record<string, unknown>) => questionsApi.create(data),
  update: (id: number, data: Record<string, unknown>) => questionsApi.update(id, data),
  updateStatus: (id: number, status: string) => questionsApi.updateStatus(id, status),
  delete: (id: number) => questionsApi.delete(id),
}

export const annotationApi = {
  list: (status?: string, min_conf?: number, max_conf?: number, page = 1, size = 15) =>
    annotationsApi.getList({ annotation_status: status, confidence_min: min_conf, confidence_max: max_conf, page, size }),
  confirm: (id: number, confirmed_primary: string, confirmed_secondary?: string) =>
    annotationsApi.confirm(id, { confirmed_primary, confirmed_secondary }),
  batchConfirm: (ids: number[], threshold = 0.85) =>
    annotationsApi.batchConfirm(ids, threshold),
}

export const strategyApi = {
  list: () => strategiesApi.getList(),
  update: (id: string, data: Record<string, unknown>) => strategiesApi.update(id, data),
}

export const studentApi = {
  list: (grade?: string, has_profile?: boolean, keyword?: string, page = 1, size = 15) =>
    studentsApi.getList({ grade, has_profile, keyword, page, size }),
  detail: (id: number) => studentsApi.getDetail(id),
  bindParent: (studentId: number, parentId: number) => studentsApi.bindParent(studentId, parentId),
}

export const auditApi = {
  list: (action?: string, page = 1, size = 20) =>
    auditLogsApi.getList({ action, page, size }),
}

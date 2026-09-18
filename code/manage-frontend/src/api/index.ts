/**
 * API 统一导出入口
 *
 * 目录结构（按模块独立管理）：
 * ├── request.ts          Axios 实例（拦截器、Token 注入、401 处理）
 * ├── common.ts           公共接口：认证（login/verify2fa/logout）、健康检查
 * ├── questions.ts        题库管理：知识体系树、题目 CRUD、分析、发布、驳回
 * ├── cognitive.ts        五力测试题维护：新增、编辑、状态变更（发布/下架）、删除
 * ├── training.ts         训练参数配置：各维度参数版本管理
 * ├── system.ts           系统参数配置 + 启发策略管理
 * ├── dashboard.ts        数据看板：概览指标、各分析子页接口
 * ├── users.ts            用户管理：学生、家长、管理员
 * └── audit.ts            审计日志
 *
 * 接口文档：/docs/4.架构设计/06_接口设计说明书.md §9
 * Base URL：/api/v1/admin（由 request.ts 配置）
 */

// ── 公共接口 ─────────────────────────────────────────────────
export { authApi, healthApi } from './common'

// ── 题库管理 ─────────────────────────────────────────────────
export { knowledgeTreeApi, questionApi } from './questions'
export type { KnowledgeTreeNode, KnowledgeTreeResponse, QuestionListParams, PublishPayload } from './questions'

// ── 五力测试题维护 ───────────────────────────────────────────
export { cognitiveApi } from './cognitive'
export type { CognitiveListResponse, StatusChangeResponse, CognitiveAnswerInput, CognitiveQuestionInput } from './cognitive'

// ── 训练参数配置 ─────────────────────────────────────────────
export { trainingApi, trainingConfigApi } from './training'
export type { TrainingDimension, DimensionConfigInput } from './training'

// ── 系统参数 + 启发策略 ──────────────────────────────────────
export { systemConfigApi, strategyApi } from './system'

// ── 数据看板 ─────────────────────────────────────────────────
export { dashboardApi } from './dashboard'

// ── 用户管理 ─────────────────────────────────────────────────
export { studentApi, parentApi, adminUserApi } from './users'

// ── 审计日志 ─────────────────────────────────────────────────
export { auditLogApi } from './audit'

/**
 * @deprecated §9.2 AI标注审核已合并入题库管理（v2.1废弃）
 * AnnotationView.vue 为历史遗留页面，保留空对象防止编译报错
 */
export const annotationApi = {
  getList: (_p: unknown) => Promise.resolve({ list: [], total: 0, page: 1, limit: 20, total_pages: 1 }),
  confirm: (_id: number, _d: unknown) => Promise.resolve(null),
  reject: (_id: number) => Promise.resolve(null),
  batchConfirm: (_threshold: number) => Promise.resolve({ confirmed_count: 0 }),
}

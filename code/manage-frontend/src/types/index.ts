// 通用分页
export interface PaginatedResponse<T> {
  list: T[]
  total: number
  has_more: boolean
  next_cursor: number | null
}

// 管理员
export interface AdminUser {
  id: number
  username: string
  role: 'SUPER_ADMIN' | 'ADMIN'
}

// 五力维度
export type FivePower = 'INSIGHT' | 'CONSTRUCT' | 'DEDUCE' | 'ADAPT' | 'MIGRATE'
export const FivePowerLabels: Record<FivePower, string> = {
  INSIGHT: '洞察力',
  CONSTRUCT: '建构力',
  DEDUCE: '推演力',
  ADAPT: '调适力',
  MIGRATE: '迁移力',
}

// 题目状态（v1.2.0：扩展为5态）
export type QuestionStatus = 'draft' | 'analyzing' | 'pending_review' | 'published' | 'archived'
export const QuestionStatusLabels: Record<QuestionStatus, string> = {
  draft:          '草稿',
  analyzing:      '分析中',
  pending_review: '待审核',
  published:      '已发布',
  archived:       '已归档',
}

// 难度
export type Difficulty = 'basic' | 'advanced' | 'challenge'
export const DifficultyLabels: Record<Difficulty, string> = {
  basic: '基础',
  advanced: '进阶',
  challenge: '挑战',
}

// 五力权重（整数，合计10分）
export type FivePowerWeights = Record<FivePower, number>

// 五力训练思路（各维度文字描述）
export type FivePowerThoughts = Record<FivePower, string>

// 题目（v1.2.0：AI 全量分析字段 + 新状态模型）
export interface Question {
  id: number
  stem: string                        // 管理员录入的题干（唯一必填字段）
  image_url?: string                  // 配图（可选）
  status: QuestionStatus
  analysis_round: number              // 分析轮次（驳回后 +1）
  // ── 以下字段由大模型填充，pending_review 后可修改 ──
  subject?: string                    // 科目（数学/物理/化学）
  grade?: string                      // 年级
  chapter?: string                    // 章节
  knowledge_points?: string[]         // 知识点（多个）
  difficulty?: Difficulty
  solution?: string                   // 参考解析
  typical_error?: string              // 典型错误
  five_power_weights?: FivePowerWeights   // 五力训练权重（整数，合计10分）
  five_power_thoughts?: FivePowerThoughts // 五力训练思路（各维度文字描述）
  migration_directions?: string[]         // 迁移方向
  embedding_status: 'pending' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

// 五力测试题状态
export type CognitiveQuestionStatus = 'draft' | 'published' | 'archived'
export const CognitiveQuestionStatusLabels: Record<CognitiveQuestionStatus, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已下架',
}

// 五力测试题答案（v1.4.0）
// key 由后端按序自动生成（A/B/C/D…），前端提交时无需传 key
export interface CognitiveAnswer {
  key?: string
  text: string
  force_weights: Record<FivePower, number>
}

// 五力测试题（v1.4.0）
// 移除 question_type / target_power / option_scores / option_force_weights
// 新增 description（管理员元数据）/ answers（统一答案+权重）/ display_order
export interface CognitiveQuestion {
  id: number
  question_no: number
  display_order: number
  description?: string
  stem: string
  image_url?: string
  answers: CognitiveAnswer[]
  reference_time_sec: number
  status: CognitiveQuestionStatus
  created_at: string
  updated_at: string
}

// 训练配置版本
export interface TrainingConfig {
  id: number
  version: string
  is_active: boolean
  questions_per_session: number
  dedup_window: number
  weak_threshold: number
  severe_weak_bonus: number
  general_weak_bonus: number
  difficulty_basic_pct: number
  difficulty_advanced_pct: number
  difficulty_challenge_pct: number
  rag_mode: 'all' | 'wrong_only' | 'disabled'
  rag_timeout_sec: number
  rag_question_recall: number
  rag_strategy_recall: number
  rag_similarity_threshold: number
  ewma_decay: number
  created_at: string
  created_by: string
}

// 系统参数
export interface SystemConfig {
  key: string
  value: string
  description: string
  updated_at: string
}

// 策略
export interface Strategy {
  id: number
  name: string
  code: string
  applicable_powers: string
  priority: number
  is_enabled: boolean
  description: string
}

// 学生
export interface Student {
  id: number
  nickname: string
  grade: string
  subjects: string[]
  phone_masked: string
  has_profile: boolean
  weakest_power?: FivePower
  training_count: number
  last_login_at: string
  created_at: string
  parent_count: number  // 已绑定家长数量
}

// 学生详情
export interface StudentDetail extends Student {
  five_power_scores: Record<FivePower, number>
  ai_analysis: string
  profile_updated_at: string
  total_answers: number
  accuracy_rate: number
  parents: Array<{
    id: number
    nickname: string
    phone_masked: string
    bind_method: string
    bind_status: string
    bound_at: string
  }>
}

// 家长
export interface Parent {
  id: number
  nickname: string
  phone_masked: string
  is_confirmed: boolean          // 是否已激活（首次登录后 true）
  last_login_at: string
  created_at: string
  bound_students: Array<{
    id: number
    nickname: string
    grade: string
    bind_method: string
    bound_at: string
  }>
}

// 管理员账号
export interface AdminUser {
  id: number
  username: string
  display_name: string
  phone_masked: string
  role: 'SUPER_ADMIN' | 'ADMIN'
  is_active: boolean
  last_login_at: string
  created_at: string
}

// 审计日志
export interface AuditLog {
  id: number
  admin_id: number
  admin_username: string
  action_type: string
  target_table: string
  target_id: number
  before_data: Record<string, unknown> | null
  after_data: Record<string, unknown> | null
  ip_address: string
  created_at: string
}

// 看板数据
export interface DashboardStats {
  date: string
  // 用户规模
  total_students: number
  new_students_today: number
  active_students_today: number
  students_with_profile: number
  completed_test_total: number
  // 训练
  training_sessions_today: number
  answers_today: number
  avg_accuracy: number
  wrong_answers_today: number
  // AI
  rag_calls_today: number
  chat_sessions_today: number
  chat_messages_today: number
  aha_moments_today: number
  token_cost_today: number
  degradation_rate: number
  // 题库
  published_questions: number
  draft_questions: number
  pending_annotations: number
  confirmed_annotations: number
  pending_vectors: number
}

export interface TokenTrend {
  date: string
  training_cost: number
  assistant_cost: number
  test_cost: number
}

export interface UserGrowthPoint {
  date: string
  new_users: number
  active_users: number
}

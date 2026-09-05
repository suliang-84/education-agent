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

// 题目状态
export type QuestionStatus = 'draft' | 'published' | 'archived'
export const QuestionStatusLabels: Record<QuestionStatus, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}

// 标注状态
export type AnnotationStatus = 'pending' | 'confirmed' | 'rejected'
export const AnnotationStatusLabels: Record<AnnotationStatus, string> = {
  pending: '待审核',
  confirmed: '已确认',
  rejected: '已驳回',
}

// 难度
export type Difficulty = 'basic' | 'advanced' | 'challenge'
export const DifficultyLabels: Record<Difficulty, string> = {
  basic: '基础',
  advanced: '进阶',
  challenge: '挑战',
}

// 题目
export interface Question {
  id: number
  stem: string
  solution: string
  knowledge_point: string
  question_type: string
  difficulty: Difficulty
  status: QuestionStatus
  primary_power: FivePower
  secondary_power?: FivePower
  annotation_status: AnnotationStatus
  annotation_confidence?: number
  embedding_status: 'pending' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

// AI标注记录
export interface Annotation {
  id: number
  question_id: number
  question_stem: string
  ai_primary_power: FivePower
  ai_confidence: number
  ai_reason: string
  confirmed_primary_power?: FivePower
  annotation_status: AnnotationStatus
  created_at: string
}

// 五力测试题
export interface CognitiveQuestion {
  id: number
  order_num: number
  stem: string
  question_type: 'STANDARD' | 'OPEN'
  target_power: FivePower
  reference_time_sec: number
  option_scores: Record<string, number>
  option_force_weights?: Record<string, Record<FivePower, number>>
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
    bind_method: string
    bound_at: string
  }>
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
  total_students: number
  new_students_today: number
  active_students_today: number
  students_with_profile: number
  training_sessions_today: number
  answers_today: number
  avg_accuracy: number
  rag_calls_today: number
  chat_messages_today: number
  token_cost_today: number
  degradation_rate: number
  published_questions: number
  pending_annotations: number
  pending_vectors: number
}

export interface TokenTrend {
  date: string
  training_cost: number
  assistant_cost: number
  test_cost: number
}

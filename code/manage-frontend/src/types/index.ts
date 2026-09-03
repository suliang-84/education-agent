// ==================== 通用响应类型 ====================
export interface ApiResponse<T = unknown> {
  status: 'success' | 'fail' | 'error'
  code: number
  msg: string
  data: T
}

export interface PageData<T> {
  list: T[]
  total: number
  has_more: boolean
  next_cursor: number | null
}

// ==================== 管理员类型 ====================
export interface AdminInfo {
  admin_id: number
  username: string
  display_name: string
  role: string
  password_expired: boolean
}

export interface LoginStep1Response {
  two_fa_required: boolean
  phone_masked: string
  session_token: string
}

export interface LoginStep2Response {
  access_token: string
  access_expires_in: number
  admin_info: AdminInfo
}

// ==================== 题目类型 ====================
export type Difficulty = 'basic' | 'advanced' | 'challenge'
export type QuestionStatus = 'draft' | 'published' | 'archived'
export type AnnotationStatus = 'pending' | 'confirmed' | 'rejected'
export type PowerType = 'INSIGHT' | 'STRUCTURE' | 'INFERENCE' | 'ADAPTATION' | 'TRANSFER'
export type EmbeddingStatus = 'pending' | 'completed' | 'failed'

export interface QuestionAnnotation {
  annotation_status: AnnotationStatus
  primary_power: PowerType
  confidence: number
  reasoning?: string
}

export interface Question {
  question_id: number
  stem: string
  question_type: string
  difficulty: Difficulty
  primary_power: PowerType
  secondary_power: PowerType | null
  status: QuestionStatus
  embedding_status: EmbeddingStatus
  is_seed_data: boolean
  annotation: QuestionAnnotation
  created_at: string
}

export interface QuestionDetail extends Question {
  knowledge_point_id: number
  solution: string
  common_error: string
  insight_point: string
  construct_point: string
  inference_point: string
  adapt_point: string
  transfer_direction: string[]
  image_url: string | null
}

// ==================== AI标注审核类型 ====================
export interface Annotation {
  annotation_id: number
  question_id: number
  stem: string
  ai_annotation: {
    primary_power: PowerType
    confidence: number
    reasoning: string
  }
  annotation_status: AnnotationStatus
  created_at: string
}

// ==================== 五力测试题类型 ====================
export interface CognitiveQuestionOption {
  key: string
  text: string
}

export interface CognitiveQuestion {
  id: number
  question_no: number
  display_order: number
  question_type: 'STANDARD' | 'OPEN'
  target_power: PowerType
  stem: string
  options: CognitiveQuestionOption[]
  option_scores: Record<string, number> | null
  option_force_weights: Record<string, Record<string, number>> | null
  reference_time_sec: number
  is_active: boolean
}

// ==================== 训练配置类型 ====================
export interface TrainingConfig {
  training_total_questions: number
  weak_boost_level1: number
  weak_boost_level2: number
  weak_power_threshold: number
  difficulty_ratio: { basic: number; advanced: number; challenge: number }
  dedup_window_size: number
  rag_trigger_mode: string
  rag_topk_questions: number
  rag_topk_strategies: number
  rag_similarity_threshold: number
  rag_timeout_seconds: number
  profile_decay_coefficient: number
}

export interface TrainingConfigVersion {
  version_id: number
  version_number: string
  is_active: boolean
  config: TrainingConfig
  description?: string
  created_at: string
}

// ==================== 系统参数类型 ====================
export interface SystemConfig {
  key: string
  value: string
  value_type: 'string' | 'number' | 'boolean' | 'json'
  description: string
}

// ==================== 启发策略类型 ====================
export interface Strategy {
  strategy_id: string
  strategy_name: string
  description: string
  applicable_powers: PowerType[]
  default_priority: number
  example_phrase: string
  is_active: boolean
}

// ==================== 数据看板类型 ====================
export interface DashboardOverview {
  date: string
  users: {
    total_students: number
    new_today: number
    active_today: number
    completed_test: number
  }
  training: {
    sessions_today: number
    answers_today: number
    accuracy_rate: number
  }
  ai: {
    rag_calls_today: number
    chat_messages_today: number
    token_cost_today_usd: number
    downgrade_rate: number
  }
  question_bank: {
    total_published: number
    pending_annotation: number
    pending_embedding: number
  }
}

export interface TokenUsageDay {
  date: string
  total_tokens: number
  total_cost_usd: number
}

export interface TokenUsage {
  summary: {
    total_tokens: number
    total_cost_usd: number
    by_module: {
      training: { tokens: number; cost_usd: number }
      assistant: { tokens: number; cost_usd: number }
      test: { tokens: number; cost_usd: number }
    }
  }
  daily_data: TokenUsageDay[]
}

// ==================== 学生类型 ====================
export interface Student {
  student_id: number
  nickname: string
  grade: string
  is_minor: boolean
  has_five_power_profile: boolean
  primary_weakness: string | null
  training_count: number
  last_login_at: string
  created_at: string
}

export interface StudentDetail {
  student_id: number
  nickname: string
  grade: string
  subject_prefs: string[]
  is_minor: boolean
  created_at: string
  five_power_profile: {
    profile_id: number
    forces: Record<string, { ability: number; preference: number; final: number; level: string }>
    primary_weakness: string
    test_date: string
  } | null
  training_stats: {
    total_sessions: number
    total_questions: number
    avg_accuracy: number
    last_trained_at: string
  }
  bound_parents: Array<{ parent_id: number; nickname: string; bind_date: string }>
}

// ==================== 审计日志类型 ====================
export interface AuditLog {
  log_id: number
  admin_id: number
  admin_name: string
  action: string
  target_type: string
  target_id: string
  detail: {
    before: Record<string, unknown>
    after: Record<string, unknown>
  }
  ip_address: string
  created_at: string
}

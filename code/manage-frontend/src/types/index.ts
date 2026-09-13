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

// 题目类型（v1.2.0 新增，由大模型自动判断）
export type QuestionType = 'SINGLE_CHOICE' | 'MULTIPLE_CHOICE' | 'FILL_BLANK' | 'TRUE_FALSE' | 'APPLICATION'
export const QuestionTypeLabels: Record<QuestionType, string> = {
  SINGLE_CHOICE:   '单选题',
  MULTIPLE_CHOICE: '多选题',
  FILL_BLANK:      '填空题',
  TRUE_FALSE:      '判断题',
  APPLICATION:     '应用题',
}

// 题目答案（依题型结构化，由大模型生成，管理员可修改）
export type QuestionAnswer =
  | { type: 'SINGLE_CHOICE';   correct: string }
  | { type: 'MULTIPLE_CHOICE'; correct: string[] }
  | { type: 'FILL_BLANK';      correct: string[]; accept_range?: null }
  | { type: 'TRUE_FALSE';      correct: boolean }
  | { type: 'APPLICATION';     final_answer: string; key_steps: string[] }

// 五力权重（整数，合计10分）
export type FivePowerWeights = Record<FivePower, number>

// 五力训练思路（各维度文字描述）
export type FivePowerThoughts = Record<FivePower, string>

// 题目（v1.2.0：AI 全量分析字段 + 5级知识体系 + 题目类型与答案）
export interface Question {
  id: number
  stem: string                        // 管理员录入的题干（唯一必填字段）
  image_url?: string                  // 配图（可选）
  status: QuestionStatus
  analysis_round: number              // 分析轮次（驳回后 +1）
  // ── 以下字段由大模型填充，pending_review 后可修改 ──
  subject?: string                    // 科目（数学/物理/化学）
  grade?: string                      // 年级
  semester?: string                   // 学期（上学期/下学期）— 第三级知识体系节点
  chapter?: string                    // 单元/章节
  knowledge_points?: string[]         // 知识点（多个）— 第五级
  question_type?: QuestionType        // 题目类型（单选/多选/填空/判断/应用题）
  answer?: QuestionAnswer             // 题目答案（结构化，依题型适配）
  difficulty?: Difficulty
  solution?: string                   // 参考解析（详细推导过程）
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

// 训练维度类型（v2.0）
export type TrainingMode = 'knowledge_point' | 'chapter' | 'semester' | 'wrong_answer' | 'random'
export const TrainingModeLabels: Record<TrainingMode, string> = {
  knowledge_point: '按知识点',
  chapter:         '按单元',
  semester:        '按学期',
  wrong_answer:    '错题集',
  random:          '随机练习',
}

// 全局算法参数版本（v2.0）
export interface GlobalAlgoConfig {
  id: number
  version: string
  is_active: boolean
  rag_mode: 'all' | 'wrong_only' | 'disabled'
  rag_timeout_sec: number
  rag_question_recall: number
  rag_strategy_recall: number
  rag_similarity_threshold: number
  ewma_decay: number
  is_correct_threshold: number   // 文字题答对阈值
  created_at: string
  created_by: string
}

// 维度训练参数版本（v2.0，各维度独立版本化）
export interface DimensionTrainingConfig {
  id: number
  mode: TrainingMode
  version: string
  is_active: boolean
  questions_per_session: number
  dedup_window: number
  difficulty_basic_pct: number
  difficulty_advanced_pct: number
  difficulty_challenge_pct: number    // = 100 - basic - advanced
  weak_threshold: number
  severe_weak_bonus: number
  general_weak_bonus: number
  // 错题集专属参数
  wrong_sort_by?: 'error_count' | 'recent' | 'oldest_practice'
  new_question_mix_ratio?: number     // 新题混入比例 (0~0.5)
  consecutive_correct_to_remove?: number  // 连续答对几次移出错题
  created_at: string
  created_by: string
}

// 旧版统一配置（保留兼容，历史接口使用）
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

// 知识点练习统计（管理员视角，student_kp_stats 来源）
export interface StudentKpStat {
  knowledge_point: string
  practice_count: number
  error_rate: number | null      // null 表示不足5题，不做统计
  is_stat_valid: boolean         // practice_count >= 5 时为 true
}

// AI助教提示词摘要
export interface StudentAiPromptSummary {
  student_id: number
  learning_summary: string       // 学习信息摘要（系统自动生成）
  personal_insight: string       // 个人洞察摘要（AI提取 + 管理员可编辑）
  full_prompt_preview: string    // 合并后的完整 Prompt 预览（只读）
  updated_at: string
}

// 个人洞察历史条目
export interface PromptInsightEntry {
  id: number
  content: string
  source: 'AI' | 'ADMIN'        // AI提取 或 管理员手动补充
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

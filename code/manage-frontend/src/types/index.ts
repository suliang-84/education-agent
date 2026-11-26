// 通用分页
export interface PaginatedResponse<T> {
  list: T[]
  total: number
  page: number
  limit: number
  total_pages: number
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
  stem: string                        // 管理员录入的题目（唯一必填字段）
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
  /** 启用状态（后端 is_active 字段落地前，由 status 派生：published=已启用，archived=已停用） */
  is_active?: boolean
  created_at: string
  updated_at: string
}

// 五力测试题状态
// 测试题只有两态：published 已启用 / archived 已停用（新建即 archived，启用后才参与测试）
export type CognitiveQuestionStatus = 'published' | 'archived'
export const CognitiveQuestionStatusLabels: Record<CognitiveQuestionStatus, string> = {
  published: '已启用',
  archived: '已停用',
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
  bound_parents_count: number  // 已绑定家长数量
  warning_count?: number       // 未处理的画像预警条数
  warning_level?: 'notice' | 'attention' | 'critical' | null   // 其中最高的级别
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
    student_id: number
    nickname: string
    grade: string
    bind_method: string
    bind_date: string
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

// ── 训练配置 ─────────────────────────────────────────────────
export interface SmartParams {
  slots: { weak: number; strong: number; review: number }
  intent_min_slots: number
  weights: { kp_weak: number; pending: number; type_weak: number; power_fit: number; intent: number; fav: number; novelty: number }
  half_life_days: number
  intent_half_life_days: number
  prior: [number, number]
  recent_penalty: number
  temperature: number
  diversity_type: number
  diversity_kp: number
  review_interval_days: number
}

export interface DimensionConfig {
  dimension: string
  label: string
  version_number: string
  questions_per_session: number
  dedup_window_size: number
  difficulty_ratio: Record<string, number> | null
  type_ratio: Record<string, number> | null
  smart_params: SmartParams | null
}

export interface AnalysisConfig {
  question_analysis_concurrency: number
  question_analysis_timeout_sec: number
}

export interface TrainingConfigList {
  list: DimensionConfig[]
  question_types: string[]
  difficulties: string[]
  default_difficulty_ratio: Record<string, number>
  default_smart_params: SmartParams
  analysis: AnalysisConfig
}

// ── 学生画像（管理员视图，一期）────────────────────────────────
export interface CognitivePower {
  key: string; label: string; test: number | null; answered: number; accuracy: number | null; prev_accuracy: number | null
  delta: number | null; gap: number | null; share: number | null; blank_rate: number | null; avg_seconds: number | null
  test_change: number | null; status: 'below' | 'above' | 'ok' | 'few'
}
export interface CognitiveInsights {
  powers: CognitivePower[]
  highlights: { tone: 'good' | 'warn'; text: string }[]
  balance: { spread: number; level: string; strongest: string; weakest: string } | null
  total_answered: number
}
export interface ProfileDiagnosis {
  answered: number; blank: number; blank_rate: number | null
  blank_by_type: { key: string; label: string; answered: number; blank: number; rate: number | null }[]
  wrong: number
  causes: { key: string; label: string; count: number; ratio: number | null }[]
  repeat: { questions: number; attempts: { attempt: number; label: string; answered: number; accuracy: number | null }[]; gain: number | null }
}
export interface ProfileInsights {
  fatigue: { early: { answered: number; accuracy: number | null; blank_rate: number | null } | null; late: { answered: number; accuracy: number | null; blank_rate: number | null } | null; verdict: string | null }
  explanation: { questions: number; before: { answered: number; accuracy: number | null }; after: { answered: number; accuracy: number | null }; verdict: string | null }
  misconceptions: { question_id: number; kp: string | null; answer: string; wrong_times: number; same_times: number; text: string }[]
  bias: { text: string | null; items: { type: string; label: string; answer: string; share: number; answered: number }[] }
}
export interface ProfileRate { key: string; label: string; answered: number; accuracy: number | null }
export interface ProfileKp {
  id: number; name: string; chapter: string | null; attempts: number; errors: number; error_rate: number | null; weak_score: number; last_at: string | null
  blank_errors: number; rush_errors: number; thoughtful_errors: number; trend: 'up' | 'flat' | 'down' | null; advice: string | null
  root_kp: { id: number; name: string } | null   // 可能被它拖累的前置薄弱点（同一单元里排在前面）
}
export interface ProfileStrategy { strategy_id: string; name: string; uses: number; likes: number; dislikes: number; score: number | null }
export interface ProfileKpi { key: string; label: string; value: string; delta: number | null; unit: string; good: 'up' | 'down' | null; tip: string; series: (number | null)[] }

export interface StudyTime {
  has_data: boolean
  unit?: 'day' | 'week'
  time_buckets?: { key: string; label: string; range: string; minutes: number }[]
  types?: { key: string; label: string; minutes: number; sessions: number; share: number | null }[]
  /** 每个学科各自的练习方式时长分布（键是学科 code；占比按这个学科自己的总时长算） */
  types_by_subject?: Record<string, { key: string; label: string; minutes: number; sessions: number; share: number | null }[]>
  tips?: string[]
  subjects?: { code: string; name: string; minutes: number; share: number | null }[]
  series?: { label: string; minutes: Record<string, number>; total: number }[]
  stats?: {
    total_minutes: number; prev_minutes: number; delta_pct: number | null; active_days: number; avg_per_active_day: number | null
    best_day: { date: string; minutes: number } | null; prev_best_minutes?: number | null; avg_per_session: number | null; weekday_avg: number | null; weekend_avg: number | null
    prev_avg_per_session?: number | null; prev_weekday_avg?: number | null; prev_weekend_avg?: number | null   // 前一周期对应值（分钟），没有则 null
  }
  highlights?: { tone: 'good' | 'warn'; text: string }[]
  /** 每个学科周期内用时最长的 5 个知识点（键是学科 code）；一道题挂多个知识点时各算一份，只用来排名 */
  kp_top?: Record<string, { id: number; name: string; minutes: number; answered: number }[]>
}

/** 训练次数明细（中间明细区，顶部选中「训练次数」时用）。口径见后端 _sessions_build */
export interface TrainingStats {
  has_data: boolean
  unit?: 'day' | 'week'
  stats?: {
    total: number; prev_total: number; days: number; active_days: number; done: number
    avg_per_day: number; prev_avg_per_day: number | null
    best_day: { date: string; count: number }; prev_best_count: number | null
    completion: number | null; prev_completion: number | null          // 答题完成度：作答题数 ÷ 下发题数（%）
    avg_answered: number | null; prev_avg_answered: number | null       // 平均每次作答题数（只算作答了的训练）
    weekday_avg: number | null; weekend_avg: number | null              // ÷ 范围内对应的天数
    max_gap_days: number
    completeness: { full: number; partial: number; none: number }       // 全部作答 / 作答一部分 / 一题没答
  }
  /** 各学科的训练次数（一次训练归到下发题目里最多的那个学科） */
  subjects?: { code: string; name: string; count: number; share: number | null }[]
  series?: { label: string; done: number; undone: number; total: number; by_subject: Record<string, number> }[]
  types?: { key: string; label: string; count: number; share: number | null; done_rate: number | null }[]
  /** 每个学科各自的练习方式次数分布（键是学科 code；占比按这个学科自己的训练数算） */
  types_by_subject?: Record<string, { key: string; label: string; count: number; share: number | null; done_rate: number | null }[]>
  /** 每个学科周期内被训练次数最多的 5 个知识点（键是学科 code）；一次训练里同一个知识点只算一次，count 是训练次数，done 是其中完成的次数 */
  kp_top?: Record<string, { id: number; name: string; count: number; done: number }[]>
  tips?: string[]
}

/** 答题数明细（中间明细区，顶部选中「答题数」时用）。错题 / 顽固错题 / 收藏是当前状态，不随日期范围变；其余是所选范围内的。口径见后端 _answers_build */
export interface AnswerBucket { key: string; label: string; count: number; correct: number; accuracy: number | null; share: number | null }
export interface AnswerStats {
  has_data: boolean
  stats: {
    total: number; prev_total: number; correct: number; accuracy: number | null
    wrong_pending: number; wrong_mastered: number; mastered_rate: number | null    // 待攻克 / 已攻克 / 攻克率（%）
    prev_wrong_pending?: number | null; prev_wrong_mastered?: number | null; prev_stubborn?: number | null; prev_favorites?: number | null   // 所选范围开始时的值（涨跌 = 范围内净变化）
    stubborn: number; favorites: number                                            // 顽固错题（同一道题错 3 次以上）/ 收藏题数
    breakdown: Record<string, { pending: number; mastered: number; stubborn: number; favorites: number }>   // 每个学科各是多少
  }
  subjects: { code: string; name: string; count: number; correct: number; accuracy: number | null; share: number | null }[]
  types_by_subject: Record<string, AnswerBucket[]>            // 题型：固定 5 种
  difficulty_by_subject: Record<string, AnswerBucket[]>       // 难度：固定 基础 / 进阶 / 挑战
  kp_top: Record<string, { id: number; name: string; count: number; correct: number; accuracy: number | null }[]>
  tips: string[]
}

/** 正确率明细（中间明细区，顶部选中「正确率」时用）。口径和「学业掌握」标签页一致，但限定在所选日期范围内，并按学科拆开。见后端 _accuracy_build */
export interface AccuracyKp {
  id: number; name: string; count: number; correct: number; accuracy: number | null; error_rate: number | null
  wrong: number; blank: number; rush: number; thoughtful: number          // 错因：没作答 / 秒答 / 认真做仍错
  trend: 'up' | 'flat' | 'down' | null                                       // 走向（同「学业掌握」：按全部历史算，做的次数不够为 null）
  root_kp: { id: number; name: string } | null                              // 可能被它拖累的前置薄弱点
}
export interface AiAsksStats {
  has_data: boolean
  stats: {
    total: number; prev_total: number; sessions: number; prev_sessions: number; aha: number; prev_aha: number
    avg_ask: number | null; prev_avg_ask: number | null; like_rate: number | null; rated: number; ask_answer: number; mood: number
  }
  series: { label: string; count: number; aha: number }[]
  unit: 'day' | 'week'
  periods: { key: string; label: string; range: string; count: number; share: number | null }[]
  strategies: { id: string; name: string; uses: number; likes: number; dislikes: number }[]
  tips: string[]
}
export interface AccuracyStats {
  has_data: boolean
  stats: {
    total: number; correct: number; wrong: number; accuracy: number | null
    prev_accuracy: number | null; prev_total: number; prev_correct: number | null      // 前一段不足 10 题时为 null
    weak_kps: number; strong_kps: number                                                // 薄弱（错误率 ≥ 40%）/ 强项知识点个数（做过 2 次以上）
    semester: { practiced: number; total: number; rate: number | null }                 // 当前学期进度：练过的知识点 / 总数
    causes: { wrong: number; blank: number; rush: number; thoughtful: number }
  }
  subjects: { code: string; name: string; count: number; correct: number; accuracy: number | null }[]
  /** 正确率趋势：从旧到新，每个点（按天 / 按周）的整体和各学科正确率；样本太少（按天 < 2 题、按周 < 3 题）为 null */
  trend: { unit: 'day' | 'week'; series: { label: string; count: number; accuracy: number | null; by_subject: Record<string, { count: number; accuracy: number | null }> }[] } | null
  types_by_subject: Record<string, AnswerBucket[]>
  difficulty_by_subject: Record<string, AnswerBucket[]>
  weak_by_subject: Record<string, AccuracyKp[]>
  strong_by_subject: Record<string, AccuracyKp[]>
  tips: string[]
}

export interface StudentProfile {
  generated_at: string
  kpis: ProfileKpi[]
  /** 最近三个月（91 天）每天的学习时长 / 正确率，固定口径，不随日期范围变；顶部卡片背景用 */
  trend_3m?: { unit: 'day'; days: number; has_data: boolean; series: { date: string; label: string; minutes: number; answered: number; correct: number; accuracy: number | null; sessions: number }[] }
  study_time: StudyTime
  training?: TrainingStats
  answers?: AnswerStats
  accuracy?: AccuracyStats
  ai_asks?: AiAsksStats
  range: { start: string; end: string; days: number; label: string; is_recent: boolean; daily: boolean; min_answered: number; freq_full: number; review_full: number }
  summary: {
    status: string; status_reason: string; engagement_score: number
    engagement_parts: { frequency: number; streak: number; complete: number; careful: number | null; review: number | null; review_sessions: number; review_wrong_total: number }
    trend: { weeks: { weeks_ago: number; label: string; answered: number; accuracy: number | null }[]; slope: number | null; delta: number | null; unit: 'day' | 'week' }
    tips: string[]
    dim_advice?: { dim: string; text: string }[]   // 各维度里拆出来的建议（维度卡片只留总结）
    status_detail: {
      metrics: { key: string; label: string; value: string; hint: string | null; tone: 'good' | 'warn' | null; delta?: number | null; unit?: string; prev?: string | null }[]
      drivers: { tone: 'good' | 'warn'; text: string }[]
    }
  }
  basic: {
    id: number; nickname: string; avatar_url: string | null; grade: string | null; semester: string | null; is_minor: boolean
    is_active?: boolean; phone_masked?: string | null   // 账号是否启用 / 脱敏手机号
    created_at: string; last_login_at: string | null; active_days_30: number
    parents: { id: number; nickname: string; confirmed_at: string | null }[]
  }
  cognitive: {
    has_profile: boolean; tested_at?: string
    final?: Record<string, number>; ability?: Record<string, number>; preference?: Record<string, number>; training?: Record<string, number> | null
    training_info?: { total_training_count: number; total_question_count: number; last_trained_at: string | null } | null
    primary_strength?: string; primary_weakness?: string; secondary_weakness?: string; preferred_force?: string; recommended_mode?: string
    confidence?: number | null; tags?: string[]
    previous_test?: { tested_at: string; final: Record<string, number> } | null
    insights?: CognitiveInsights
  }
  mastery: {
    answered: number; correct: number; accuracy: number | null
    by_subject: ProfileRate[]; by_type: ProfileRate[]; by_difficulty: ProfileRate[]
    weak_kps: ProfileKp[]; strong_kps: ProfileKp[]; kp_total_practiced: number
    wrong_pending: number; wrong_mastered: number; wrong_mastered_rate: number | null
    stubborn_questions: number; favorites: number
    semester_progress: { practiced: number; total: number; rate: number | null }
  }
  diagnosis: ProfileDiagnosis
  insights: ProfileInsights
  behavior: {
    sessions_range: number; active_days: number; sessions_total: number; streak_days: number; last_active_date: string | null
    time_buckets: { key: string; label: string; count: number; ratio: number | null; accuracy: number | null }[]
    avg_seconds_per_question: number | null; avg_seconds_per_session: number | null
    fast_wrong_ratio: number | null; fast_wrong_samples: number
    completed_sessions: number; finished_sessions: number; issued_questions: number; answered_questions: number; complete_rate: number | null
    dimensions: { key: string; label: string; count: number }[]
  }
  ai_interaction: {
    student_messages: number; assistant_messages: number; sessions: number; last_chat_at: string | null; aha_count: number
    top_strategies: ProfileStrategy[]; bottom_strategies: ProfileStrategy[]; strategies: ProfileStrategy[]
    intents: unknown[]; chat_summary: string | null; intents_refreshed_at: string | null
  }
  traits: {
    personal_insight: string | null; insight_admin_text: string | null; insight_ai_text: string | null
    personal_insight_updated_at?: string | null; learning_summary?: string | null; learning_summary_updated_at?: string | null
  }
  warnings: { open: ProfileWarning[]; handled: ProfileWarning[] }
}

export interface ProfileWarning {
  id: number; rule_code: string; rule_name: string; level: 'notice' | 'attention' | 'critical'; level_label: string
  status: 'open' | 'handled' | 'closed'; message: string; triggered_at: string; handled_at: string | null; note: string | null
}
export interface ProfileRuleField {
  key: string; label: string; unit: string; default: number | string
  min?: number; max?: number                       // 数字类参数的范围
  type?: 'select'; options?: { value: string; label: string }[]   // 下拉类参数
}
export interface ProfileRule {
  code: string; name: string; desc: string; tiered: boolean; fields: ProfileRuleField[]
  enabled: boolean; level: 'notice' | 'attention' | 'critical'; params: Record<string, number | string>
}
export interface ProfileConfig {
  levels: { value: string; label: string }[]
  rules: ProfileRule[]
  weights: Record<string, number>
  weight_labels: Record<string, string>
  default_weights: Record<string, number>
}

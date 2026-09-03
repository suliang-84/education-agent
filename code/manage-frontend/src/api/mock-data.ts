import type {
  Question, Annotation, CognitiveQuestion, TrainingConfigVersion,
  SystemConfig, Strategy, DashboardOverview, TokenUsage,
  Student, StudentDetail, AuditLog
} from '../types'

// ==================== Mock 题目列表 ====================
export const mockQuestions: Question[] = [
  {
    question_id: 5001,
    stem: '几个人一起买一件东西。如果每人出400钱，会多出3400钱；如果每人出300钱，会多出100钱。请建立人数与总价之间的方程关系。',
    question_type: 'app',
    difficulty: 'basic',
    primary_power: 'STRUCTURE',
    secondary_power: 'INSIGHT',
    status: 'published',
    embedding_status: 'completed',
    is_seed_data: false,
    annotation: { annotation_status: 'confirmed', primary_power: 'STRUCTURE', confidence: 0.92 },
    created_at: '2026-08-01T00:00:00Z',
  },
  {
    question_id: 5002,
    stem: '一辆汽车在平直公路上行驶，受到2000N的合力作用，质量为1000kg，请求出加速度大小。',
    question_type: 'calc',
    difficulty: 'advanced',
    primary_power: 'INFERENCE',
    secondary_power: 'STRUCTURE',
    status: 'draft',
    embedding_status: 'pending',
    is_seed_data: false,
    annotation: { annotation_status: 'pending', primary_power: 'INFERENCE', confidence: 0.75 },
    created_at: '2026-08-05T00:00:00Z',
  },
  {
    question_id: 5003,
    stem: '如图所示，△ABC中，∠ACB=90°，CD⊥AB，垂足为D。请证明CD²=AD·DB。',
    question_type: 'proof',
    difficulty: 'challenge',
    primary_power: 'INSIGHT',
    secondary_power: 'INFERENCE',
    status: 'archived',
    embedding_status: 'completed',
    is_seed_data: true,
    annotation: { annotation_status: 'confirmed', primary_power: 'INSIGHT', confidence: 0.88 },
    created_at: '2026-07-20T00:00:00Z',
  },
  {
    question_id: 5004,
    stem: '城市气温数据分析：某城市连续7天的最高气温（℃）分别为28、30、32、29、35、33、31，求这7天最高气温的平均数、中位数和众数。',
    question_type: 'stat',
    difficulty: 'basic',
    primary_power: 'INSIGHT',
    secondary_power: 'ADAPTATION',
    status: 'published',
    embedding_status: 'completed',
    is_seed_data: false,
    annotation: { annotation_status: 'confirmed', primary_power: 'INSIGHT', confidence: 0.91 },
    created_at: '2026-08-10T00:00:00Z',
  },
  {
    question_id: 5005,
    stem: '小明从家出发，以4km/h的速度步行去学校，途中因忘带书包返回，再以6km/h的速度步行去学校，比原计划晚到10分钟。求小明家到学校的距离。',
    question_type: 'app',
    difficulty: 'advanced',
    primary_power: 'TRANSFER',
    secondary_power: 'STRUCTURE',
    status: 'published',
    embedding_status: 'completed',
    is_seed_data: false,
    annotation: { annotation_status: 'confirmed', primary_power: 'TRANSFER', confidence: 0.85 },
    created_at: '2026-08-12T00:00:00Z',
  },
  {
    question_id: 5006,
    stem: '溶液配制：将50mL 10mol/L的盐酸溶液稀释成1mol/L的盐酸，需要加水多少毫升？',
    question_type: 'calc',
    difficulty: 'basic',
    primary_power: 'ADAPTATION',
    secondary_power: 'INFERENCE',
    status: 'published',
    embedding_status: 'completed',
    is_seed_data: false,
    annotation: { annotation_status: 'confirmed', primary_power: 'ADAPTATION', confidence: 0.89 },
    created_at: '2026-08-15T00:00:00Z',
  },
  {
    question_id: 5007,
    stem: '函数f(x)=2x²-3x+1，求其在区间[0,2]上的最大值和最小值。',
    question_type: 'func',
    difficulty: 'advanced',
    primary_power: 'INFERENCE',
    secondary_power: 'STRUCTURE',
    status: 'draft',
    embedding_status: 'pending',
    is_seed_data: false,
    annotation: { annotation_status: 'pending', primary_power: 'INFERENCE', confidence: 0.67 },
    created_at: '2026-08-20T00:00:00Z',
  },
  {
    question_id: 5008,
    stem: '科学家发现某湖泊鱼类突然减少，目前有四条线索：A.近期有工厂排污；B.外来物种入侵；C.气候变化导致水温升高；D.渔民过度捕捞。请分析最可能的主要原因。',
    question_type: 'analysis',
    difficulty: 'challenge',
    primary_power: 'INSIGHT',
    secondary_power: 'ADAPTATION',
    status: 'published',
    embedding_status: 'completed',
    is_seed_data: false,
    annotation: { annotation_status: 'pending', primary_power: 'INSIGHT', confidence: 0.63 },
    created_at: '2026-08-22T00:00:00Z',
  },
]

// ==================== Mock 标注列表 ====================
export const mockAnnotations: Annotation[] = [
  {
    annotation_id: 301,
    question_id: 5002,
    stem: '一辆汽车在平直公路上行驶，受到2000N的合力作用，质量为1000kg，请求出加速度大小。',
    ai_annotation: {
      primary_power: 'INFERENCE',
      confidence: 0.75,
      reasoning: '题目需要连续推导牛顿第二定律的步骤，属于推演力训练题',
    },
    annotation_status: 'pending',
    created_at: '2026-08-30T08:00:00Z',
  },
  {
    annotation_id: 302,
    question_id: 5007,
    stem: '函数f(x)=2x²-3x+1，求其在区间[0,2]上的最大值和最小值。',
    ai_annotation: {
      primary_power: 'INFERENCE',
      confidence: 0.67,
      reasoning: '需要利用导数判断极值，涉及推演能力',
    },
    annotation_status: 'pending',
    created_at: '2026-08-30T08:30:00Z',
  },
  {
    annotation_id: 303,
    question_id: 5008,
    stem: '科学家发现某湖泊鱼类突然减少，目前有四条线索...',
    ai_annotation: {
      primary_power: 'INSIGHT',
      confidence: 0.63,
      reasoning: '题目要求从多条线索中筛选关键信息，属于洞察力训练',
    },
    annotation_status: 'pending',
    created_at: '2026-08-30T09:00:00Z',
  },
  {
    annotation_id: 304,
    question_id: 5001,
    stem: '几个人一起买一件东西。如果每人出400钱...',
    ai_annotation: {
      primary_power: 'STRUCTURE',
      confidence: 0.92,
      reasoning: '题目需要建立变量关系，属于建构力训练题',
    },
    annotation_status: 'confirmed',
    created_at: '2026-08-29T10:00:00Z',
  },
]

// ==================== Mock 五力测试题 ====================
export const mockCognitiveQuestions: CognitiveQuestion[] = [
  {
    id: 1, question_no: 1, display_order: 3, question_type: 'STANDARD',
    target_power: 'INSIGHT',
    stem: '有一个封闭房间，里面放着完全相同的三杯热水。A杯没有盖，B杯和C杯有盖子，C杯外面还裹了一条毛巾。20分钟后，哪杯水温度最高？',
    options: [
      { key: 'A', text: '三个杯子的水最后都会变凉' },
      { key: 'B', text: 'B和C都加了盖，但结果仍然不同' },
      { key: 'C', text: 'A杯没有毛巾' },
      { key: 'D', text: '实验时间都是20分钟' },
    ],
    option_scores: { A: 1, B: 4, C: 10, D: 1 },
    option_force_weights: null,
    reference_time_sec: 90,
    is_active: true,
  },
  {
    id: 2, question_no: 2, display_order: 7, question_type: 'STANDARD',
    target_power: 'STRUCTURE',
    stem: '一块长方形草坪，长比宽多10米，周长为60米。如果用篱笆围起来，需要多少米篱笆？围起来后，草坪面积是多少平方米？',
    options: [
      { key: 'A', text: '周长60米，面积200平方米' },
      { key: 'B', text: '周长60米，面积175平方米' },
      { key: 'C', text: '篱笆需要60米，面积200平方米' },
      { key: 'D', text: '无法确定' },
    ],
    option_scores: { A: 10, B: 4, C: 4, D: 1 },
    option_force_weights: null,
    reference_time_sec: 120,
    is_active: true,
  },
  {
    id: 3, question_no: 3, display_order: 12, question_type: 'OPEN',
    target_power: 'INSIGHT',
    stem: '科学家发现某湖泊的鱼类数量在过去一年中突然大幅减少。目前有以下四条线索：A.附近有新建工厂开始运营；B.当地引入了一种外来鱼类；C.该地区经历了异常高温天气；D.当地渔民反映捕鱼量与往年相比没有明显变化。请选择你认为最可能的主要原因，并解释你的推理过程。',
    options: [
      { key: 'A', text: '工厂排污是主因，因为工业废水会直接污染水体' },
      { key: 'B', text: '外来物种入侵，竞争食物资源导致本地鱼类减少' },
      { key: 'C', text: '气候变化影响了水温，部分鱼类无法适应' },
      { key: 'D', text: '综合多种因素共同作用的结果' },
    ],
    option_scores: null,
    option_force_weights: {
      A: { INSIGHT: 0.70, STRUCTURE: 0.05, INFERENCE: 0.10, ADAPTATION: 0.10, TRANSFER: 0.05 },
      B: { INSIGHT: 0.10, STRUCTURE: 0.65, INFERENCE: 0.10, ADAPTATION: 0.10, TRANSFER: 0.05 },
      C: { INSIGHT: 0.15, STRUCTURE: 0.05, INFERENCE: 0.60, ADAPTATION: 0.15, TRANSFER: 0.05 },
      D: { INSIGHT: 0.20, STRUCTURE: 0.20, INFERENCE: 0.20, ADAPTATION: 0.20, TRANSFER: 0.20 },
    },
    reference_time_sec: 180,
    is_active: true,
  },
  {
    id: 4, question_no: 4, display_order: 5, question_type: 'STANDARD',
    target_power: 'INFERENCE',
    stem: '在一个数列中：1, 4, 9, 16, 25, ...，第10项是多少？第n项的通项公式是什么？',
    options: [
      { key: 'A', text: '第10项是100，通项公式是n²' },
      { key: 'B', text: '第10项是90，通项公式是n(n-1)' },
      { key: 'C', text: '第10项是100，通项公式是2n-1的累加' },
      { key: 'D', text: '第10项是110，无规律通项' },
    ],
    option_scores: { A: 10, B: 2, C: 4, D: 1 },
    option_force_weights: null,
    reference_time_sec: 90,
    is_active: true,
  },
  {
    id: 5, question_no: 5, display_order: 15, question_type: 'STANDARD',
    target_power: 'ADAPTATION',
    stem: '小明骑自行车从A城到B城，速度为20km/h；返回时改乘公交车，速度为60km/h。问全程平均速度是多少？',
    options: [
      { key: 'A', text: '40 km/h（两者平均）' },
      { key: 'B', text: '30 km/h（调和平均）' },
      { key: 'C', text: '45 km/h（加权平均）' },
      { key: 'D', text: '无法确定' },
    ],
    option_scores: { A: 2, B: 10, C: 3, D: 1 },
    option_force_weights: null,
    reference_time_sec: 100,
    is_active: true,
  },
]

// ==================== Mock 训练配置 ====================
export const mockTrainingConfig: TrainingConfigVersion = {
  version_id: 5,
  version_number: 'v5',
  is_active: true,
  config: {
    training_total_questions: 5,
    weak_boost_level1: 0.40,
    weak_boost_level2: 0.20,
    weak_power_threshold: 65,
    difficulty_ratio: { basic: 50, advanced: 35, challenge: 15 },
    dedup_window_size: 30,
    rag_trigger_mode: 'all',
    rag_topk_questions: 3,
    rag_topk_strategies: 2,
    rag_similarity_threshold: 0.75,
    rag_timeout_seconds: 8,
    profile_decay_coefficient: 0.30,
  },
  description: '初始配置版本',
  created_at: '2026-08-01T00:00:00Z',
}

export const mockTrainingConfigHistory: TrainingConfigVersion[] = [
  mockTrainingConfig,
  {
    version_id: 4,
    version_number: 'v4',
    is_active: false,
    config: {
      training_total_questions: 5,
      weak_boost_level1: 0.35,
      weak_boost_level2: 0.15,
      weak_power_threshold: 60,
      difficulty_ratio: { basic: 55, advanced: 30, challenge: 15 },
      dedup_window_size: 25,
      rag_trigger_mode: 'wrong_only',
      rag_topk_questions: 3,
      rag_topk_strategies: 2,
      rag_similarity_threshold: 0.70,
      rag_timeout_seconds: 10,
      profile_decay_coefficient: 0.25,
    },
    description: '调整选题权重',
    created_at: '2026-07-15T00:00:00Z',
  },
]

// ==================== Mock 系统配置 ====================
export const mockSystemConfigs: SystemConfig[] = [
  { key: 'active_llm_provider', value: 'tongyi', value_type: 'string', description: '当前LLM供应商，支持热切换（tongyi/openai/claude）' },
  { key: 'chat_max_rounds', value: '30', value_type: 'number', description: '单会话最大对话轮数' },
  { key: 'rag_timeout_seconds', value: '8', value_type: 'number', description: 'RAG生成超时时间（秒），超时触发降级' },
  { key: 'token_session_limit', value: '15000', value_type: 'number', description: '单会话Token上限，超出后AI降级响应' },
  { key: 'wrong_review_timeout_min', value: '20', value_type: 'number', description: '错题复盘最长时间（分钟）' },
  { key: 'strategy_switch_threshold', value: '2', value_type: 'number', description: '同一策略连续无效次数后自动切换' },
  { key: 'proactive_max_count', value: '3', value_type: 'number', description: 'AI主动介入上限（次/训练会话）' },
  { key: 'sms_rate_limit_seconds', value: '60', value_type: 'number', description: '短信发送间隔限制（秒）' },
  { key: 'test_retest_days', value: '30', value_type: 'number', description: '五力测试重测推荐间隔（天，建议值，不强制）' },
  { key: 'enable_achievement_feedback', value: 'true', value_type: 'boolean', description: '是否开启成就感反馈功能' },
]

// ==================== Mock 启发策略 ====================
export const mockStrategies: Strategy[] = [
  {
    strategy_id: 'S-SOCRATIC',
    strategy_name: '苏格拉底提问',
    description: '通过连续小问题引导学生自主推导，不给结论，激发主动思考',
    applicable_powers: ['INSIGHT', 'STRUCTURE', 'INFERENCE', 'ADAPTATION', 'TRANSFER'],
    default_priority: 1,
    example_phrase: '首先，题目告诉我们什么？然后，我们要找的是什么？',
    is_active: true,
  },
  {
    strategy_id: 'S-SIMPLIFY',
    strategy_name: '化简特例',
    description: '将复杂问题简化为特殊情况，帮助学生找到规律后泛化',
    applicable_powers: ['ADAPTATION'],
    default_priority: 2,
    example_phrase: '先假设只有2个人，这种情况下你会怎么列式？',
    is_active: true,
  },
  {
    strategy_id: 'S-ANALOGY',
    strategy_name: '生活场景类比',
    description: '用学生熟悉的生活场景类比抽象数学概念，降低认知负担',
    applicable_powers: ['INSIGHT', 'STRUCTURE'],
    default_priority: 3,
    example_phrase: '这个关系就像去超市买东西，总价=单价×数量，你能找到这里的"单价"是什么吗？',
    is_active: true,
  },
  {
    strategy_id: 'S-SPATIAL',
    strategy_name: '空间想象',
    description: '引导学生用几何直观或图形化思维处理抽象关系',
    applicable_powers: ['INSIGHT', 'INFERENCE'],
    default_priority: 4,
    example_phrase: '试着在脑海中画一条数轴，把这个关系标注出来看看？',
    is_active: true,
  },
  {
    strategy_id: 'S-DIAGRAM',
    strategy_name: '图示引导',
    description: '引导学生动手画图、列表、建模，将信息可视化',
    applicable_powers: ['INSIGHT'],
    default_priority: 5,
    example_phrase: '你能把题目里的条件画成一张关系图吗？试试看。',
    is_active: true,
  },
  {
    strategy_id: 'S-STORY',
    strategy_name: '故事叙述',
    description: '将数学问题包装成故事情节，帮助学生理解抽象符号的现实意义',
    applicable_powers: ['STRUCTURE', 'TRANSFER'],
    default_priority: 6,
    example_phrase: '我们来讲个故事：这几个人去买东西，每人掏了400块，多了3400块……那多出来的钱是谁的？',
    is_active: true,
  },
  {
    strategy_id: 'S-COUNTEREX',
    strategy_name: '反例证伪',
    description: '通过构造反例帮助学生发现错误推理，加深正确理解',
    applicable_powers: ['INFERENCE', 'ADAPTATION'],
    default_priority: 7,
    example_phrase: '如果你的想法是对的，那么当人数为0时会发生什么？和题目矛盾吗？',
    is_active: true,
  },
  {
    strategy_id: 'S-RHYTHM',
    strategy_name: '节奏/模式感',
    description: '引导学生发现题目中的数量规律和结构模式',
    applicable_powers: ['STRUCTURE', 'INFERENCE'],
    default_priority: 8,
    example_phrase: '注意看这组数字：400、300、3400、100……你有没有发现什么规律？',
    is_active: true,
  },
  {
    strategy_id: 'S-TRANSFER',
    strategy_name: '已知知识类比',
    description: '将新问题与学生已掌握的知识点建立连接，促进知识迁移',
    applicable_powers: ['TRANSFER'],
    default_priority: 9,
    example_phrase: '这道题和你之前做过的"追及问题"有什么共同的数学结构吗？',
    is_active: true,
  },
]

// ==================== Mock 数据看板 ====================
export const mockDashboard: DashboardOverview = {
  date: '2026-08-30',
  users: {
    total_students: 483,
    new_today: 12,
    active_today: 85,
    completed_test: 312,
  },
  training: {
    sessions_today: 156,
    answers_today: 780,
    accuracy_rate: 0.63,
  },
  ai: {
    rag_calls_today: 312,
    chat_messages_today: 890,
    token_cost_today_usd: 0.24,
    downgrade_rate: 0.02,
  },
  question_bank: {
    total_published: 1280,
    pending_annotation: 45,
    pending_embedding: 8,
  },
}

export const mockTokenUsage: TokenUsage = {
  summary: {
    total_tokens: 2840000,
    total_cost_usd: 0.427,
    by_module: {
      training: { tokens: 1800000, cost_usd: 0.27 },
      assistant: { tokens: 950000, cost_usd: 0.143 },
      test: { tokens: 90000, cost_usd: 0.014 },
    },
  },
  daily_data: [
    { date: '2026-08-24', total_tokens: 92000, total_cost_usd: 0.014 },
    { date: '2026-08-25', total_tokens: 105000, total_cost_usd: 0.016 },
    { date: '2026-08-26', total_tokens: 88000, total_cost_usd: 0.013 },
    { date: '2026-08-27', total_tokens: 115000, total_cost_usd: 0.017 },
    { date: '2026-08-28', total_tokens: 130000, total_cost_usd: 0.020 },
    { date: '2026-08-29', total_tokens: 125000, total_cost_usd: 0.019 },
    { date: '2026-08-30', total_tokens: 95000, total_cost_usd: 0.014 },
  ],
}

// ==================== Mock 学生列表 ====================
export const mockStudents: Student[] = [
  {
    student_id: 1001, nickname: '小明', grade: 'G9', is_minor: true,
    has_five_power_profile: true, primary_weakness: 'STRUCTURE', training_count: 15,
    last_login_at: '2026-08-30T09:00:00Z', created_at: '2026-07-01T00:00:00Z',
  },
  {
    student_id: 1002, nickname: '小红', grade: 'G10', is_minor: false,
    has_five_power_profile: true, primary_weakness: 'INFERENCE', training_count: 8,
    last_login_at: '2026-08-28T15:30:00Z', created_at: '2026-07-15T00:00:00Z',
  },
  {
    student_id: 1003, nickname: '新用户', grade: 'G8', is_minor: true,
    has_five_power_profile: false, primary_weakness: null, training_count: 0,
    last_login_at: '2026-08-30T10:00:00Z', created_at: '2026-08-30T10:00:00Z',
  },
  {
    student_id: 1004, nickname: '张伟', grade: 'G11', is_minor: false,
    has_five_power_profile: true, primary_weakness: 'ADAPTATION', training_count: 23,
    last_login_at: '2026-08-29T20:00:00Z', created_at: '2026-06-20T00:00:00Z',
  },
  {
    student_id: 1005, nickname: '李华', grade: 'G9', is_minor: true,
    has_five_power_profile: true, primary_weakness: 'TRANSFER', training_count: 12,
    last_login_at: '2026-08-30T08:00:00Z', created_at: '2026-07-10T00:00:00Z',
  },
]

export const mockStudentDetail: StudentDetail = {
  student_id: 1001,
  nickname: '小明',
  grade: 'G9',
  subject_prefs: ['MATH', 'PHYSICS'],
  is_minor: true,
  created_at: '2026-07-01T00:00:00Z',
  five_power_profile: {
    profile_id: 2001,
    forces: {
      insight: { ability: 82, preference: 34, final: 69, level: 'strong' },
      structure: { ability: 47, preference: 18, final: 41, level: 'weak' },
      inference: { ability: 74, preference: 17, final: 57, level: 'good' },
      adaptation: { ability: 55, preference: 21, final: 45, level: 'medium' },
      transfer: { ability: 51, preference: 10, final: 39, level: 'weak' },
    },
    primary_weakness: 'structure',
    test_date: '2026-08-30T10:00:00Z',
  },
  training_stats: {
    total_sessions: 15,
    total_questions: 75,
    avg_accuracy: 0.65,
    last_trained_at: '2026-08-30T15:00:00Z',
  },
  bound_parents: [
    { parent_id: 2001, nickname: '小明爸爸', bind_date: '2026-07-05T00:00:00Z' },
    { parent_id: 2002, nickname: '小明妈妈', bind_date: '2026-08-01T00:00:00Z' },
  ],
}

// ==================== Mock 审计日志 ====================
export const mockAuditLogs: AuditLog[] = [
  {
    log_id: 5001,
    admin_id: 1, admin_name: '系统管理员',
    action: 'CONFIRM_ANNOTATION',
    target_type: 'question_annotations', target_id: '301',
    detail: {
      before: { annotation_status: 'pending' },
      after: { annotation_status: 'confirmed', confirmed_primary_power: 'STRUCTURE', confirmed_at: '2026-08-30T09:00:00Z' },
    },
    ip_address: '192.168.1.1',
    created_at: '2026-08-30T10:00:00Z',
  },
  {
    log_id: 5002,
    admin_id: 1, admin_name: '系统管理员',
    action: 'PUBLISH_QUESTION',
    target_type: 'questions', target_id: '5001',
    detail: {
      before: { status: 'draft' },
      after: { status: 'published', embedding_triggered: true },
    },
    ip_address: '192.168.1.1',
    created_at: '2026-08-30T09:30:00Z',
  },
  {
    log_id: 5003,
    admin_id: 1, admin_name: '系统管理员',
    action: 'UPDATE_SYSTEM_CONFIG',
    target_type: 'system_configs', target_id: 'active_llm_provider',
    detail: {
      before: { value: 'tongyi' },
      after: { value: 'openai' },
    },
    ip_address: '192.168.1.1',
    created_at: '2026-08-30T09:00:00Z',
  },
  {
    log_id: 5004,
    admin_id: 1, admin_name: '系统管理员',
    action: 'CREATE_TRAINING_CONFIG',
    target_type: 'training_config_versions', target_id: '5',
    detail: {
      before: { is_active: false },
      after: { is_active: true, version_number: 'v5' },
    },
    ip_address: '192.168.1.1',
    created_at: '2026-08-01T00:00:00Z',
  },
  {
    log_id: 5005,
    admin_id: 1, admin_name: '系统管理员',
    action: 'BIND_PARENT',
    target_type: 'students', target_id: '1001',
    detail: {
      before: {},
      after: { parent_id: 2003, bind_method: 'ADMIN' },
    },
    ip_address: '192.168.1.1',
    created_at: '2026-08-29T14:00:00Z',
  },
]

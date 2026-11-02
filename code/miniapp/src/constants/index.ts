// ── 存储键名 ────────────────────────────────────────────────────────────
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'mesh_access_token',
  REFRESH_TOKEN: 'mesh_refresh_token',
  USER_INFO: 'mesh_user_info',
} as const

// ── 五力维度 ─────────────────────────────────────────────────────────────
export const FIVE_POWERS = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const
export type FivePower = (typeof FIVE_POWERS)[number]

export const FIVE_POWER_LABELS: Record<FivePower, string> = {
  INSIGHT: '洞察力',
  CONSTRUCT: '建构力',
  DEDUCE: '推演力',
  ADAPT: '调适力',
  MIGRATE: '迁移力',
}

// 亮色主题下的五力颜色；页面里请通过 useTheme().powerColors 取值（会随亮 / 暗主题切换），不要直接用这个常量
export const FIVE_POWER_COLORS: Record<FivePower, string> = {
  INSIGHT: '#0D9488',
  CONSTRUCT: '#E11D48',
  DEDUCE: '#0EA5E9',   // 天蓝：与系统主色（柔蓝紫）拉开色相，避免混淆
  ADAPT: '#D97706',
  MIGRATE: '#7C3AED',
}

// 五力的图标和一句话简介：测试首页的「测试将评估以下五力」与测试结果页的分数列表共用
export const FIVE_POWER_META: Record<FivePower, { icon: string; desc: string }> = {
  INSIGHT: { icon: 'target', desc: '感知题目关键信息' },
  CONSTRUCT: { icon: 'ruler', desc: '搭建解题框架' },
  DEDUCE: { icon: 'branch', desc: '逻辑推导能力' },
  ADAPT: { icon: 'repeat', desc: '灵活调整策略' },
  MIGRATE: { icon: 'rocket', desc: '跨情境应用' },
}

// 暗色主题下的五力颜色：提亮一档（同后台暗色 --power-*），在近黑底上不发暗
export const FIVE_POWER_COLORS_DARK: Record<FivePower, string> = {
  INSIGHT: '#2DD4BF',
  CONSTRUCT: '#F87171',
  DEDUCE: '#38BDF8',
  ADAPT: '#FCD34D',
  MIGRATE: '#A78BFA',
}

// ── 训练维度 ─────────────────────────────────────────────────────────────
export const TRAINING_DIMENSIONS = [
  'KNOWLEDGE_POINT',
  'UNIT',
  'SEMESTER',
  'ERROR_QUESTIONS',
  'RANDOM',
] as const
export type TrainingDimension = (typeof TRAINING_DIMENSIONS)[number]

export const TRAINING_DIMENSION_LABELS: Record<TrainingDimension, string> = {
  KNOWLEDGE_POINT: '按知识点',
  UNIT: '按单元',
  SEMESTER: '按学期',
  ERROR_QUESTIONS: '错题集',
  RANDOM: '随机练习',
}

// ── 错题状态 ─────────────────────────────────────────────────────────────
export const WRONG_STATUS_LABELS: Record<string, string> = {
  unreview: '未复盘',
  reviewing: '复盘中',
  pending_consolidation: '待巩固',
  aha_achieved: '已突破',
}

// ── 难度 ─────────────────────────────────────────────────────────────────
export const DIFFICULTY_LABELS: Record<string, string> = {
  basic: '基础',
  advanced: '进阶',
  challenge: '挑战',
}

// ── AI 助教会话模式 ──────────────────────────────────────────────────────
export const SESSION_MODE_LABELS: Record<string, string> = {
  free_chat: '自由提问',
  wrong_review: '错题复盘',
  training_error_guidance: '训练介入',
}

// ── 页面路径 ─────────────────────────────────────────────────────────────
export const PAGES = {
  AUTH_LOGIN: '/pages/auth/login',
  AUTH_BIND_PHONE: '/pages/auth/bind-phone',
  TRAINING_HOME: '/pages/training/index',
  TRAINING_SESSION: '/pages/training/session/index',
  TEST_HOME: '/pages/test/index',
  TEST_QUESTIONS: '/pages/test/questions',
  TEST_RESULT: '/pages/test/result',
  ASSISTANT_HOME: '/pages/assistant/index',
  ASSISTANT_CHAT: '/pages/assistant/chat',
  PROFILE_HOME: '/pages/profile/index',
  WRONG_ANSWERS: '/pages/wrong-answers/index',
} as const

// ── 科目 ─────────────────────────────────────────────────────────────────
export const SUBJECT_LABELS: Record<string, string> = {
  MATH: '数学',
  PHYSICS: '物理',
  CHEMISTRY: '化学',
}

export const SUBJECT_ICONS: Record<string, string> = {
  MATH: 'ruler',
  PHYSICS: 'atom',
  CHEMISTRY: 'flask',
}

// ── 学期 ─────────────────────────────────────────────────────────────────
export const SEMESTER_LABELS: Record<string, string> = {
  S1: '上学期',
  S2: '下学期',
}

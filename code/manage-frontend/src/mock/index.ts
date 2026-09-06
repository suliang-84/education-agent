import type { MockMethod } from 'vite-plugin-mock'

const success = (data: unknown) => ({ status: 'success', code: 0, msg: '操作成功', data })
const paginated = (list: unknown[], total: number) =>
  success({ list, total, has_more: false, next_cursor: null })

// Mock 题目数据
const questions = Array.from({ length: 30 }, (_, i) => ({
  id: 5001 + i,
  stem: [
    '几个人一起买一件东西。如果每人出400钱，会多出3400钱；如果每人出300钱，会多出100钱。请建立人数与总价之间的方程关系。',
    '一辆汽车在平直公路上行驶，受到2000N的合力作用，求加速度。',
    '如图所示，△ABC中，已知条件如图，求角B的大小。',
    '科学家发现某湖泊鱼类突然减少，目前有四条线索，请分析最可能的原因。',
    '城市气温数据如下，请分析哪一年的温差最大。',
  ][i % 5],
  solution: '参考解析内容...',
  knowledge_point: ['二元一次方程组', '牛顿第二定律', '三角形', '生态学', '数据分析'][i % 5],
  question_type: ['应用题', '计算题', '证明题', '分析题', '统计题'][i % 5],
  difficulty: ['basic', 'advanced', 'challenge'][i % 3] as 'basic' | 'advanced' | 'challenge',
  status: ['published', 'draft', 'published', 'published', 'archived'][i % 5] as 'published' | 'draft' | 'archived',
  primary_power: ['CONSTRUCT', 'DEDUCE', 'INSIGHT', 'ADAPT', 'MIGRATE'][i % 5],
  secondary_power: ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'MIGRATE', 'ADAPT'][i % 5],
  annotation_status: ['confirmed', 'pending', 'confirmed', 'pending', 'rejected'][i % 5],
  annotation_confidence: [0.92, 0.67, 0.88, 0.71, 0.95][i % 5],
  embedding_status: ['completed', 'pending', 'completed', 'failed', 'completed'][i % 5],
  created_at: '2026-08-25T10:00:00Z',
  updated_at: '2026-08-30T10:00:00Z',
}))

// Mock 标注数据
const annotations = Array.from({ length: 20 }, (_, i) => ({
  id: 301 + i,
  question_id: 5001 + i,
  question_stem: questions[i].stem.substring(0, 50) + '...',
  ai_primary_power: ['CONSTRUCT', 'DEDUCE', 'INSIGHT', 'ADAPT', 'MIGRATE'][i % 5],
  ai_confidence: [0.92, 0.67, 0.88, 0.71, 0.56][i % 5],
  ai_reason: '该题目需要学生建立变量关系，属于建构力训练。题目涉及多条件约束，主要考查学生将语言描述转化为数学关系的能力。',
  confirmed_primary_power: i % 3 === 0 ? ['CONSTRUCT', 'DEDUCE', 'INSIGHT'][i % 3] : undefined,
  annotation_status: ['pending', 'confirmed', 'pending', 'rejected', 'pending'][i % 5],
  created_at: '2026-08-30T10:00:00Z',
}))

// Mock 学生数据
const students = Array.from({ length: 25 }, (_, i) => ({
  id: 1001 + i,
  nickname: ['小明', '小红', '小刚', '小美', '小强', '小李', '小王', '小张', '小赵', '小陈'][i % 10],
  grade: ['初一', '初二', '初三', '高一', '高二'][i % 5],
  subjects: [['数学', '物理'], ['数学'], ['物理', '化学'], ['数学', '物理', '化学']][i % 4],
  phone_masked: `138****${String(8000 + i).padStart(4, '0')}`,
  has_profile: i % 4 !== 0,
  weakest_power: ['CONSTRUCT', 'ADAPT', 'MIGRATE', 'DEDUCE', 'INSIGHT'][i % 5],
  training_count: Math.floor(Math.random() * 30),
  last_login_at: ['2026-08-30T09:00:00Z', '2026-08-29T14:00:00Z', '2026-08-27T10:00:00Z'][i % 3],
  created_at: '2026-07-01T00:00:00Z',
}))

// Mock 审计日志
const auditLogs = Array.from({ length: 30 }, (_, i) => ({
  id: 1 + i,
  admin_id: 1,
  admin_username: 'admin001',
  action_type: ['CONFIRM_ANNOTATION', 'PUBLISH_QUESTION', 'UPDATE_SYSTEM_CONFIG', 'CREATE_TRAINING_CONFIG'][i % 4],
  target_table: ['question_annotations', 'questions', 'system_configs', 'training_configs'][i % 4],
  target_id: 100 + i,
  before_data: { status: 'pending' },
  after_data: { status: 'confirmed', confirmed_at: '2026-08-30T10:00:00Z' },
  ip_address: '192.168.1.1',
  created_at: `2026-08-30T${String(9 + (i % 8)).padStart(2, '0')}:${String(i * 2 % 60).padStart(2, '0')}:00Z`,
}))

const mockRoutes: MockMethod[] = [
  // 登录
  {
    url: '/api/v1/admin/auth/login',
    method: 'post',
    response: () => success({ session_token: 'mock_session_token_abc123' }),
  },
  {
    url: '/api/v1/admin/auth/verify-2fa',
    method: 'post',
    response: () => success({
      access_token: 'mock_access_token_xyz789',
      admin: { id: 1, username: 'admin001', role: 'SUPER_ADMIN' },
    }),
  },
  {
    url: '/api/v1/admin/auth/logout',
    method: 'post',
    response: () => success(null),
  },

  // 题库
  {
    url: '/api/v1/admin/questions',
    method: 'get',
    response: ({ query }) => {
      const page = Number(query.cursor || 0)
      const size = 20
      const filtered = questions.filter(q => {
        if (query.status && q.status !== query.status) return false
        if (query.primary_power && q.primary_power !== query.primary_power) return false
        if (query.difficulty && q.difficulty !== query.difficulty) return false
        if (query.keyword && !q.stem.includes(query.keyword as string)) return false
        return true
      })
      return paginated(filtered.slice(page, page + size), filtered.length)
    },
  },
  {
    url: '/api/v1/admin/questions',
    method: 'post',
    response: ({ body }) => success({ ...body, id: 9999, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), embedding_status: 'pending', annotation_status: 'pending' }),
  },
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)$/,
    method: 'get',
    response: ({ url }) => {
      const id = parseInt(url.split('/').pop() || '5001')
      return success(questions.find(q => q.id === id) || questions[0])
    },
  },
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)$/,
    method: 'put',
    response: ({ body }) => success({ ...questions[0], ...body }),
  },
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)\/publish$/,
    method: 'post',
    response: () => success({ ...questions[0], status: 'published' }),
  },
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)\/archive$/,
    method: 'post',
    response: () => success({ ...questions[0], status: 'archived' }),
  },
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)$/,
    method: 'delete',
    response: () => success(null),
  },

  // 标注
  {
    url: '/api/v1/admin/annotations',
    method: 'get',
    response: ({ query }) => {
      const filtered = annotations.filter(a => {
        if (query.annotation_status && a.annotation_status !== query.annotation_status) return false
        return true
      })
      return paginated(filtered, filtered.length)
    },
  },
  {
    url: /\/api\/v1\/admin\/annotations\/(\d+)\/confirm$/,
    method: 'post',
    response: () => success({ annotation_status: 'confirmed' }),
  },
  {
    url: '/api/v1/admin/annotations/batch-confirm',
    method: 'post',
    response: () => success({ confirmed_count: 52 }),
  },

  // 五力测试题
  {
    url: '/api/v1/admin/cognitive-questions',
    method: 'get',
    response: () => success(Array.from({ length: 20 }, (_, i) => ({
      id: i + 1,
      order_num: i + 1,
      stem: [
        '有一个封闭房间，里面放着完全相同的三杯热水。实验记录如下：杯A敞口、杯B加盖、杯C加盖+毛巾。有人说："只要加盖，就能解释全部差异。" 以下哪一条最能说明这个结论有问题？',
        '小明在解方程时，先把左边化简，得到一个结论，然后他说这个结论对所有整数都成立。你认为他的推理过程有什么问题？',
        '科学家发现某湖泊鱼类突然减少，目前有四条线索：①水温升高 ②外来物种入侵 ③工厂排污 ④捕鱼量增加。哪条线索最需要优先调查？',
      ][i % 3],
      question_type: i % 4 === 0 ? 'OPEN' : 'STANDARD',
      target_power: ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'][i % 5],
      reference_time_sec: [90, 120, 150, 60, 180][i % 5],
      option_scores: { A: [1, 10, 5, 2][i % 4], B: [10, 1, 3, 8][i % 4], C: [4, 3, 10, 1][i % 4], D: [1, 2, 1, 4][i % 4] },
      option_force_weights: i % 4 === 0 ? {
        A: { INSIGHT: 0.6, CONSTRUCT: 0.2, DEDUCE: 0.1, ADAPT: 0.05, MIGRATE: 0.05 },
        B: { INSIGHT: 0.1, CONSTRUCT: 0.6, DEDUCE: 0.15, ADAPT: 0.1, MIGRATE: 0.05 },
        C: { INSIGHT: 0.2, CONSTRUCT: 0.1, DEDUCE: 0.5, ADAPT: 0.1, MIGRATE: 0.1 },
        D: { INSIGHT: 0.1, CONSTRUCT: 0.1, DEDUCE: 0.1, ADAPT: 0.6, MIGRATE: 0.1 },
      } : undefined,
    }))),
  },
  {
    url: /\/api\/v1\/admin\/cognitive-questions\/(\d+)$/,
    method: 'put',
    response: ({ body }) => success(body),
  },

  // 训练配置
  {
    url: '/api/v1/admin/training-configs',
    method: 'get',
    response: () => success(Array.from({ length: 6 }, (_, i) => ({
      id: i + 1,
      version: `v${6 - i}`,
      is_active: i === 0,
      questions_per_session: 5,
      dedup_window: 30,
      weak_threshold: 65,
      severe_weak_bonus: 0.4,
      general_weak_bonus: 0.2,
      difficulty_basic_pct: 50,
      difficulty_advanced_pct: 35,
      difficulty_challenge_pct: 15,
      rag_mode: 'all',
      rag_timeout_sec: 8,
      rag_question_recall: 3,
      rag_strategy_recall: 2,
      rag_similarity_threshold: 0.75,
      ewma_decay: 0.3,
      created_at: `2026-0${8 - i}-25T09:00:00Z`,
      created_by: 'admin001',
    }))),
  },
  {
    url: '/api/v1/admin/training-configs/active',
    method: 'get',
    response: () => success({
      id: 1, version: 'v6', is_active: true, questions_per_session: 5,
      dedup_window: 30, weak_threshold: 65, severe_weak_bonus: 0.4,
      general_weak_bonus: 0.2, difficulty_basic_pct: 50, difficulty_advanced_pct: 35,
      difficulty_challenge_pct: 15, rag_mode: 'all', rag_timeout_sec: 8,
      rag_question_recall: 3, rag_strategy_recall: 2, rag_similarity_threshold: 0.75,
      ewma_decay: 0.3, created_at: '2026-08-25T09:00:00Z', created_by: 'admin001',
    }),
  },
  {
    url: '/api/v1/admin/training-configs',
    method: 'post',
    response: ({ body }) => success({ ...body, id: 99, is_active: true, created_at: new Date().toISOString() }),
  },

  // 系统参数
  {
    url: '/api/v1/admin/system-configs',
    method: 'get',
    response: () => success([
      { key: 'active_llm_provider', value: 'tongyi', description: '当前AI模型供应商（热切换）', updated_at: '2026-08-30T09:00:00Z' },
      { key: 'max_chat_rounds', value: '30', description: '单会话最大对话轮数', updated_at: '2026-08-30T09:00:00Z' },
      { key: 'rag_timeout_sec', value: '8', description: 'RAG生成超时时间（秒）', updated_at: '2026-08-28T10:00:00Z' },
      { key: 'max_token_per_session', value: '15000', description: 'Token会话上限，超出后AI降级', updated_at: '2026-08-25T09:00:00Z' },
      { key: 'review_session_max_min', value: '20', description: '错题复盘时限（分钟）', updated_at: '2026-08-25T09:00:00Z' },
      { key: 'strategy_switch_threshold', value: '2', description: '策略切换阈值（无效次数）', updated_at: '2026-08-25T09:00:00Z' },
      { key: 'max_proactive_per_session', value: '3', description: 'AI主动介入上限（每训练会话）', updated_at: '2026-08-25T09:00:00Z' },
      { key: 'sms_daily_limit', value: '10', description: '同一手机号每日最多发送短信次数', updated_at: '2026-08-25T09:00:00Z' },
    ]),
  },
  {
    url: /\/api\/v1\/admin\/system-configs\/(.+)$/,
    method: 'put',
    response: ({ body }) => success(body),
  },

  // 启发策略
  {
    url: '/api/v1/admin/strategies',
    method: 'get',
    response: () => success([
      { id: 1, name: '苏格拉底提问', code: 'S-SOCRATIC', applicable_powers: '全维度', priority: 1, is_enabled: true, description: '通过连续追问引导学生自主思考，是最常用的基础策略' },
      { id: 2, name: '化简特例', code: 'S-SIMPLIFY', applicable_powers: '调适力', priority: 2, is_enabled: true, description: '将复杂问题简化为特殊情况，降低认知负荷' },
      { id: 3, name: '生活场景类比', code: 'S-ANALOGY', applicable_powers: '洞察力/建构力', priority: 3, is_enabled: true, description: '用熟悉的生活场景类比抽象概念' },
      { id: 4, name: '空间想象', code: 'S-SPATIAL', applicable_powers: '洞察力/推演力', priority: 4, is_enabled: true, description: '引导学生构建空间模型帮助理解' },
      { id: 5, name: '图示引导', code: 'S-DIAGRAM', applicable_powers: '洞察力', priority: 5, is_enabled: true, description: '鼓励学生画图或使用视觉辅助工具' },
      { id: 6, name: '故事叙述', code: 'S-STORY', applicable_powers: '建构力/迁移力', priority: 6, is_enabled: true, description: '将问题包装成故事情节降低抽象感' },
      { id: 7, name: '反例证伪', code: 'S-COUNTER', applicable_powers: '推演力/调适力', priority: 7, is_enabled: true, description: '提供反例引发认知冲突，促进概念修正' },
      { id: 8, name: '节奏/模式感', code: 'S-PATTERN', applicable_powers: '建构力/推演力', priority: 8, is_enabled: true, description: '识别题目中的数量规律和结构模式' },
      { id: 9, name: '已知知识类比', code: 'S-KNOWN', applicable_powers: '迁移力', priority: 9, is_enabled: true, description: '联结学生已掌握的知识，构建迁移桥梁' },
    ]),
  },
  {
    url: /\/api\/v1\/admin\/strategies\/(\d+)$/,
    method: 'put',
    response: ({ body }) => success(body),
  },
  {
    url: '/api/v1/admin/strategies/reorder',
    method: 'post',
    response: () => success(null),
  },

  // 学生管理
  {
    url: '/api/v1/admin/students',
    method: 'get',
    response: ({ query }) => {
      const filtered = students.filter(s => {
        if (query.grade && s.grade !== query.grade) return false
        if (query.has_profile === 'true' && !s.has_profile) return false
        if (query.has_profile === 'false' && s.has_profile) return false
        if (query.keyword && !s.nickname.includes(query.keyword as string)) return false
        return true
      })
      return paginated(filtered, filtered.length)
    },
  },
  {
    url: /\/api\/v1\/admin\/students\/(\d+)$/,
    method: 'get',
    response: ({ url }) => {
      const id = parseInt(url.split('/').pop() || '1001')
      const s = students.find(st => st.id === id) || students[0]
      return success({
        ...s,
        five_power_scores: { INSIGHT: 82, CONSTRUCT: 47, DEDUCE: 74, ADAPT: 55, MIGRATE: 51 },
        ai_analysis: '你具有出色的洞察力——善于从复杂信息中快速抓住关键。但在"建构力"上稍显不足：题目虽然看懂了，却很难把条件之间的关系建立成方程式。',
        profile_updated_at: '2026-08-30T15:00:00Z',
        total_answers: 75,
        accuracy_rate: 0.65,
        parents: [
          { id: 2001, nickname: '小明爸爸', bind_method: '邀请码', bound_at: '2026-07-05T00:00:00Z' },
          { id: 2002, nickname: '小明妈妈', bind_method: '邀请码', bound_at: '2026-08-01T00:00:00Z' },
        ],
      })
    },
  },

  // 审计日志
  {
    url: '/api/v1/admin/audit-logs',
    method: 'get',
    response: () => paginated(auditLogs, auditLogs.length),
  },
  {
    url: /\/api\/v1\/admin\/audit-logs\/(\d+)$/,
    method: 'get',
    response: ({ url }) => {
      const id = parseInt(url.split('/').pop() || '1')
      return success(auditLogs.find(l => l.id === id) || auditLogs[0])
    },
  },

  // 数据看板
  {
    url: '/api/v1/admin/dashboard/stats',
    method: 'get',
    response: () => success({
      date: new Date().toISOString().split('T')[0],
      total_students: 483,
      new_students_today: 12,
      active_students_today: 85,
      students_with_profile: 312,
      completed_test_total: 823,
      training_sessions_today: 156,
      answers_today: 780,
      avg_accuracy: 0.63,
      wrong_answers_today: 198,
      rag_calls_today: 312,
      chat_sessions_today: 89,
      chat_messages_today: 890,
      aha_moments_today: 23,
      token_cost_today: 0.24,
      degradation_rate: 0.02,
      published_questions: 1280,
      draft_questions: 124,
      pending_annotations: 45,
      confirmed_annotations: 1197,
      pending_vectors: 8,
    }),
  },
  {
    url: '/api/v1/admin/dashboard/token-trend',
    method: 'get',
    response: ({ query }) => {
      const days = Number(query.days || 7)
      return success(Array.from({ length: days }, (_, i) => ({
        date: new Date(Date.now() - (days - 1 - i) * 86400000).toISOString().split('T')[0],
        training_cost: 2.1 + Math.random() * 0.8,
        assistant_cost: 1.2 + Math.random() * 0.5,
        test_cost: 0.1 + Math.random() * 0.1,
      })))
    },
  },
  {
    url: '/api/v1/admin/dashboard/user-growth',
    method: 'get',
    response: ({ query }) => {
      const days = Number(query.days || 7)
      return success(Array.from({ length: days }, (_, i) => ({
        date: new Date(Date.now() - (days - 1 - i) * 86400000).toISOString().split('T')[0],
        new_users: Math.floor(6 + Math.random() * 12),
        active_users: Math.floor(70 + Math.random() * 40),
      })))
    },
  },
]

export default mockRoutes

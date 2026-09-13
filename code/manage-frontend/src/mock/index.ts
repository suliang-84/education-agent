import type { MockMethod } from 'vite-plugin-mock'

const success = (data: unknown) => ({ status: 'success', code: 0, msg: '操作成功', data })
const paginated = (list: unknown[], total: number) =>
  success({ list, total, has_more: false, next_cursor: null })

// Mock 题目数据
// 五力权重模板（合计10分）
const powerWeights = [
  { INSIGHT: 2, CONSTRUCT: 5, DEDUCE: 2, ADAPT: 1, MIGRATE: 0 },
  { INSIGHT: 1, CONSTRUCT: 1, DEDUCE: 5, ADAPT: 2, MIGRATE: 1 },
  { INSIGHT: 5, CONSTRUCT: 2, DEDUCE: 1, ADAPT: 1, MIGRATE: 1 },
  { INSIGHT: 2, CONSTRUCT: 1, DEDUCE: 1, ADAPT: 4, MIGRATE: 2 },
  { INSIGHT: 1, CONSTRUCT: 2, DEDUCE: 2, ADAPT: 2, MIGRATE: 3 },
]

const powerThoughts = [
  { INSIGHT: '识别题目中的隐含数量关系', CONSTRUCT: '建立变量与方程的对应模型', DEDUCE: '推导各步骤的逻辑依据', ADAPT: '将结果代入验证是否符合约束', MIGRATE: '联系到生活中类似的分摊情境' },
  { INSIGHT: '观察物理量之间的因果关系', CONSTRUCT: '建立牛顿第二定律的计算模型', DEDUCE: '逐步推导加速度计算过程', ADAPT: '在不同质量/力情境下调整公式', MIGRATE: '迁移至摩擦力、斜面等复杂场景' },
  { INSIGHT: '从图形中识别对称轴和关键角', CONSTRUCT: '构建全等三角形的条件关系', DEDUCE: '逐步证明SAS条件满足', ADAPT: '检验结论与图形几何关系一致', MIGRATE: '迁移到等腰三角形轴对称性' },
  { INSIGHT: '从多条线索中筛选最有价值的一条', CONSTRUCT: '建立因果关系的逻辑框架', DEDUCE: '推演各线索的影响程度', ADAPT: '在证据不足时调整假设', MIGRATE: '联系到其他生态或社会系统问题' },
  { INSIGHT: '从数据表中识别最大差异的年份', CONSTRUCT: '建立温差计算的数学模型', DEDUCE: '逐列计算并比较最大值', ADAPT: '处理异常数据时灵活调整方法', MIGRATE: '迁移到其他统计分析场景' },
]

// 各题型的标准答案模板
const answerTemplates = [
  { type: 'APPLICATION',     final_answer: 'x=33，y=9800（人数33人，总价9800钱）', key_steps: ['设人数为x，总价为y', '由题意建立二元方程组：400x - y = 3400 且 300x - y = 100', '两式相减得100x = 3300，解得x = 33', '代入得y = 9800'] },
  { type: 'APPLICATION',     final_answer: 'a = 2 m/s²', key_steps: ['由牛顿第二定律 F = ma', '已知 F = 2000N，m = 1000kg', '解得 a = F/m = 2 m/s²'] },
  { type: 'APPLICATION',     final_answer: 'BD是AC的垂直平分线，即AD = CD', key_steps: ['在△ABD和△CBD中，AB = CB（等腰三角形），BD = BD（公共边），∠ADB = ∠CDB = 90°', '由RHS可得△ABD ≅ △CBD', '故AD = DC，BD是AC的垂直平分线'] },
  { type: 'SINGLE_CHOICE',   correct: 'B' },
  { type: 'FILL_BLANK',      correct: ['2023', '42.3°C'], accept_range: null },
]

// Mock 题库数据（v1.2.0：5态状态模型 + 五级知识体系 + 题目类型与答案）
const questions = Array.from({ length: 30 }, (_, i) => {
  const statusList = ['published', 'draft', 'pending_review', 'published', 'archived', 'analyzing'] as const
  const status = statusList[i % 6]
  const hasAnalysis = ['published', 'pending_review', 'archived'].includes(status)
  const stems = [
    '几个人一起买一件东西。如果每人出400钱，会多出3400钱；如果每人出300钱，会多出100钱。请建立人数与总价之间的方程关系。',
    '一辆汽车在平直公路上行驶，受到2000N的合力作用，车的质量为1000kg，求加速度。',
    '如图所示，△ABC中，AB=AC，BD是AC的垂线，BD与AC交于D点，求证BD是AC的垂直平分线。',
    '科学家发现某湖泊鱼类突然减少，目前有四条线索：①水温升高 ②外来物种入侵 ③工厂排污 ④捕鱼量增加。哪条线索最需要优先调查？',
    '某城市2021~2025年各月平均气温数据如下表，请分析哪一年的年温差最大。',
  ]
  return {
    id: 5001 + i,
    stem: stems[i % 5],
    image_url: undefined as string | undefined,
    status,
    analysis_round: status === 'pending_review' && i % 7 === 0 ? 2 : 1,
    // AI 分析字段（仅 hasAnalysis 时有值）— 五级知识体系
    subject:          hasAnalysis ? ['数学', '物理', '数学', '生物', '数学'][i % 5] : undefined,
    grade:            hasAnalysis ? ['八年级', '九年级', '八年级', '七年级', '九年级'][i % 5] : undefined,
    semester:         hasAnalysis ? ['上学期', '下学期', '上学期', '下学期', '上学期'][i % 5] : undefined,
    chapter:          hasAnalysis ? ['方程与方程组', '牛顿运动定律', '全等三角形', '生态系统', '统计与概率'][i % 5] : undefined,
    knowledge_points: hasAnalysis ? [['二元一次方程组', '应用题建模'], ['牛顿第二定律'], ['全等三角形', '垂直平分线'], ['生态系统', '调查分析'], ['统计图', '数据分析']][i % 5] : undefined,
    question_type:    hasAnalysis ? ['APPLICATION', 'APPLICATION', 'APPLICATION', 'SINGLE_CHOICE', 'FILL_BLANK'][i % 5] : undefined,
    answer:           hasAnalysis ? answerTemplates[i % 5] : undefined,
    difficulty:       hasAnalysis ? (['basic', 'advanced', 'challenge'] as const)[i % 3] : undefined,
    solution:         hasAnalysis ? ['设人数为x，总价为y。由题意得：400x - y = 3400，300x - y = 100。两式相减得100x = 3300，解得x = 33，y = 9800。', '由牛顿第二定律 F = ma，得 a = F/m = 2000/1000 = 2 m/s²。', '证：在△ABD和△CBD中，BD=BD（公共边），∠BDA=∠BDC=90°（已知BD⊥AC），AB=BC（等腰三角形），故△ABD≅△CBD（RHS），所以AD=DC，即BD是AC的垂直平分线。', '外来物种入侵最可能导致生态链断裂，应优先调查线索②。', '计算每年各月最高温和最低温之差，即年温差，通过比较可知2023年温差最大。'][i % 5] : undefined,
    typical_error:    hasAnalysis ? ['把盈余关系写反（400x+3400=y）', '混淆合力与分力的关系', '忽略垂直条件直接用角度证明', '将相关性误认为因果关系', '未统一单位直接比较'][i % 5] : undefined,
    five_power_weights:  hasAnalysis ? powerWeights[i % 5] : undefined,
    five_power_thoughts: hasAnalysis ? powerThoughts[i % 5] : undefined,
    migration_directions: hasAnalysis ? [['班级活动收费', '租车收费'], ['斜面加速', '电梯运动'], ['等腰三角形', '角平分线'], ['水资源保护', '城市扩张'], ['经济数据分析', '气候变化']][i % 5] : undefined,
    embedding_status: status === 'published' ? (['completed', 'completed', 'failed'][i % 3]) : 'pending',
    created_at: '2026-08-25T10:00:00Z',
    updated_at: '2026-08-30T10:00:00Z',
  }
})

// Mock 学生数据
const students = Array.from({ length: 25 }, (_, i) => ({
  id: 1001 + i,
  nickname: ['小明', '小红', '小刚', '小美', '小强', '小李', '小王', '小张', '小赵', '小陈'][i % 10],
  grade: ['初一', '初二', '初三', '高一', '高二'][i % 5],
  subjects: [['数学', '物理'], ['数学'], ['物理', '化学'], ['数学', '物理', '化学']][i % 4],
  phone_masked: `138****${String(8000 + i).padStart(4, '0')}`,
  has_profile: i % 4 !== 0,
  weakest_power: ['CONSTRUCT', 'ADAPT', 'MIGRATE', 'DEDUCE', 'INSIGHT'][i % 5],
  training_count: (i * 7) % 30,
  last_login_at: ['2026-08-30T09:00:00Z', '2026-08-29T14:00:00Z', '2026-08-27T10:00:00Z'][i % 3],
  created_at: '2026-07-01T00:00:00Z',
  parent_count: [2, 1, 0, 1, 2][i % 5],
}))

// Mock 家长数据
const parents = Array.from({ length: 18 }, (_, i) => ({
  id: 2001 + i,
  nickname: ['小明爸爸', '小红妈妈', '张父', '李母', '刚爸', '美妈', '强父', '李妈', '王父'][i % 9],
  phone_masked: `139****${String(9000 + i).padStart(4, '0')}`,
  is_confirmed: i % 5 !== 4,
  last_login_at: ['2026-08-30T08:00:00Z', '2026-08-28T20:00:00Z', '2026-08-25T12:00:00Z'][i % 3],
  created_at: '2026-07-05T00:00:00Z',
  bound_students: [
    {
      id: 1001 + (i % 25),
      nickname: ['小明', '小红', '小刚', '小美', '小强'][i % 5],
      grade: ['初三', '高一', '初一', '高二', '初二'][i % 5],
      bind_method: ['INVITE_CODE', 'PARENT_SELF', 'ADMIN'][i % 3],
      bound_at: '2026-07-05T00:00:00Z',
    },
    ...(i % 3 === 0 ? [{
      id: 1001 + ((i + 5) % 25),
      nickname: ['小张', '小赵', '小陈'][i % 3],
      grade: ['初二', '高一', '初三'][i % 3],
      bind_method: 'ADMIN',
      bound_at: '2026-08-01T00:00:00Z',
    }] : []),
  ],
}))

// Mock 管理员账号数据
const adminUsers = [
  { id: 1, username: 'admin001', display_name: '系统管理员', phone_masked: '138****1111', role: 'SUPER_ADMIN', is_active: true, last_login_at: '2026-09-07T09:00:00Z', created_at: '2026-01-01T00:00:00Z' },
  { id: 2, username: 'ops001',   display_name: '运营专员',   phone_masked: '139****2222', role: 'ADMIN',       is_active: true, last_login_at: '2026-09-06T14:00:00Z', created_at: '2026-03-01T00:00:00Z' },
  { id: 3, username: 'content01',display_name: '内容编辑',   phone_masked: '136****3333', role: 'ADMIN',       is_active: false, last_login_at: '2026-08-20T10:00:00Z', created_at: '2026-04-01T00:00:00Z' },
  { id: 4, username: 'ops002',   display_name: '运营助理',   phone_masked: '135****4444', role: 'ADMIN',       is_active: true, last_login_at: '2026-09-05T16:00:00Z', created_at: '2026-06-01T00:00:00Z' },
]

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

  // 题库（v1.2.0：新增 analyze / reject 接口，5态状态模型）
  {
    url: '/api/v1/admin/questions',
    method: 'get',
    response: ({ query }) => {
      const page = Number(query.cursor || 0)
      const size = 20
      const filtered = questions.filter(q => {
        if (query.status && q.status !== query.status) return false
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
    response: ({ body }) => success({
      ...(body as object),
      id: Math.floor(Math.random() * 9000) + 6000,
      status: 'draft',
      analysis_round: 0,
      embedding_status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }),
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
    response: ({ body, url }) => {
      const id = parseInt((url as string).match(/\/(\d+)$/)?.[1] || '5001')
      const q = questions.find(q => q.id === id) || questions[0]
      return success({ ...q, ...(body as object), updated_at: new Date().toISOString() })
    },
  },
  // 触发大模型分析（draft → analyzing → pending_review，Mock 直接返回 pending_review）
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)\/analyze$/,
    method: 'post',
    response: ({ url }) => {
      const id = parseInt((url as string).match(/\/(\d+)\/analyze/)?.[1] || '5001')
      const q = questions.find(q => q.id === id) || questions[0]
      return success({ ...q, status: 'pending_review', analysis_round: (q.analysis_round || 0) + 1,
        // 五级知识体系
        subject: '数学', grade: '八年级', semester: '上学期', chapter: '方程与方程组',
        knowledge_points: ['二元一次方程组', '应用题建模'],
        // 题目属性
        question_type: 'APPLICATION',
        answer: { type: 'APPLICATION', final_answer: 'x=33，y=9800（人数33人，总价9800钱）', key_steps: ['设人数为x，总价为y', '由题意建立方程组：400x - y = 3400 且 300x - y = 100', '两式相减得100x = 3300，解得x = 33', '代入得y = 9800'] },
        difficulty: 'basic',
        solution: '设人数为x，总价为y。由题意得：400x - y = 3400，300x - y = 100。两式相减得100x = 3300，解得x = 33，y = 9800。',
        typical_error: '把盈余关系写反（400x+3400=y）',
        five_power_weights: { INSIGHT: 2, CONSTRUCT: 5, DEDUCE: 2, ADAPT: 1, MIGRATE: 0 },
        five_power_thoughts: { INSIGHT: '识别题目中的隐含数量关系', CONSTRUCT: '建立变量与方程的对应模型', DEDUCE: '推导各步骤的逻辑依据', ADAPT: '将结果代入验证是否符合约束', MIGRATE: '联系到生活中类似的分摊情境' },
        migration_directions: ['班级活动收费', '租车收费'],
        updated_at: new Date().toISOString(),
      })
    },
  },
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)\/publish$/,
    method: 'post',
    response: ({ url }) => {
      const id = parseInt((url as string).match(/\/(\d+)\/publish/)?.[1] || '5001')
      const q = questions.find(q => q.id === id) || questions[0]
      return success({ ...q, status: 'published', embedding_status: 'pending', updated_at: new Date().toISOString() })
    },
  },
  // 驳回并自动重新分析（pending_review → analyzing）
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)\/reject$/,
    method: 'post',
    response: ({ url }) => {
      const id = parseInt((url as string).match(/\/(\d+)\/reject/)?.[1] || '5001')
      const q = questions.find(q => q.id === id) || questions[0]
      return success({ ...q, status: 'analyzing', updated_at: new Date().toISOString() })
    },
  },
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)\/archive$/,
    method: 'post',
    response: ({ url }) => {
      const id = parseInt((url as string).match(/\/(\d+)\/archive/)?.[1] || '5001')
      const q = questions.find(q => q.id === id) || questions[0]
      return success({ ...q, status: 'archived', updated_at: new Date().toISOString() })
    },
  },
  {
    url: /\/api\/v1\/admin\/questions\/(\d+)$/,
    method: 'delete',
    response: () => success(null),
  },
  {
    url: '/api/v1/admin/questions/batch-import',
    method: 'post',
    response: ({ body }) => {
      const stems = (body as { stems?: string[] }).stems || []
      return success({ imported_count: stems.length, message: `已创建 ${stems.length} 条题干，AI 分析任务已提交` })
    },
  },

  // 五力测试题（v1.4.0 结构：answers JSONB，无 question_type/target_power/option_scores）
  {
    url: '/api/v1/admin/cognitive-questions',
    method: 'get',
    response: () => success(Array.from({ length: 25 }, (_, i) => {
      // 前18道已发布，19-20草稿，21-22已下架，23-24草稿
      const status = i < 18 ? 'published' : i < 20 ? 'draft' : i < 22 ? 'archived' : 'draft'
      const stems = [
        '有一个封闭房间，里面放着完全相同的三杯热水。实验记录如下：杯A敞口、杯B加盖、杯C加盖+毛巾。有人说："只要加盖，就能解释全部差异。" 以下哪一条最能说明这个结论有问题？',
        '小明在解方程时，先把左边化简，得到一个结论，然后他说这个结论对所有整数都成立。你认为他的推理过程有什么问题？',
        '科学家发现某湖泊鱼类突然减少，目前有四条线索：①水温升高 ②外来物种入侵 ③工厂排污 ④捕鱼量增加。哪条线索最需要优先调查？',
        '一位建筑师设计了一栋大楼，但施工方发现原材料成本超出预算30%。建筑师提出三个方案：①减少楼层数 ②使用替代材料 ③延期施工等待价格下降。请分析哪个方案最合理？',
        '实验报告中发现一处数据异常：对照组的数值比实验组还要高。以下哪种解释最能说明这个现象？',
      ]
      // answers 模板：每道题4个选项，每个选项含文本+五力权重（合计=1.0）
      const answerSets = [
        [
          { key: 'A', text: '杯A、B、C最终都会变凉，加盖只影响速度', force_weights: { INSIGHT: 0.10, CONSTRUCT: 0.05, DEDUCE: 0.05, ADAPT: 0.70, MIGRATE: 0.10 } },
          { key: 'B', text: 'B和C都加了盖，但结果仍然不同，说明"加盖"不能解释全部差异', force_weights: { INSIGHT: 0.70, CONSTRUCT: 0.10, DEDUCE: 0.10, ADAPT: 0.05, MIGRATE: 0.05 } },
          { key: 'C', text: '毛巾起到了隔热作用，是加盖之外的因素', force_weights: { INSIGHT: 0.30, CONSTRUCT: 0.20, DEDUCE: 0.20, ADAPT: 0.20, MIGRATE: 0.10 } },
          { key: 'D', text: '三杯水都不会变凉，因为房间是封闭的', force_weights: { INSIGHT: 0.10, CONSTRUCT: 0.10, DEDUCE: 0.10, ADAPT: 0.10, MIGRATE: 0.60 } },
        ],
        [
          { key: 'A', text: '他的推理逻辑正确，只要左边成立，右边也成立', force_weights: { INSIGHT: 0.15, CONSTRUCT: 0.60, DEDUCE: 0.10, ADAPT: 0.10, MIGRATE: 0.05 } },
          { key: 'B', text: '缺少对"所有整数"的穷举验证，特例可能推翻结论', force_weights: { INSIGHT: 0.20, CONSTRUCT: 0.10, DEDUCE: 0.55, ADAPT: 0.10, MIGRATE: 0.05 } },
          { key: 'C', text: '方程化简本身有误，导致结论错误', force_weights: { INSIGHT: 0.35, CONSTRUCT: 0.20, DEDUCE: 0.25, ADAPT: 0.15, MIGRATE: 0.05 } },
          { key: 'D', text: '应该先验证负整数的情况再下结论', force_weights: { INSIGHT: 0.25, CONSTRUCT: 0.15, DEDUCE: 0.30, ADAPT: 0.20, MIGRATE: 0.10 } },
        ],
        [
          { key: 'A', text: '水温升高是最直接的物理原因，优先调查', force_weights: { INSIGHT: 0.20, CONSTRUCT: 0.10, DEDUCE: 0.55, ADAPT: 0.10, MIGRATE: 0.05 } },
          { key: 'B', text: '外来物种入侵最可能造成生态链断裂，影响最大', force_weights: { INSIGHT: 0.55, CONSTRUCT: 0.15, DEDUCE: 0.15, ADAPT: 0.10, MIGRATE: 0.05 } },
          { key: 'C', text: '工厂排污属于人为因素，更易追责和控制', force_weights: { INSIGHT: 0.15, CONSTRUCT: 0.55, DEDUCE: 0.15, ADAPT: 0.10, MIGRATE: 0.05 } },
          { key: 'D', text: '四条线索都有可能，应同时调查', force_weights: { INSIGHT: 0.10, CONSTRUCT: 0.10, DEDUCE: 0.20, ADAPT: 0.55, MIGRATE: 0.05 } },
        ],
        [
          { key: 'A', text: '减少楼层数，直接降低总成本', force_weights: { INSIGHT: 0.10, CONSTRUCT: 0.15, DEDUCE: 0.20, ADAPT: 0.50, MIGRATE: 0.05 } },
          { key: 'B', text: '使用替代材料在保证质量前提下控制成本', force_weights: { INSIGHT: 0.15, CONSTRUCT: 0.50, DEDUCE: 0.15, ADAPT: 0.15, MIGRATE: 0.05 } },
          { key: 'C', text: '延期施工等待材料降价，规避当前压力', force_weights: { INSIGHT: 0.20, CONSTRUCT: 0.10, DEDUCE: 0.15, ADAPT: 0.05, MIGRATE: 0.50 } },
          { key: 'D', text: '需要综合评估三个方案的风险和收益后再决定', force_weights: { INSIGHT: 0.50, CONSTRUCT: 0.15, DEDUCE: 0.20, ADAPT: 0.10, MIGRATE: 0.05 } },
        ],
        [
          { key: 'A', text: '实验组操作失误，导致数据偏低', force_weights: { INSIGHT: 0.30, CONSTRUCT: 0.10, DEDUCE: 0.45, ADAPT: 0.10, MIGRATE: 0.05 } },
          { key: 'B', text: '对照组受到了未控制变量的干扰', force_weights: { INSIGHT: 0.55, CONSTRUCT: 0.15, DEDUCE: 0.15, ADAPT: 0.10, MIGRATE: 0.05 } },
          { key: 'C', text: '数据记录时发生了组别对调', force_weights: { INSIGHT: 0.20, CONSTRUCT: 0.55, DEDUCE: 0.10, ADAPT: 0.10, MIGRATE: 0.05 } },
          { key: 'D', text: '实验设计本身存在根本性缺陷', force_weights: { INSIGHT: 0.40, CONSTRUCT: 0.20, DEDUCE: 0.25, ADAPT: 0.10, MIGRATE: 0.05 } },
        ],
      ]
      return {
        id: i + 1,
        question_no: i + 1,
        display_order: i + 1,
        description: ['测量学生在面对冲突证据时的洞察力倾向', '考察学生的推演能力与归纳逻辑', '评估面对多因素问题时的洞察与建构能力', '衡量学生在资源约束下的调适与迁移思维', '测量科学推理中对系统误差的识别能力'][i % 5],
        stem: stems[i % 5],
        answers: answerSets[i % 5],
        reference_time_sec: [90, 120, 150, 60, 180][i % 5],
        status,
        created_at: '2026-08-25T10:00:00Z',
        updated_at: '2026-09-01T10:00:00Z',
      }
    })),
  },
  {
    url: '/api/v1/admin/cognitive-questions',
    method: 'post',
    response: ({ body }) => success({
      ...body,
      id: Math.floor(Math.random() * 9000) + 1000,
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }),
  },
  {
    url: /\/api\/v1\/admin\/cognitive-questions\/(\d+)$/,
    method: 'put',
    response: ({ body }) => success({ ...body, updated_at: new Date().toISOString() }),
  },
  {
    url: /\/api\/v1\/admin\/cognitive-questions\/(\d+)\/publish$/,
    method: 'post',
    response: ({ url }) => {
      const id = Number((url as string).match(/\/(\d+)\/publish/)?.[1])
      return success({ id, status: 'published', updated_at: new Date().toISOString() })
    },
  },
  {
    url: /\/api\/v1\/admin\/cognitive-questions\/(\d+)\/archive$/,
    method: 'post',
    response: ({ url }) => {
      const id = Number((url as string).match(/\/(\d+)\/archive/)?.[1])
      return success({ id, status: 'archived', updated_at: new Date().toISOString() })
    },
  },
  {
    url: /\/api\/v1\/admin\/cognitive-questions\/(\d+)$/,
    method: 'delete',
    response: () => success(null),
  },

  // 训练配置（v2.0：全局算法参数 + 五维度参数）

  // ── 全局算法参数 ──
  {
    url: '/api/v1/admin/training-configs/global',
    method: 'get',
    response: () => success(Array.from({ length: 4 }, (_, i) => ({
      id: i + 1, version: `v${4 - i}`, is_active: i === 0,
      rag_mode: 'all', rag_timeout_sec: 8, rag_question_recall: 3,
      rag_strategy_recall: 2, rag_similarity_threshold: 0.75,
      ewma_decay: i === 0 ? 0.3 : 0.25,
      is_correct_threshold: 0.70,
      created_at: `2026-0${9 - i}-01T09:00:00Z`, created_by: 'admin001',
    }))),
  },
  {
    url: '/api/v1/admin/training-configs/global/active',
    method: 'get',
    response: () => success({
      id: 1, version: 'v4', is_active: true,
      rag_mode: 'all', rag_timeout_sec: 8, rag_question_recall: 3,
      rag_strategy_recall: 2, rag_similarity_threshold: 0.75,
      ewma_decay: 0.3, is_correct_threshold: 0.70,
      created_at: '2026-09-01T09:00:00Z', created_by: 'admin001',
    }),
  },
  {
    url: '/api/v1/admin/training-configs/global',
    method: 'post',
    response: ({ body }) => success({ ...(body as object), id: 99, is_active: true, created_at: new Date().toISOString(), created_by: 'admin001' }),
  },

  // ── 各维度训练参数 ──
  {
    url: /\/api\/v1\/admin\/training-configs\/dimension\/([a-z_]+)$/,
    method: 'get',
    response: ({ url }) => {
      const mode = (url as string).match(/\/dimension\/([a-z_]+)$/)?.[1] || 'knowledge_point'
      const defaults: Record<string, object> = {
        knowledge_point: { questions_per_session: 5,  dedup_window: 30,  difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15, weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2 },
        chapter:         { questions_per_session: 8,  dedup_window: 50,  difficulty_basic_pct: 40, difficulty_advanced_pct: 40, difficulty_challenge_pct: 20, weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2 },
        semester:        { questions_per_session: 10, dedup_window: 100, difficulty_basic_pct: 30, difficulty_advanced_pct: 40, difficulty_challenge_pct: 30, weak_threshold: 55, severe_weak_bonus: 0.2, general_weak_bonus: 0.1 },
        wrong_answer:    { questions_per_session: 5,  dedup_window: 10,  difficulty_basic_pct: 0,  difficulty_advanced_pct: 0,  difficulty_challenge_pct: 0,  weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2, wrong_sort_by: 'error_count', new_question_mix_ratio: 0.2, consecutive_correct_to_remove: 3 },
        random:          { questions_per_session: 5,  dedup_window: 20,  difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15, weak_threshold: 65, severe_weak_bonus: 0.1, general_weak_bonus: 0.05 },
      }
      const d = defaults[mode] || defaults['knowledge_point']
      return success(Array.from({ length: 3 }, (_, i) => ({
        id: i + 1, mode, version: `v${3 - i}`, is_active: i === 0,
        ...d,
        created_at: `2026-0${9 - i}-01T10:00:00Z`, created_by: 'admin001',
      })))
    },
  },
  {
    url: /\/api\/v1\/admin\/training-configs\/dimension\/([a-z_]+)\/active$/,
    method: 'get',
    response: ({ url }) => {
      const mode = (url as string).match(/\/dimension\/([a-z_]+)\/active/)?.[1] || 'knowledge_point'
      const defaults: Record<string, object> = {
        knowledge_point: { questions_per_session: 5,  dedup_window: 30,  difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15, weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2 },
        chapter:         { questions_per_session: 8,  dedup_window: 50,  difficulty_basic_pct: 40, difficulty_advanced_pct: 40, difficulty_challenge_pct: 20, weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2 },
        semester:        { questions_per_session: 10, dedup_window: 100, difficulty_basic_pct: 30, difficulty_advanced_pct: 40, difficulty_challenge_pct: 30, weak_threshold: 55, severe_weak_bonus: 0.2, general_weak_bonus: 0.1 },
        wrong_answer:    { questions_per_session: 5,  dedup_window: 10,  difficulty_basic_pct: 0,  difficulty_advanced_pct: 0,  difficulty_challenge_pct: 0,  weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2, wrong_sort_by: 'error_count', new_question_mix_ratio: 0.2, consecutive_correct_to_remove: 3 },
        random:          { questions_per_session: 5,  dedup_window: 20,  difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15, weak_threshold: 65, severe_weak_bonus: 0.1, general_weak_bonus: 0.05 },
      }
      const d = defaults[mode] || defaults['knowledge_point']
      return success({ id: 1, mode, version: 'v3', is_active: true, ...d, created_at: '2026-09-01T10:00:00Z', created_by: 'admin001' })
    },
  },
  {
    url: /\/api\/v1\/admin\/training-configs\/dimension\/([a-z_]+)$/,
    method: 'post',
    response: ({ body }) => success({ ...(body as object), id: Math.floor(Math.random() * 900) + 100, is_active: true, created_at: new Date().toISOString(), created_by: 'admin001' }),
  },

  // 旧版兼容接口
  {
    url: '/api/v1/admin/training-configs',
    method: 'get',
    response: () => success(Array.from({ length: 6 }, (_, i) => ({
      id: i + 1, version: `v${6 - i}`, is_active: i === 0,
      questions_per_session: 5, dedup_window: 30, weak_threshold: 65,
      severe_weak_bonus: 0.4, general_weak_bonus: 0.2,
      difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15,
      rag_mode: 'all', rag_timeout_sec: 8, rag_question_recall: 3,
      rag_strategy_recall: 2, rag_similarity_threshold: 0.75,
      ewma_decay: 0.3, created_at: `2026-0${8 - i}-25T09:00:00Z`, created_by: 'admin001',
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
    response: ({ body }) => success({ ...(body as object), id: 99, is_active: true, created_at: new Date().toISOString() }),
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
          { id: 2001, nickname: '小明爸爸', phone_masked: '138****8888', bind_method: 'ADMIN',       bind_status: 'active', bound_at: '2026-07-05T00:00:00Z' },
          { id: 2002, nickname: '小明妈妈', phone_masked: '139****9999', bind_method: 'INVITE_CODE',  bind_status: 'active', bound_at: '2026-08-01T00:00:00Z' },
        ],
      })
    },
  },

  // 解绑家长
  {
    url: /\/api\/v1\/admin\/students\/(\d+)\/unbind-parent$/,
    method: 'post',
    response: () => success(null),
  },

  // 知识点练习统计
  {
    url: /\/api\/v1\/admin\/students\/(\d+)\/kp-stats$/,
    method: 'get',
    response: () => success([
      { knowledge_point: '二元一次方程组应用题', practice_count: 12, error_rate: 0.583, is_stat_valid: true },
      { knowledge_point: '一次函数图像与性质', practice_count: 9,  error_rate: 0.333, is_stat_valid: true },
      { knowledge_point: '一次函数实际应用', practice_count: 6,  error_rate: 0.167, is_stat_valid: true },
      { knowledge_point: '相似三角形判定', practice_count: 5,  error_rate: 0.400, is_stat_valid: true },
      { knowledge_point: '二元一次方程组图形问题', practice_count: 3,  error_rate: null, is_stat_valid: false },
      { knowledge_point: '不等式与不等式组', practice_count: 1,  error_rate: null, is_stat_valid: false },
    ]),
  },

  // AI助教提示词摘要
  {
    url: /\/api\/v1\/admin\/students\/(\d+)\/ai-prompt-summary$/,
    method: 'get',
    response: () => success({
      student_id: 1001,
      learning_summary: '学生小明，初三（G9）上学期，主要学习数学和物理。五力测试显示洞察力82分（优势），建构力47分（主要薄弱点），推演力74分，调适力61分，迁移力51分，推荐训练模式为TRAIN_WEAKNESS。\n\n近期训练情况：累计训练15次，近7天活跃5天，整体正确率65%。建构力维度正确率仅41%，是当前核心突破方向。高频错题集中在二元一次方程组应用（错误率58%）、一次函数实际应用（41%）。',
      personal_insight: '小明喜欢打篮球，自称是湖人队球迷。近期期中考试压力较大，在与AI对话中提到"最近有点焦虑，感觉数学学不进去"。对游戏角色类比（如用RPG升级类比五力提升）反应积极，aha时刻多出现在此类场景。家庭方面：爸爸比较严格，妈妈更温和，学习上压力来自家长期望。建议AI助教多用运动/游戏类比，语气轻松不说教。',
      full_prompt_preview: '你是小明的专属AI数学/物理助教。\n\n【学生学情】\n学生小明，初三（G9）上学期，主要学习数学和物理。五力测试显示洞察力82分（优势），建构力47分（主要薄弱点）……\n\n【个人洞察】\n小明喜欢打篮球，自称是湖人队球迷……建议多用运动/游戏类比。',
      updated_at: '2026-09-12T15:30:00Z',
    }),
  },
  {
    url: /\/api\/v1\/admin\/students\/(\d+)\/ai-prompt-summary$/,
    method: 'put',
    response: ({ body }) => success({ ...(body as object), updated_at: new Date().toISOString() }),
  },
  {
    url: /\/api\/v1\/admin\/students\/(\d+)\/ai-prompt-summary\/regenerate$/,
    method: 'post',
    response: () => success({ message: '学习信息摘要重新生成任务已提交，约 30 秒后完成' }),
  },

  // 个人洞察条目
  {
    url: /\/api\/v1\/admin\/students\/(\d+)\/prompt-insights$/,
    method: 'get',
    response: () => success([
      { id: 4, content: '近期期中考试压力，有焦虑情绪', source: 'AI', created_at: '2026-09-10T14:20:00Z' },
      { id: 3, content: '喜欢用游戏类比理解知识，反应积极', source: 'AI', created_at: '2026-09-08T10:05:00Z' },
      { id: 2, content: '补充：爸爸较严格，建议AI语气温和', source: 'ADMIN', created_at: '2026-09-05T09:30:00Z' },
      { id: 1, content: '自称湖人球迷，喜欢打篮球', source: 'AI', created_at: '2026-08-30T16:45:00Z' },
    ]),
  },
  {
    url: /\/api\/v1\/admin\/students\/(\d+)\/prompt-insights$/,
    method: 'post',
    response: ({ body }) => success({
      id: Math.floor(Math.random() * 9000) + 100,
      ...(body as object),
      source: 'ADMIN',
      created_at: new Date().toISOString(),
    }),
  },

  // 家长管理
  {
    url: '/api/v1/admin/parents',
    method: 'get',
    response: ({ query }) => {
      const kw = (query.keyword as string) || ''
      const filtered = parents.filter(p =>
        !kw || p.nickname.includes(kw) || p.phone_masked.includes(kw)
      )
      return paginated(filtered, filtered.length)
    },
  },
  {
    url: /\/api\/v1\/admin\/parents\/(\d+)\/unbind$/,
    method: 'post',
    response: () => success(null),
  },

  // 管理员账号管理
  {
    url: '/api/v1/admin/admin-users',
    method: 'get',
    response: () => success(adminUsers),
  },
  {
    url: '/api/v1/admin/admin-users',
    method: 'post',
    response: ({ body }) => success({
      ...body,
      id: Math.floor(Math.random() * 900) + 100,
      phone_masked: (body as Record<string, string>).phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') || '',
      role: 'ADMIN',
      is_active: true,
      last_login_at: null,
      created_at: new Date().toISOString(),
    }),
  },
  {
    url: /\/api\/v1\/admin\/admin-users\/(\d+)\/status$/,
    method: 'put',
    response: ({ body }) => success(body),
  },
  {
    url: /\/api\/v1\/admin\/admin-users\/(\d+)\/reset-password$/,
    method: 'post',
    response: () => success({ message: '临时密码已发送至管理员手机号' }),
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

  // 子页详细数据

  // 14.2.2 用户增长分析
  {
    url: '/api/v1/admin/dashboard/user-growth-detail',
    method: 'get',
    response: ({ query }) => {
      const days = Number(query.days || 30)
      return success({
        daily_new_users: Array.from({ length: days }, (_, i) => ({
          date: new Date(Date.now() - (days - 1 - i) * 86400000).toISOString().split('T')[0],
          new_users: Math.floor(6 + Math.random() * 12),
          active_users: Math.floor(70 + Math.random() * 40),
        })),
        retention_funnel: [
          { stage: '注册用户',     count: 1024, pct: 100 },
          { stage: '完成五力测试', count: 823,  pct: 80 },
          { stage: '参与训练',     count: 568,  pct: 55 },
          { stage: '使用AI助教',   count: 312,  pct: 30 },
          { stage: '产生理解突破', count: 186,  pct: 18 },
        ],
        grade_distribution: [
          { grade: '初一', count: 82,  pct: 8 },
          { grade: '初二', count: 123, pct: 12 },
          { grade: '初三', count: 225, pct: 22 },
          { grade: '高一', count: 286, pct: 28 },
          { grade: '高二', count: 205, pct: 20 },
          { grade: '高三', count: 103, pct: 10 },
        ],
        subject_preference: [
          { subject: '数学', pct: 92 },
          { subject: '物理', pct: 75 },
          { subject: '化学', pct: 58 },
        ],
      })
    },
  },

  // 14.2.3 五力测试分析
  {
    url: '/api/v1/admin/dashboard/five-force-analysis',
    method: 'get',
    response: () => success({
      summary: { total_tests: 1024, today_tests: 38, retest_rate: 0.24, completion_rate: 0.85, avg_duration_min: 18 },
      avg_scores: { INSIGHT: 68, CONSTRUCT: 47, DEDUCE: 72, ADAPT: 61, MIGRATE: 54 },
      weakness_distribution: [
        { power: '建构力', power_key: 'CONSTRUCT', pct: 38 },
        { power: '迁移力', power_key: 'MIGRATE',   pct: 29 },
        { power: '调适力', power_key: 'ADAPT',     pct: 18 },
        { power: '推演力', power_key: 'DEDUCE',    pct: 10 },
        { power: '洞察力', power_key: 'INSIGHT',   pct: 5 },
      ],
    }),
  },

  // 14.2.4 AI助教效果分析
  {
    url: '/api/v1/admin/dashboard/ai-teaching-analysis',
    method: 'get',
    response: ({ query }) => {
      const days = Number(query.days || 7)
      return success({
        summary: { aha_total: 186, avg_rounds: 6.2, breakthrough_rate: 0.24, review_breakthrough_rate: 0.38, silence_rate: 0.08 },
        session_mode_distribution: [
          { mode: '自由提问', pct: 45, color: '#4F46E5' },
          { mode: '错题复盘', pct: 38, color: '#10B981' },
          { mode: '训练介入', pct: 17, color: '#F59E0B' },
        ],
        strategy_effectiveness: [
          { name: '苏格拉底提问',   uses: 3241, success_rate: 0.81 },
          { name: '生活场景类比',   uses: 2186, success_rate: 0.74 },
          { name: '化简特例',       uses: 1843, success_rate: 0.68 },
          { name: '反例证伪',       uses: 1204, success_rate: 0.62 },
          { name: '空间想象',       uses: 892,  success_rate: 0.58 },
          { name: '图示引导',       uses: 764,  success_rate: 0.55 },
          { name: '故事叙述',       uses: 623,  success_rate: 0.52 },
          { name: '节奏/模式感',   uses: 512,  success_rate: 0.49 },
          { name: '已知知识类比',   uses: 389,  success_rate: 0.46 },
        ],
        aha_trend: Array.from({ length: days }, (_, i) => ({
          date: new Date(Date.now() - (days - 1 - i) * 86400000).toISOString().split('T')[0],
          aha_count: Math.floor(18 + Math.random() * 15),
          session_count: Math.floor(80 + Math.random() * 30),
          message_count: Math.floor(700 + Math.random() * 200),
        })),
      })
    },
  },

  // 14.2.5 错题集分析
  {
    url: '/api/v1/admin/dashboard/error-questions-analysis',
    method: 'get',
    response: () => success({
      summary: { total_errors: 8432, review_rate: 0.38, breakthrough_rate: 0.62 },
      review_status_distribution: [
        { status: '未复盘',     count: 5228, pct: 62, color: '#94A3B8' },
        { status: '已突破',     count: 1939, pct: 23, color: '#10B981' },
        { status: '待巩固',     count: 759,  pct: 9,  color: '#F59E0B' },
        { status: '复盘进行中', count: 506,  pct: 6,  color: '#4F46E5' },
      ],
      power_distribution: [
        { power: '建构力', power_key: 'CONSTRUCT', pct: 35 },
        { power: '推演力', power_key: 'DEDUCE',    pct: 28 },
        { power: '迁移力', power_key: 'MIGRATE',   pct: 18 },
        { power: '调适力', power_key: 'ADAPT',     pct: 12 },
        { power: '洞察力', power_key: 'INSIGHT',   pct: 7 },
      ],
      top_error_questions: [
        { rank: 1, stem: '几个人一起买东西，每人400多出3400，每人300多出100...', error_count: 128, power: '建构力', power_key: 'CONSTRUCT' },
        { rank: 2, stem: '身高每天变成前一天的90%，以下判断哪个正确？',           error_count: 94,  power: '推演力', power_key: 'DEDUCE' },
        { rank: 3, stem: '银行/细菌/社交网络增长方式相同的是哪一项？',             error_count: 87,  power: '迁移力', power_key: 'MIGRATE' },
        { rank: 4, stem: '衣服让人感觉暖和是因为衣服自身产生热量？',               error_count: 76,  power: '调适力', power_key: 'ADAPT' },
        { rank: 5, stem: '如图所示，△ABC中AB=AC，BD是AC的垂线，求证BD是...', error_count: 68,  power: '推演力', power_key: 'DEDUCE' },
        { rank: 6, stem: '城市气温数据如下，哪一年的年温差最大？',                 error_count: 61,  power: '洞察力', power_key: 'INSIGHT' },
        { rank: 7, stem: '小明发现两组数据差距很大，请分析最可能的原因...',         error_count: 54,  power: '洞察力', power_key: 'INSIGHT' },
        { rank: 8, stem: '以下哪种情况下，增大压力能提高摩擦力？',                 error_count: 48,  power: '调适力', power_key: 'ADAPT' },
        { rank: 9, stem: '从生物学角度解释：为什么北极熊比普通熊更耐寒？',         error_count: 43,  power: '迁移力', power_key: 'MIGRATE' },
        { rank: 10, stem: '实验报告中对照组数值比实验组还高，最可能的原因是？',     error_count: 39,  power: '建构力', power_key: 'CONSTRUCT' },
      ],
    }),
  },
]

export default mockRoutes

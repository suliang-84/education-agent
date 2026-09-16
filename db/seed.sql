-- ============================================================
-- MESH AI 助教平台 · 初始化种子数据
-- 文件: seed.sql
-- 执行前提: init_db.sql 已执行完毕
-- 可重复执行: 是（INSERT ... ON CONFLICT DO NOTHING）
-- ============================================================

\set ON_ERROR_STOP on
SET client_encoding = 'UTF8';

-- ============================================================
-- §1. 学科（subjects）
-- ============================================================

INSERT INTO subjects (code, name, sort_order) VALUES
    ('MATH',      '数学', 1),
    ('PHYSICS',   '物理', 2),
    ('CHEMISTRY', '化学', 3)
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- §2. 年级（grades）—— 每学科 6 个年级
-- ============================================================

INSERT INTO grades (subject_id, code, name, sort_order)
SELECT s.id, g.code, g.name, g.sort_order
FROM subjects s
CROSS JOIN (VALUES
    ('G7',  '七年级（初一）', 1),
    ('G8',  '八年级（初二）', 2),
    ('G9',  '九年级（初三）', 3),
    ('G10', '高一',           4),
    ('G11', '高二',           5),
    ('G12', '高三',           6)
) AS g(code, name, sort_order)
ON CONFLICT (subject_id, code) DO NOTHING;

-- ============================================================
-- §3. 学期（semesters）—— 每年级 2 个学期
-- ============================================================

INSERT INTO semesters (grade_id, code, name, sort_order)
SELECT g.id, s.code, s.name, s.sort_order
FROM grades g
CROSS JOIN (VALUES
    ('S1', '上学期', 1),
    ('S2', '下学期', 2)
) AS s(code, name, sort_order)
ON CONFLICT (grade_id, code) DO NOTHING;

-- ============================================================
-- §4. 启发策略库（ai_heuristic_strategies）
-- ============================================================

INSERT INTO ai_heuristic_strategies
    (strategy_id, strategy_name, description, applicable_powers, default_priority, example_phrase)
VALUES
(
    'S-SOCRATIC', '苏格拉底提问',
    '通过连续小问题引导学生自主推导，不给结论',
    '["INSIGHT","CONSTRUCT","DEDUCE","ADAPT","MIGRATE"]', 1,
    '首先，题目告诉我们什么？然后，我们要找的是什么？'
),
(
    'S-SIMPLIFY', '化简特例',
    '在复杂问题上先验证最简单的特殊情形，找到规律',
    '["ADAPT"]', 2,
    '如果数字换成1和2，这道题你会做吗？先试试？'
),
(
    'S-ANALOGY-LIFE', '生活场景类比',
    '将抽象数学/物理概念与日常生活场景类比，降低陌生感',
    '["INSIGHT","CONSTRUCT"]', 3,
    '你有没有注意到，这个和骑自行车上坡的感觉很像？'
),
(
    'S-SPATIAL', '空间想象',
    '引导学生在脑中建立几何或函数的空间直觉',
    '["INSIGHT","DEDUCE"]', 4,
    '你能在脑子里画出这个函数的大概形状吗？'
),
(
    'S-VISUAL', '图示引导',
    '建议学生自己画图或提供图示辅助，将抽象转为具象',
    '["INSIGHT","CONSTRUCT"]', 5,
    '你试着把这道题画出来，把已知量标在图上？'
),
(
    'S-STORY', '故事叙述',
    '将数学问题嵌入故事情境，激发叙事思维',
    '["CONSTRUCT","MIGRATE"]', 6,
    '假设你是一个侦探，题目给的每个条件都是一条线索……'
),
(
    'S-COUNTER', '反例证伪',
    '引导学生思考"如果不这样，会怎样"，通过反例加深理解',
    '["DEDUCE","ADAPT"]', 7,
    '如果把这个条件去掉，结论还成立吗？举个反例试试？'
),
(
    'S-PATTERN', '节奏/模式感',
    '引导学生发现数学结构的规律性和节奏性',
    '["CONSTRUCT","DEDUCE"]', 8,
    '你看这个数列，有没有感受到一种节奏？每步变化量是……'
),
(
    'S-ANALOGY-KNOWN', '已知知识类比',
    '将新知识与学生已掌握的知识点类比，建立迁移桥梁',
    '["MIGRATE"]', 9,
    '这道题和上次我们讨论的等比数列有什么相似之处？'
)
ON CONFLICT (strategy_id) DO NOTHING;

-- ============================================================
-- §5. 系统配置（system_configs）
-- ============================================================

INSERT INTO system_configs (key, value, value_type, description) VALUES
-- 五力评分算法参数
('objective_weight',           '0.70',  'number', 'ability_score 在 final 中的权重'),
('preference_weight',          '0.30',  'number', 'preference_score 在 final 中的权重'),
('focus_threshold',            '50',    'number', '重点强化项阈值：ability < 50 = 困难🔴'),
('secondary_threshold',        '65',    'number', '次重点项阈值：50~65 = 需改进🟡'),
('time_bonus_coefficient',     '0.10',  'number', '时长加分系数，最高加10%'),
('history_decay',              '0.30',  'number', '重测历史衰减系数（新结果权重=70%）'),
('training_profile_decay',     '0.30',  'number', 'EWMA训练画像新数据权重'),
-- 综合能力融合比例
('test_train_mix_train',       '0.60',  'number', '综合查询时训练画像权重'),
('test_train_mix_test',        '0.40',  'number', '综合查询时测试画像权重'),
-- RAG 参数
('rag_timeout_sec',            '8',     'number', 'RAG 生成超时秒数'),
('rag_topk_questions',         '3',     'number', 'RAG 路径1召回题目数量'),
('rag_topk_strategies',        '2',     'number', 'RAG 路径2召回策略文档数量'),
('rag_similarity_threshold',   '0.75',  'number', 'RAG 相关性过滤阈值'),
-- AI 对话参数
('strategy_switch_threshold',  '2',     'number', '同一策略连续无效次数后切换'),
('proactive_max_count',        '3',     'number', 'AI 单会话最大主动介入次数'),
('chat_max_rounds',            '30',    'number', '单会话最大对话轮数'),
('session_max_token_budget',   '15000', 'number', '单次训练会话最大 Token 消耗'),
('chat_silence_timeout_min',   '10',    'number', '沉默模式自动解除时间（分钟）'),
-- LLM / Embedding 配置
('active_llm_provider',        'tongyi',     'string', '当前 LLM 供应商，支持热切换'),
('active_embedding_provider',  'dashscope',  'string', '当前 Embedding 供应商'),
('embedding_model',            'text-embedding-v2', 'string', 'Embedding 模型名'),
('embedding_dimensions',       '1536',  'number', 'Embedding 向量维度'),
-- 业务限制
('invite_code_expire_hours',   '48',    'number', '邀请码有效期（小时）'),
('sms_expire_minutes',         '5',     'number', '短信验证码有效期（分钟）'),
('sms_daily_limit',            '10',    'number', '同一手机号每日最多发送短信次数'),
('sms_cooldown_seconds',       '60',    'number', '同一手机号短信发送冷却时间（秒）'),
('admin_password_expire_days', '90',    'number', '管理员密码过期天数'),
('admin_lock_duration_minutes','30',    'number', '管理员账号锁定时长（分钟）'),
-- 未成年人保护
('minor_push_curfew_start',    '22',    'number', '未成年人推送禁止开始小时（22:00）'),
('minor_push_curfew_end',      '7',     'number', '未成年人推送禁止结束小时（07:00）')
ON CONFLICT (key) DO NOTHING;

-- ============================================================
-- §6. 全局训练配置版本（training_config_versions）—— 默认激活 v1
-- ============================================================

INSERT INTO training_config_versions (
    version_number, training_total_questions, difficulty_ratio,
    dedup_window_size, is_correct_threshold,
    rag_trigger_mode, rag_topk_questions, rag_topk_strategies,
    rag_similarity_threshold, rag_timeout_seconds,
    profile_decay_coefficient, is_active, description
) VALUES (
    'v1', 5,
    '{"basic":50,"advanced":35,"challenge":15}',
    30, 0.70,
    'all', 3, 2, 0.75, 8,
    0.30, TRUE,
    '默认初始配置（v1.0）'
)
ON CONFLICT (version_number) DO NOTHING;

-- ============================================================
-- §7. 五维度训练参数配置（training_dimension_configs）—— 每维度默认激活 v1
-- ============================================================

INSERT INTO training_dimension_configs (
    dimension, version_number,
    questions_per_session, dedup_window_size, difficulty_ratio,
    is_active, description
) VALUES
(
    'KNOWLEDGE_POINT', 'v1', 5, 30,
    '{"basic":50,"advanced":35,"challenge":15}',
    TRUE, '按知识点训练默认配置'
),
(
    'UNIT', 'v1', 8, 50,
    '{"basic":40,"advanced":40,"challenge":20}',
    TRUE, '按单元训练默认配置'
),
(
    'SEMESTER', 'v1', 10, 100,
    '{"basic":30,"advanced":40,"challenge":30}',
    TRUE, '按学期训练默认配置'
),
(
    'ERROR_QUESTIONS', 'v1', 5, 10,
    NULL,
    TRUE, '错题集训练默认配置（难度按原题，不强制分布）'
),
(
    'RANDOM', 'v1', 5, 20,
    '{"basic":50,"advanced":35,"challenge":15}',
    TRUE, '随机训练默认配置'
)
ON CONFLICT (dimension, version_number) DO NOTHING;

-- ============================================================
-- 完成
-- ============================================================
DO $$ BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'seed.sql 执行完毕';
    RAISE NOTICE '  学科: 3  年级: 18  学期: 36';
    RAISE NOTICE '  启发策略: 9  系统配置: 29';
    RAISE NOTICE '  训练配置版本: 1  维度配置: 5';
    RAISE NOTICE '========================================';
END $$;

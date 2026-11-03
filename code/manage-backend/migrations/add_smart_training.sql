-- 智能训练（SMART 维度）：学习信号缓存 + 维度配置的算法参数

-- 1. 学生学习信号缓存：AI 助手聊天里提取出的「近期困惑知识点」与聊天摘要（不存聊天原文）
CREATE TABLE IF NOT EXISTS student_learning_signals (
    id                BIGSERIAL    PRIMARY KEY,
    student_id        BIGINT       NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    intents           JSONB        NOT NULL DEFAULT '[]',   -- [{"kp_id":163,"confidence":0.8,"mentioned_at":"2026-11-03T10:00:00+00:00"}]
    chat_summary      TEXT,                                 -- 近期与 AI 助手交流的学习情况摘要（≤100 字）
    source_message_id BIGINT       NOT NULL DEFAULT 0,      -- 已分析到的最新学生消息 id，有新消息才重新分析
    refreshed_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 2. 训练维度配置：智能训练的权重 / 槽位配比等参数
ALTER TABLE training_dimension_configs ADD COLUMN IF NOT EXISTS smart_params JSONB;
COMMENT ON COLUMN training_dimension_configs.smart_params IS '智能训练算法参数（权重、槽位比例、半衰期等）；NULL 用代码默认值';
-- 触发器 trg_training_dimension_configs_updated_at 要写 updated_at，但表里没有这个字段，任何 UPDATE 都会报错
ALTER TABLE training_dimension_configs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- 3. 新增训练维度 SMART
ALTER TABLE training_sessions DROP CONSTRAINT IF EXISTS training_sessions_training_dimension_check;
ALTER TABLE training_sessions ADD CONSTRAINT training_sessions_training_dimension_check
    CHECK (training_dimension IN ('KNOWLEDGE_POINT','UNIT','SEMESTER','ERROR_QUESTIONS','RANDOM','FAVORITES','SMART'));
ALTER TABLE training_dimension_configs DROP CONSTRAINT IF EXISTS training_dimension_configs_dimension_check;
ALTER TABLE training_dimension_configs ADD CONSTRAINT training_dimension_configs_dimension_check
    CHECK (dimension IN ('KNOWLEDGE_POINT','UNIT','SEMESTER','ERROR_QUESTIONS','RANDOM','FAVORITES','SMART'));

INSERT INTO training_dimension_configs (dimension, version_number, questions_per_session, dedup_window_size, difficulty_ratio, is_active, description)
SELECT 'SMART', 'v1', 5, 30, NULL, TRUE, '智能训练默认配置（算法参数见 smart_params，NULL 时用代码默认值）'
WHERE NOT EXISTS (SELECT 1 FROM training_dimension_configs WHERE dimension = 'SMART' AND version_number = 'v1');

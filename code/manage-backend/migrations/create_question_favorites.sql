-- 题目收藏（答题页右上角五角星）+ 收藏夹训练维度 FAVORITES
CREATE TABLE IF NOT EXISTS question_favorites (
    id          BIGSERIAL    PRIMARY KEY,
    student_id  BIGINT       NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    question_id BIGINT       NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_question_favorites_student_question UNIQUE (student_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_question_favorites_student ON question_favorites(student_id, created_at DESC);

-- 训练维度新增 FAVORITES（会话表、维度配置表的 CHECK 约束）
ALTER TABLE training_sessions DROP CONSTRAINT IF EXISTS training_sessions_training_dimension_check;
ALTER TABLE training_sessions ADD CONSTRAINT training_sessions_training_dimension_check
    CHECK (training_dimension IN ('KNOWLEDGE_POINT','UNIT','SEMESTER','ERROR_QUESTIONS','RANDOM','FAVORITES'));
ALTER TABLE training_dimension_configs DROP CONSTRAINT IF EXISTS training_dimension_configs_dimension_check;
ALTER TABLE training_dimension_configs ADD CONSTRAINT training_dimension_configs_dimension_check
    CHECK (dimension IN ('KNOWLEDGE_POINT','UNIT','SEMESTER','ERROR_QUESTIONS','RANDOM','FAVORITES'));

-- 收藏夹维度的默认配置：每次 5 题，题型平均，难度比例同随机
INSERT INTO training_dimension_configs (dimension, version_number, questions_per_session, dedup_window_size, difficulty_ratio, is_active, description)
SELECT 'FAVORITES', 'v1', 5, 30, '{"basic":50,"advanced":35,"challenge":15}'::jsonb, TRUE, '收藏夹训练默认配置'
WHERE NOT EXISTS (SELECT 1 FROM training_dimension_configs WHERE dimension = 'FAVORITES' AND version_number = 'v1');

-- 训练中断记录表（v2.3.0）
CREATE TABLE IF NOT EXISTS training_interrupts (
    id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id              BIGINT          NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_code            VARCHAR(20)     NOT NULL,
    training_dimension      VARCHAR(30)     NOT NULL,
    scope_label             VARCHAR(200)    NOT NULL DEFAULT '',
    scope_info              JSONB           NOT NULL DEFAULT '{}',
    questions_snapshot      JSONB           NOT NULL DEFAULT '[]',
    answers_snapshot        JSONB           NOT NULL DEFAULT '[]',
    current_question_index  SMALLINT        NOT NULL DEFAULT 0,
    total_questions         SMALLINT        NOT NULL DEFAULT 0,
    session_id              UUID            REFERENCES training_sessions(id) ON DELETE SET NULL,
    interrupted_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, subject_code, training_dimension)
);

CREATE INDEX IF NOT EXISTS idx_training_interrupts_student
    ON training_interrupts(student_id, subject_code, training_dimension);

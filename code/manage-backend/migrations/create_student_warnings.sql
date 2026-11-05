-- 学生画像预警记录（二期）
-- status：open = 未处理，handled = 管理员已处理，closed = 条件不再成立后自动关闭
-- level：notice = 提醒，attention = 关注，critical = 重点
CREATE TABLE IF NOT EXISTS student_warnings (
    id           BIGSERIAL PRIMARY KEY,
    student_id   BIGINT       NOT NULL REFERENCES students(id),
    rule_code    VARCHAR(40)  NOT NULL,
    level        VARCHAR(10)  NOT NULL CHECK (level IN ('notice', 'attention', 'critical')),
    status       VARCHAR(10)  NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'handled', 'closed')),
    message      TEXT         NOT NULL,
    detail       JSONB,
    triggered_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    handled_by   BIGINT,
    handled_at   TIMESTAMPTZ,
    note         TEXT,
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 同一学生同一规则，未处理的预警最多一条
CREATE UNIQUE INDEX IF NOT EXISTS uq_student_warnings_open
    ON student_warnings(student_id, rule_code) WHERE status = 'open';
CREATE INDEX IF NOT EXISTS idx_student_warnings_student
    ON student_warnings(student_id, status, triggered_at DESC);

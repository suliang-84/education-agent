-- ============================================================
-- MESH AI 助教平台 · 数据库初始化脚本
-- 文件: init_db.sql
-- 版本: v1.3.0-r1（含架构师决策 Q1-Q12）
-- 数据库: mesh_edu  |  执行用户: suliang (superuser)
-- 可重复执行: 是（IF NOT EXISTS + DO $$ 幂等块）
-- ============================================================

\set ON_ERROR_STOP on
SET client_encoding = 'UTF8';
SET timezone = 'UTC';

-- ============================================================
-- §0. 扩展
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- gen_random_uuid() 在 PG16 已内置，pgcrypto 确保兼容性

-- ============================================================
-- §1. 枚举类型（DO 块保证幂等）
-- ============================================================

-- 五力维度（Q4: 以前端代码为准统一枚举值）
DO $$ BEGIN
    CREATE TYPE force_type AS ENUM (
        'INSIGHT',    -- 洞察力
        'CONSTRUCT',  -- 建构力（原 STRUCTURE）
        'DEDUCE',     -- 推演力（原 INFERENCE）
        'ADAPT',      -- 调适力（原 ADAPTATION）
        'MIGRATE'     -- 迁移力（原 TRANSFER）
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 五力等级
DO $$ BEGIN
    CREATE TYPE force_level AS ENUM (
        'weak',    -- 🔴 困难（ability < 50）
        'medium',  -- 🟡 需改进（50 ≤ ability < 65）
        'good',    -- 🟢 良好（65 ≤ ability < 80）
        'strong'   -- 💚 优势（ability ≥ 80）
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 学习模式
DO $$ BEGIN
    CREATE TYPE training_mode AS ENUM (
        'TRAIN_WEAKNESS',    -- 补足模式：有薄弱力需要强化
        'LEARN_BY_STRENGTH'  -- 一通百通：从优势入口学新知识
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 错题复盘状态
DO $$ BEGIN
    CREATE TYPE wrong_review_status AS ENUM (
        'unreview',             -- 未复盘（默认）
        'reviewing',            -- 复盘进行中
        'aha_achieved',         -- 理解突破（终态）
        'pending_consolidation' -- 复盘完成但未突破，待巩固
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- AI 对话模式
DO $$ BEGIN
    CREATE TYPE chat_session_mode AS ENUM (
        'free_chat',                -- 自由提问
        'wrong_review',             -- 错题复盘
        'training_error_guidance'   -- 训练连续答错触发的引导
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 策略事件类型
DO $$ BEGIN
    CREATE TYPE strategy_event_type AS ENUM (
        'strategy_start',   -- 策略开始使用
        'strategy_switch',  -- 策略切换（因无效）
        'aha_moment',       -- 理解突破
        'silence_mode',     -- 进入沉默模式
        'proactive_trigger' -- AI 主动介入
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 题目难度
DO $$ BEGIN
    CREATE TYPE question_difficulty AS ENUM (
        'basic',     -- 基础
        'advanced',  -- 进阶
        'challenge'  -- 挑战
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================
-- §2. 工具函数
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at() IS '通用触发器函数：BEFORE UPDATE 时自动更新 updated_at 为当前时间';

-- ============================================================
-- §3. 独立序列
-- ============================================================

-- 五力测试题目序号（独立于 id 主键，Q5：NOT NULL 但不强制 UNIQUE）
CREATE SEQUENCE IF NOT EXISTS cog_question_no_seq
    START 1 INCREMENT 1 NO CYCLE;

-- ============================================================
-- §4. 建表（严格按外键依赖顺序，共 34 张表）
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 第 1 批：无外键依赖
-- ────────────────────────────────────────────────────────────

-- ① subjects（学科表）
CREATE TABLE IF NOT EXISTS subjects (
    id          SERIAL       PRIMARY KEY,
    code        VARCHAR(20)  NOT NULL UNIQUE,
    name        VARCHAR(50)  NOT NULL,
    sort_order  SMALLINT     NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  subjects        IS '学科表：数学/物理/化学';
COMMENT ON COLUMN subjects.code   IS '学科代码：MATH / PHYSICS / CHEMISTRY';

-- ② admin_users（管理员账户表）
CREATE TABLE IF NOT EXISTS admin_users (
    id                  BIGSERIAL    PRIMARY KEY,
    username            VARCHAR(50)  NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    display_name        VARCHAR(50)  NOT NULL,
    email               VARCHAR(100) DEFAULT NULL,          -- Q7: 允许 NULL（创建时可选）
    phone               VARCHAR(64)  NOT NULL,
    role                VARCHAR(20)  NOT NULL DEFAULT 'SUPER_ADMIN',
    is_active           SMALLINT     NOT NULL DEFAULT 2     -- 0=禁用 1=启用 2=待首次登录
                        CHECK (is_active IN (0, 1, 2)),
    login_fail_count    SMALLINT     NOT NULL DEFAULT 0,
    locked_until        TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ,
    last_login_at       TIMESTAMPTZ,
    last_login_ip       VARCHAR(50),
    created_by          BIGINT       REFERENCES admin_users(id) ON DELETE RESTRICT,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_admin_users_username ON admin_users(username);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_admin_users_email   ON admin_users(email) WHERE email IS NOT NULL;
COMMENT ON TABLE  admin_users                  IS '管理员账户表';
COMMENT ON COLUMN admin_users.password_hash    IS 'bcrypt 哈希，cost=12';
COMMENT ON COLUMN admin_users.phone            IS '加密存储，用于 2FA 短信验证';
COMMENT ON COLUMN admin_users.email            IS '可选，Q7决策：允许NULL，用于通知/找回密码';
COMMENT ON COLUMN admin_users.is_active        IS '0=禁用 1=启用 2=待首次登录（必须先改密码）';
COMMENT ON COLUMN admin_users.login_fail_count IS '连续登录失败次数，达5次触发锁定30分钟';

-- ③ system_configs（系统配置热更新表）
CREATE TABLE IF NOT EXISTS system_configs (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT         NOT NULL,
    value_type  VARCHAR(20)  NOT NULL DEFAULT 'string'
                CHECK (value_type IN ('string', 'number', 'json', 'boolean')),
    description TEXT,
    updated_by  BIGINT       REFERENCES admin_users(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),    -- Q9: 补充 created_at
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  system_configs            IS '系统配置热更新表，无需重启服务即可生效';
COMMENT ON COLUMN system_configs.key        IS '配置键名，全局唯一，如 rag_timeout_sec';
COMMENT ON COLUMN system_configs.value_type IS '值类型：string/number/json/boolean';
COMMENT ON COLUMN system_configs.created_at IS 'Q9补充：配置项首次写入时间';

-- ④ ai_heuristic_strategies（启发策略库表）
CREATE TABLE IF NOT EXISTS ai_heuristic_strategies (
    strategy_id      VARCHAR(32)  PRIMARY KEY,
    strategy_name    VARCHAR(50)  NOT NULL,
    description      TEXT         NOT NULL,
    applicable_powers JSONB       NOT NULL,
    default_priority SMALLINT     NOT NULL,
    example_phrase   TEXT,
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  ai_heuristic_strategies                  IS '9种预置启发策略库，管理员可维护调整';
COMMENT ON COLUMN ai_heuristic_strategies.strategy_id      IS '策略标识：S-SOCRATIC / S-SIMPLIFY / S-ANALOGY-LIFE 等';
COMMENT ON COLUMN ai_heuristic_strategies.applicable_powers IS 'JSONB数组，适用五力，如 ["INSIGHT","CONSTRUCT"]（Q4: 使用新枚举值）';
COMMENT ON COLUMN ai_heuristic_strategies.default_priority  IS '默认优先级：1(最高)~9(最低)';
COMMENT ON COLUMN ai_heuristic_strategies.description       IS '注入AI上下文的策略描述，≤50字';

-- ────────────────────────────────────────────────────────────
-- 第 2 批：依赖第 1 批
-- ────────────────────────────────────────────────────────────

-- ⑤ students（用户账户表：学生+家长统一存储）
CREATE TABLE IF NOT EXISTS students (
    id            BIGSERIAL    PRIMARY KEY,
    openid        VARCHAR(64)  NOT NULL,
    openid_hash   VARCHAR(64)  NOT NULL,
    phone         VARCHAR(64),
    phone_hash    VARCHAR(64),
    nickname      VARCHAR(50),
    avatar_url    VARCHAR(512),
    user_type     VARCHAR(10)  NOT NULL DEFAULT 'STUDENT'
                  CHECK (user_type IN ('STUDENT', 'PARENT')),
    grade         VARCHAR(10)
                  CHECK (grade IN ('G7','G8','G9','G10','G11','G12')),
    semester      VARCHAR(2)
                  CHECK (semester IN ('S1','S2')),
    subject_prefs JSONB        NOT NULL DEFAULT '[]',
    is_minor      BOOLEAN      NOT NULL DEFAULT TRUE,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    is_confirmed  BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at    TIMESTAMPTZ  DEFAULT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_students_openid_hash ON students(openid_hash);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_students_phone_hash  ON students(phone_hash) WHERE phone_hash IS NOT NULL;
CREATE        INDEX IF NOT EXISTS idx_students_created_at   ON students(created_at DESC);
CREATE        INDEX IF NOT EXISTS idx_students_user_type    ON students(user_type, is_active);
COMMENT ON TABLE  students                IS '用户账户表（v1.2.0：统一存储学生与家长两类角色）';
COMMENT ON COLUMN students.openid         IS '微信 openid（AES 可逆加密后存储）';
COMMENT ON COLUMN students.openid_hash    IS 'SHA256 哈希，用于唯一性查询';
COMMENT ON COLUMN students.phone          IS '手机号（AES 加密存储）';
COMMENT ON COLUMN students.phone_hash     IS 'SHA256 哈希，用于唯一性查询';
COMMENT ON COLUMN students.user_type      IS 'STUDENT=学习用户；PARENT=家长（通过绑定关系查看子女数据）';
COMMENT ON COLUMN students.subject_prefs  IS 'JSONB 数组，学科偏好如 ["MATH","PHYSICS"]，家长为 []';
COMMENT ON COLUMN students.is_confirmed   IS '管理员创建的家长账号初始为 FALSE，首次登录后自动置 TRUE';
COMMENT ON COLUMN students.deleted_at     IS '软删除：30天后物理删除 AI 对话记录';

-- ⑥ grades（年级表）
CREATE TABLE IF NOT EXISTS grades (
    id         SERIAL      PRIMARY KEY,
    subject_id INT         NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    code       VARCHAR(10) NOT NULL,
    name       VARCHAR(20) NOT NULL,
    sort_order SMALLINT    NOT NULL DEFAULT 0,
    is_active  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(subject_id, code)
);
COMMENT ON TABLE  grades      IS '年级表，挂载在学科下';
COMMENT ON COLUMN grades.code IS 'G7/G8/G9/G10/G11/G12';

-- ⑦ training_config_versions（全局算法配置版本表）
CREATE TABLE IF NOT EXISTS training_config_versions (
    id                       BIGSERIAL    PRIMARY KEY,
    version_number           VARCHAR(20)  NOT NULL UNIQUE,
    training_total_questions SMALLINT     NOT NULL DEFAULT 5,
    difficulty_ratio         JSONB        NOT NULL DEFAULT '{"basic":50,"advanced":35,"challenge":15}',
    dedup_window_size        SMALLINT     NOT NULL DEFAULT 30,
    is_correct_threshold     DECIMAL(3,2) NOT NULL DEFAULT 0.70,
    rag_trigger_mode         VARCHAR(20)  NOT NULL DEFAULT 'all'
                             CHECK (rag_trigger_mode IN ('all','wrong_only','disabled')),
    rag_topk_questions       SMALLINT     NOT NULL DEFAULT 3,
    rag_topk_strategies      SMALLINT     NOT NULL DEFAULT 2,
    rag_similarity_threshold DECIMAL(3,2) NOT NULL DEFAULT 0.75,
    rag_timeout_seconds      SMALLINT     NOT NULL DEFAULT 8,
    profile_decay_coefficient DECIMAL(3,2) NOT NULL DEFAULT 0.30,
    is_active                BOOLEAN      NOT NULL DEFAULT FALSE,
    description              TEXT,
    created_by               BIGINT       REFERENCES admin_users(id) ON DELETE RESTRICT,
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_config_versions_active ON training_config_versions(is_active);
COMMENT ON TABLE  training_config_versions                       IS '全局算法配置版本表（v2.1: 五维度参数已迁至 training_dimension_configs）';
COMMENT ON COLUMN training_config_versions.is_active             IS '同一时刻仅一条为 TRUE';
COMMENT ON COLUMN training_config_versions.is_correct_threshold  IS '文字题答对阈值，默认 0.70';
COMMENT ON COLUMN training_config_versions.profile_decay_coefficient IS 'EWMA衰减系数，新数据权重';

-- ⑧ training_dimension_configs（五维度训练参数配置表）
CREATE TABLE IF NOT EXISTS training_dimension_configs (
    id                     BIGSERIAL    PRIMARY KEY,
    dimension              VARCHAR(20)  NOT NULL
                           CHECK (dimension IN ('KNOWLEDGE_POINT','UNIT','SEMESTER','ERROR_QUESTIONS','RANDOM')),
    version_number         VARCHAR(20)  NOT NULL,
    questions_per_session  SMALLINT     NOT NULL DEFAULT 5,
    dedup_window_size      SMALLINT     NOT NULL DEFAULT 30,
    difficulty_ratio       JSONB,
    wrong_priority         VARCHAR(20)  DEFAULT 'most_failed'
                           CHECK (wrong_priority IN ('most_failed','most_recent','oldest_first')),
    new_question_mix_ratio DECIMAL(3,2) DEFAULT 0.20,
    remove_after_correct   SMALLINT     DEFAULT 3,
    is_active              BOOLEAN      NOT NULL DEFAULT FALSE,
    description            TEXT,
    created_by             BIGINT       REFERENCES admin_users(id) ON DELETE RESTRICT,
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(dimension, version_number)
);
CREATE INDEX IF NOT EXISTS idx_dim_configs_active ON training_dimension_configs(dimension, is_active);
COMMENT ON TABLE  training_dimension_configs                      IS '五维度训练参数配置表（v2.0新增），每维度独立版本化管理';
COMMENT ON COLUMN training_dimension_configs.dimension            IS '训练维度：KNOWLEDGE_POINT/UNIT/SEMESTER/ERROR_QUESTIONS/RANDOM';
COMMENT ON COLUMN training_dimension_configs.wrong_priority       IS '错题集排序：most_failed/most_recent/oldest_first（仅 ERROR_QUESTIONS）';
COMMENT ON COLUMN training_dimension_configs.new_question_mix_ratio IS '新旧题混入比例（仅 ERROR_QUESTIONS）：0=纯错题，0.2=80%旧+20%新';
COMMENT ON COLUMN training_dimension_configs.remove_after_correct IS '连续答对 N 次后移出错题列表（仅 ERROR_QUESTIONS）';

-- ⑨ cognitive_test_questions（五力认知测试题目表）
CREATE TABLE IF NOT EXISTS cognitive_test_questions (
    id               SERIAL      PRIMARY KEY,
    question_no      INTEGER     NOT NULL DEFAULT nextval('cog_question_no_seq'), -- Q5: NOT NULL，独立序列
    display_order    SMALLINT    NOT NULL,
    description      TEXT,
    stem             TEXT        NOT NULL,
    image_url        VARCHAR(512),
    answers          JSONB       NOT NULL,
    -- answers 格式: [{"key":"A","text":"...","force_weights":{"INSIGHT":0.7,"CONSTRUCT":0.1,"DEDUCE":0.1,"ADAPT":0.05,"MIGRATE":0.05}}]
    -- 每条答案的 force_weights 五力之和需满足 0.99 ≤ sum ≤ 1.01
    reference_time_sec SMALLINT  NOT NULL DEFAULT 90,
    status           VARCHAR(20) NOT NULL DEFAULT 'draft'
                     CHECK (status IN ('draft','published','archived')),
    created_by       INT         REFERENCES admin_users(id) ON DELETE RESTRICT,
    updated_by       INT         REFERENCES admin_users(id) ON DELETE RESTRICT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cogq_status_order ON cognitive_test_questions(status, display_order)
    WHERE status = 'published';
COMMENT ON TABLE  cognitive_test_questions                IS '五力认知测试题目表，测试激活条件：published 状态恰好 = 20 条';
COMMENT ON COLUMN cognitive_test_questions.question_no    IS '题目序号（Q5：NOT NULL，不强制 UNIQUE，由独立序列 cog_question_no_seq 分配，创建后不变）';
COMMENT ON COLUMN cognitive_test_questions.answers        IS 'JSONB 数组，含 key/text/force_weights（Q4: 五力 key 统一为 INSIGHT/CONSTRUCT/DEDUCE/ADAPT/MIGRATE）';
COMMENT ON COLUMN cognitive_test_questions.display_order  IS '前台展示顺序，已发布题目按此排序组卷';
COMMENT ON COLUMN cognitive_test_questions.description    IS '管理员内部元数据，不展示给学生';

-- ────────────────────────────────────────────────────────────
-- 第 3 批：依赖第 2 批
-- ────────────────────────────────────────────────────────────

-- ⑩ sms_codes（短信验证码表）
CREATE TABLE IF NOT EXISTS sms_codes (
    id         BIGSERIAL   PRIMARY KEY,
    phone_hash VARCHAR(64) NOT NULL,
    code       VARCHAR(6)  NOT NULL,
    purpose    VARCHAR(20) NOT NULL
               CHECK (purpose IN ('REGISTER','LOGIN','TWO_FA','BIND_PHONE')),
    expires_at TIMESTAMPTZ NOT NULL,
    is_used    BOOLEAN     NOT NULL DEFAULT FALSE,
    fail_count SMALLINT    NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sms_codes_phone_hash ON sms_codes(phone_hash, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sms_codes_expires_at ON sms_codes(expires_at);
COMMENT ON TABLE  sms_codes            IS '短信验证码表，有效期5分钟，校验失败>5次即作废';
COMMENT ON COLUMN sms_codes.phone_hash IS '手机号 SHA256 哈希';
COMMENT ON COLUMN sms_codes.purpose    IS 'REGISTER/LOGIN/TWO_FA/BIND_PHONE';
COMMENT ON COLUMN sms_codes.fail_count IS '校验失败次数，超5次此码作废需重新发送';

-- ⑪ invite_codes（家长邀请码表）
CREATE TABLE IF NOT EXISTS invite_codes (
    id         BIGSERIAL   PRIMARY KEY,
    student_id BIGINT      NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    code       VARCHAR(8)  NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_used    BOOLEAN     NOT NULL DEFAULT FALSE,
    used_by_id BIGINT      REFERENCES students(id) ON DELETE RESTRICT,
    used_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE        INDEX IF NOT EXISTS idx_invite_codes_student  ON invite_codes(student_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_invite_codes_code    ON invite_codes(code) WHERE NOT is_used;
COMMENT ON TABLE  invite_codes            IS '家长邀请码表，有效期48小时，一次性使用';
COMMENT ON COLUMN invite_codes.code       IS '8位字母数字混合码';
COMMENT ON COLUMN invite_codes.used_by_id IS '使用邀请码绑定的家长账号 student_id';

-- ⑫ parent_student_bindings（家长-学生绑定表）
CREATE TABLE IF NOT EXISTS parent_student_bindings (
    id                  BIGSERIAL   PRIMARY KEY,
    student_id          BIGINT      NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    parent_id           BIGINT      NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    bind_method         VARCHAR(20) NOT NULL
                        CHECK (bind_method IN ('INVITE_CODE','PARENT_SELF','ADMIN')),
    bind_status         VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (bind_status IN ('pending','active','rejected')),
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    created_by_admin_id BIGINT      REFERENCES admin_users(id) ON DELETE RESTRICT,
    confirmed_at        TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- Q8: 新增，追踪 bind_status 变更
    deleted_at          TIMESTAMPTZ DEFAULT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_parent_student       ON parent_student_bindings(student_id, parent_id) WHERE deleted_at IS NULL;
CREATE        INDEX IF NOT EXISTS idx_parent_bindings_student ON parent_student_bindings(student_id) WHERE deleted_at IS NULL;
CREATE        INDEX IF NOT EXISTS idx_parent_bindings_parent  ON parent_student_bindings(parent_id)  WHERE deleted_at IS NULL;
COMMENT ON TABLE  parent_student_bindings             IS '家长-学生绑定表，软删除；每生≤2个家长，每家长≤5个学生（应用层控制）';
COMMENT ON COLUMN parent_student_bindings.bind_method IS 'INVITE_CODE=邀请码；PARENT_SELF=家长主动发起（需学生确认）；ADMIN=管理员后台操作';
COMMENT ON COLUMN parent_student_bindings.bind_status IS 'pending=待确认（PARENT_SELF）；active=生效；rejected=学生拒绝';
COMMENT ON COLUMN parent_student_bindings.expires_at  IS 'PARENT_SELF 方式 pending 状态有效期 24h';
COMMENT ON COLUMN parent_student_bindings.updated_at  IS 'Q8补充：bind_status 流转时自动更新';

-- ⑬ semesters（学期表，Q1: 补充至表清单，总数 34 张）
CREATE TABLE IF NOT EXISTS semesters (
    id         SERIAL      PRIMARY KEY,
    grade_id   INT         NOT NULL REFERENCES grades(id) ON DELETE RESTRICT,
    code       VARCHAR(2)  NOT NULL CHECK (code IN ('S1','S2')),
    name       VARCHAR(20) NOT NULL,
    sort_order SMALLINT    NOT NULL DEFAULT 0,
    is_active  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(grade_id, code)
);
CREATE INDEX IF NOT EXISTS idx_semesters_grade ON semesters(grade_id, sort_order);
COMMENT ON TABLE  semesters      IS '学期表（v1.4.0新增，Q1: 补充至表清单），每年级有 S1/S2 两条';
COMMENT ON COLUMN semesters.code IS 'S1=上学期，S2=下学期';

-- ⑭ five_power_training_profiles（五力训练画像表）
CREATE TABLE IF NOT EXISTS five_power_training_profiles (
    id                   BIGSERIAL   PRIMARY KEY,
    student_id           BIGINT      NOT NULL REFERENCES students(id) ON DELETE RESTRICT UNIQUE,
    -- Q4: 字段名统一为前端枚举值（CONSTRUCT/DEDUCE/ADAPT/MIGRATE 替换原 STRUCTURE/INFERENCE/ADAPTATION/TRANSFER）
    insight_ability      SMALLINT    NOT NULL DEFAULT 50,
    construct_ability    SMALLINT    NOT NULL DEFAULT 50,  -- 原 structure_ability
    deduce_ability       SMALLINT    NOT NULL DEFAULT 50,  -- 原 inference_ability
    adapt_ability        SMALLINT    NOT NULL DEFAULT 50,  -- 原 adaptation_ability
    migrate_ability      SMALLINT    NOT NULL DEFAULT 50,  -- 原 transfer_ability
    total_training_count INT         NOT NULL DEFAULT 0,
    total_question_count INT         NOT NULL DEFAULT 0,
    last_trained_at      TIMESTAMPTZ,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  five_power_training_profiles                  IS '五力训练画像表，每生唯一一条，EWMA 滚动更新（新数据权重=0.30）';
COMMENT ON COLUMN five_power_training_profiles.construct_ability IS 'Q4: 建构力训练分（原 structure_ability），初始 50';
COMMENT ON COLUMN five_power_training_profiles.deduce_ability    IS 'Q4: 推演力训练分（原 inference_ability），初始 50';
COMMENT ON COLUMN five_power_training_profiles.adapt_ability     IS 'Q4: 调适力训练分（原 adaptation_ability），初始 50';
COMMENT ON COLUMN five_power_training_profiles.migrate_ability   IS 'Q4: 迁移力训练分（原 transfer_ability），初始 50';

-- ⑮ student_ai_prompt_summaries（学生 AI 助教提示词摘要表）
CREATE TABLE IF NOT EXISTS student_ai_prompt_summaries (
    id                          BIGSERIAL   PRIMARY KEY,
    student_id                  BIGINT      NOT NULL REFERENCES students(id) ON DELETE RESTRICT UNIQUE,
    learning_summary            TEXT,
    learning_summary_updated_at TIMESTAMPTZ,
    learning_summary_version    INT         NOT NULL DEFAULT 0,
    personal_insight            TEXT,
    personal_insight_updated_at TIMESTAMPTZ,
    insight_updated_by          VARCHAR(20) CHECK (insight_updated_by IN ('AI','ADMIN')),
    is_enabled                  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_prompt_summaries_student ON student_ai_prompt_summaries(student_id);
COMMENT ON TABLE  student_ai_prompt_summaries                          IS '学生 AI 助教提示词摘要表（v2.1新增），每生一条，注入 System Prompt';
COMMENT ON COLUMN student_ai_prompt_summaries.learning_summary         IS '学习信息摘要（≤200字），系统训练/测试完成后异步刷新';
COMMENT ON COLUMN student_ai_prompt_summaries.learning_summary_version IS '版本号，每次自动刷新 +1';
COMMENT ON COLUMN student_ai_prompt_summaries.personal_insight         IS '个人洞察摘要，AI从对话提取或管理员手动编辑';
COMMENT ON COLUMN student_ai_prompt_summaries.is_enabled               IS '禁用时不注入 Prompt';

-- ────────────────────────────────────────────────────────────
-- 第 4 批：依赖第 3 批（semesters）
-- ────────────────────────────────────────────────────────────

-- ⑯ chapters（单元表）
CREATE TABLE IF NOT EXISTS chapters (
    id          BIGSERIAL    PRIMARY KEY,
    semester_id INT          NOT NULL REFERENCES semesters(id) ON DELETE RESTRICT,
    name        VARCHAR(100) NOT NULL,
    sort_order  SMALLINT     NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chapters_semester ON chapters(semester_id, sort_order);
COMMENT ON TABLE chapters IS '单元表（v1.4.0: grade_id 改为 semester_id），知识体系路径：科目→年级→学期→单元→知识点';

-- ────────────────────────────────────────────────────────────
-- 第 5 批：依赖第 4 批（chapters）
-- ────────────────────────────────────────────────────────────

-- ⑰ knowledge_points（知识点表）
CREATE TABLE IF NOT EXISTS knowledge_points (
    id          BIGSERIAL    PRIMARY KEY,
    chapter_id  BIGINT       NOT NULL REFERENCES chapters(id) ON DELETE RESTRICT,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  SMALLINT     NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_knowledge_points_code    ON knowledge_points(code);
CREATE        INDEX IF NOT EXISTS idx_knowledge_points_chapter  ON knowledge_points(chapter_id, sort_order);
CREATE        INDEX IF NOT EXISTS idx_knowledge_points_nav      ON knowledge_points(chapter_id, is_active, sort_order) WHERE is_active = TRUE;
COMMENT ON TABLE  knowledge_points      IS '知识点表，五级体系最底层节点';
COMMENT ON COLUMN knowledge_points.code IS '全局唯一编码，格式：MATH-G9-S1-CH03-KP007（含学期标识）';

-- ────────────────────────────────────────────────────────────
-- 第 6 批：依赖第 5 批 + 第 2 批
-- ────────────────────────────────────────────────────────────

-- ⑱ questions（训练题库）
CREATE TABLE IF NOT EXISTS questions (
    id                  BIGSERIAL   PRIMARY KEY,
    stem                TEXT        NOT NULL,
    image_url           VARCHAR(512),
    -- 五级归属体系（发布时由管理员审核确认写入，发布前可空）
    subject_id          INT         REFERENCES subjects(id)          ON DELETE RESTRICT,
    grade_id            INT         REFERENCES grades(id)            ON DELETE RESTRICT,
    semester_id         INT         REFERENCES semesters(id)         ON DELETE RESTRICT,
    chapter_id          BIGINT      REFERENCES chapters(id)          ON DELETE RESTRICT,
    knowledge_point_ids JSONB       NOT NULL DEFAULT '[]',           -- [1001, 1008]，GIN索引
    -- 题目类型与答案
    question_type       VARCHAR(20)
                        CHECK (question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','FILL_BLANK','TRUE_FALSE','APPLICATION')),
    answer              JSONB,
    difficulty          VARCHAR(20)
                        CHECK (difficulty IN ('basic','advanced','challenge')),
    solution            TEXT,
    common_error        TEXT,
    power_solutions     JSONB,
    -- 五力权重（Q4: key 统一为 INSIGHT/CONSTRUCT/DEDUCE/ADAPT/MIGRATE，总分=10）
    five_power_weights  JSONB,
    primary_power       VARCHAR(20)
                        CHECK (primary_power IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    transfer_direction  JSONB       NOT NULL DEFAULT '[]',
    -- 生命周期
    status              VARCHAR(20) NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft','analyzing','pending_review','published','archived')),
    analysis_round      SMALLINT    NOT NULL DEFAULT 0,
    rejection_reason    TEXT,
    embedding_status    VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (embedding_status IN ('pending','completed','failed')),
    embedded_at         TIMESTAMPTZ,
    is_seed_data        BOOLEAN     NOT NULL DEFAULT FALSE,
    created_by          BIGINT      REFERENCES admin_users(id) ON DELETE RESTRICT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS idx_questions_power_status ON questions(primary_power, status, difficulty)
    WHERE deleted_at IS NULL AND status = 'published';
CREATE INDEX IF NOT EXISTS idx_questions_subject      ON questions(subject_id,  status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_questions_grade        ON questions(grade_id,    status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_questions_semester     ON questions(semester_id, status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_questions_chapter      ON questions(chapter_id,  status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_questions_status       ON questions(status, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_questions_kp_ids       ON questions USING GIN(knowledge_point_ids);
CREATE INDEX IF NOT EXISTS idx_questions_selection    ON questions(primary_power, difficulty, status)
    WHERE status = 'published' AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_questions_embedding    ON questions(embedding_status) WHERE embedding_status = 'pending';
COMMENT ON TABLE  questions                    IS '训练题库（PostgreSQL为唯一Source of Truth，ChromaDB为可重建语义派生索引）';
COMMENT ON COLUMN questions.five_power_weights IS 'Q4: JSONB，key统一为INSIGHT/CONSTRUCT/DEDUCE/ADAPT/MIGRATE，各维度整数值之和=10';
COMMENT ON COLUMN questions.primary_power      IS 'Q4: 主五力，取five_power_weights最大值对应维度，发布时自动写入';
COMMENT ON COLUMN questions.knowledge_point_ids IS 'JSONB数组，支持多知识点，GIN索引支持@>包含查询';
COMMENT ON COLUMN questions.status             IS '状态流转: draft→analyzing→pending_review→published→archived';
COMMENT ON COLUMN questions.analysis_round     IS '已分析轮次，0=未分析，每次触发+1';

-- ────────────────────────────────────────────────────────────
-- 第 7 批：依赖第 6 批
-- ────────────────────────────────────────────────────────────

-- ⑲ question_analyses（题目大模型分析记录表，Q2: 原 question_annotations）
CREATE TABLE IF NOT EXISTS question_analyses (
    id                     BIGSERIAL   PRIMARY KEY,
    question_id            BIGINT      NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    round                  SMALLINT    NOT NULL,
    stem_snapshot          TEXT        NOT NULL,
    rejection_reason_used  TEXT,
    -- AI 识别的归属体系
    ai_subject_id          INT         REFERENCES subjects(id)  ON DELETE RESTRICT,
    ai_grade_id            INT         REFERENCES grades(id)    ON DELETE RESTRICT,
    ai_semester_id         INT         REFERENCES semesters(id) ON DELETE RESTRICT,
    ai_chapter_id          BIGINT      REFERENCES chapters(id)  ON DELETE RESTRICT,
    ai_knowledge_point_ids JSONB       NOT NULL DEFAULT '[]',
    ai_question_type       VARCHAR(20)
                           CHECK (ai_question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','FILL_BLANK','TRUE_FALSE','APPLICATION')),
    ai_answer              JSONB,
    ai_difficulty          VARCHAR(20)
                           CHECK (ai_difficulty IN ('basic','advanced','challenge')),
    ai_solution            TEXT,
    ai_common_error        TEXT,
    ai_power_solutions     JSONB,
    -- Q4: 五力权重 key 统一为新枚举值，总分=10
    ai_five_power_weights  JSONB,
    ai_transfer_directions JSONB       NOT NULL DEFAULT '[]',
    ai_reasoning           TEXT,
    analysis_status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                           CHECK (analysis_status IN ('pending','completed','failed')),
    fail_reason            TEXT,
    model_version          VARCHAR(50),
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(question_id, round)
);
CREATE INDEX IF NOT EXISTS idx_analyses_question ON question_analyses(question_id, round DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_pending  ON question_analyses(analysis_status)
    WHERE analysis_status = 'pending';   -- Q2: 修正 question_annotations→question_analyses
COMMENT ON TABLE  question_analyses                       IS '题目大模型分析记录表（v1.2.0重构，原 question_annotations，Q2修正），每次分析一条';
COMMENT ON COLUMN question_analyses.round                 IS '分析轮次：首次=1，驳回重分析自增；与 questions.analysis_round 同步';
COMMENT ON COLUMN question_analyses.rejection_reason_used IS '首次分析（round=1）为 NULL；驳回重分析（round≥2）必填';
COMMENT ON COLUMN question_analyses.ai_five_power_weights IS 'Q4: key统一为INSIGHT/CONSTRUCT/DEDUCE/ADAPT/MIGRATE，整数值之和=10';

-- ⑳ student_kp_stats（学生知识点练习统计表）
CREATE TABLE IF NOT EXISTS student_kp_stats (
    id                 BIGSERIAL    PRIMARY KEY,
    student_id         BIGINT       NOT NULL REFERENCES students(id)         ON DELETE RESTRICT,
    knowledge_point_id BIGINT       NOT NULL REFERENCES knowledge_points(id) ON DELETE RESTRICT,
    total_attempts     INT          NOT NULL DEFAULT 0,
    error_count        INT          NOT NULL DEFAULT 0,
    error_rate         DECIMAL(5,2),
    is_stat_valid      BOOLEAN      NOT NULL DEFAULT FALSE,
    last_practiced_at  TIMESTAMPTZ,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),  -- Q10: 补充
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, knowledge_point_id)
);
CREATE INDEX IF NOT EXISTS idx_skp_student       ON student_kp_stats(student_id);
CREATE INDEX IF NOT EXISTS idx_skp_kp            ON student_kp_stats(knowledge_point_id);
CREATE INDEX IF NOT EXISTS idx_skp_student_valid ON student_kp_stats(student_id, is_stat_valid) WHERE is_stat_valid = TRUE;
COMMENT ON TABLE  student_kp_stats               IS '学生知识点练习统计表（v1.3.0新增），管理员查看各知识点掌握情况';
COMMENT ON COLUMN student_kp_stats.error_rate    IS '错误率（百分比如 42.50），total_attempts<5 时为 NULL';
COMMENT ON COLUMN student_kp_stats.is_stat_valid IS 'total_attempts≥5 时系统自动置 TRUE';
COMMENT ON COLUMN student_kp_stats.created_at    IS 'Q10补充：首次为该学生该知识点建立统计的时间';

-- ────────────────────────────────────────────────────────────
-- 第 8 批：依赖第 7 批 + 第 2 批
-- ────────────────────────────────────────────────────────────

-- ㉑ training_sessions（训练会话表）
CREATE TABLE IF NOT EXISTS training_sessions (
    id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id               BIGINT      NOT NULL REFERENCES students(id)                    ON DELETE RESTRICT,
    config_version_id        BIGINT      NOT NULL REFERENCES training_config_versions(id)    ON DELETE RESTRICT,
    dimension_config_id      BIGINT               REFERENCES training_dimension_configs(id)  ON DELETE RESTRICT,
    -- Q6: 补充 ERROR_QUESTIONS，与 training_dimension_configs.dimension 保持一致
    training_dimension       VARCHAR(20) NOT NULL DEFAULT 'KNOWLEDGE_POINT'
                             CHECK (training_dimension IN ('KNOWLEDGE_POINT','UNIT','SEMESTER','ERROR_QUESTIONS','RANDOM')),
    -- 训练范围（按维度选填）
    knowledge_point_id       BIGINT               REFERENCES knowledge_points(id) ON DELETE RESTRICT,
    chapter_id               BIGINT               REFERENCES chapters(id)         ON DELETE RESTRICT,
    semester_id              INT                  REFERENCES semesters(id)        ON DELETE RESTRICT,
    -- 学习模式参数（来自五力画像）
    training_mode            VARCHAR(30) NOT NULL
                             CHECK (training_mode IN ('TRAIN_WEAKNESS','LEARN_BY_STRENGTH')),
    training_focus_power     VARCHAR(20)
                             CHECK (training_focus_power IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    preferred_force          VARCHAR(20)
                             CHECK (preferred_force IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    five_power_snapshot      JSONB       NOT NULL,
    question_snapshot        JSONB       NOT NULL,
    session_status           VARCHAR(20) NOT NULL DEFAULT 'active'
                             CHECK (session_status IN ('active','completed','abandoned')),
    source_type              VARCHAR(20) NOT NULL DEFAULT 'normal'
                             CHECK (source_type IN ('normal','mini','recommended')),
    total_questions          SMALLINT,
    correct_count            SMALLINT,
    ai_trigger_count         SMALLINT    NOT NULL DEFAULT 0,
    linked_chat_session_ids  JSONB       NOT NULL DEFAULT '[]',
    parent_chat_session_id   UUID,       -- 无 FK 约束，避免与 ai_chat_sessions 形成循环依赖
    is_early_end             BOOLEAN     NOT NULL DEFAULT FALSE,
    started_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at                 TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_training_sessions_student_status ON training_sessions(student_id, session_status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_sessions_active         ON training_sessions(student_id, session_status) WHERE session_status = 'active';
CREATE INDEX IF NOT EXISTS idx_training_sessions_kp             ON training_sessions(knowledge_point_id, started_at DESC) WHERE knowledge_point_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_training_sessions_chapter        ON training_sessions(chapter_id, started_at DESC) WHERE chapter_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_training_sessions_semester       ON training_sessions(semester_id) WHERE training_dimension = 'SEMESTER';
CREATE INDEX IF NOT EXISTS idx_training_sessions_dimension      ON training_sessions(training_dimension, started_at DESC);
COMMENT ON TABLE  training_sessions                         IS '训练会话表（UUID主键，防枚举）';
COMMENT ON COLUMN training_sessions.training_dimension      IS 'Q6: 补充 ERROR_QUESTIONS，与 training_dimension_configs 保持一致';
COMMENT ON COLUMN training_sessions.training_focus_power    IS 'Q4: 主训练力，INSIGHT/CONSTRUCT/DEDUCE/ADAPT/MIGRATE';
COMMENT ON COLUMN training_sessions.parent_chat_session_id  IS '关联 AI 对话会话，无 FK（避免 training_sessions ↔ ai_chat_sessions 循环依赖）';

-- ㉒ test_sessions（五力测试会话表）
CREATE TABLE IF NOT EXISTS test_sessions (
    id                     BIGSERIAL   PRIMARY KEY,
    student_id             BIGINT      NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    session_status         VARCHAR(20) NOT NULL DEFAULT 'in_progress'
                           CHECK (session_status IN ('in_progress','completed','interrupted')),
    config_snapshot        JSONB       NOT NULL,
    is_retest              BOOLEAN     NOT NULL DEFAULT FALSE,
    retest_count           SMALLINT    NOT NULL DEFAULT 1,
    total_time_sec         INT,
    interrupted_at         TIMESTAMPTZ,
    current_question_index SMALLINT    NOT NULL DEFAULT 0,
    started_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at           TIMESTAMPTZ,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_test_sessions_student ON test_sessions(student_id, created_at DESC);
COMMENT ON TABLE  test_sessions                        IS '五力认知测试会话表';
COMMENT ON COLUMN test_sessions.current_question_index IS '当前答到第几题（0-based），用于中断恢复';
COMMENT ON COLUMN test_sessions.config_snapshot        IS '测试时的配置快照（JSONB）';

-- ────────────────────────────────────────────────────────────
-- 第 9 批：依赖第 8 批 + 第 6 批
-- ────────────────────────────────────────────────────────────

-- ㉓ wrong_answer_records（错题记录表）
CREATE TABLE IF NOT EXISTS wrong_answer_records (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id       BIGINT      NOT NULL REFERENCES students(id)   ON DELETE RESTRICT,
    question_id      BIGINT      NOT NULL REFERENCES questions(id)  ON DELETE RESTRICT,
    source_module    VARCHAR(20) NOT NULL CHECK (source_module IN ('training','test')),
    -- Q3: VARCHAR(64) 有意设计，兼容 training_sessions(UUID) 和 test_sessions(BIGINT) 两种 ID
    source_session_id VARCHAR(64) NOT NULL,
    student_answer   TEXT,
    correct_answer   TEXT,
    review_status    VARCHAR(30) NOT NULL DEFAULT 'unreview'
                     CHECK (review_status IN ('unreview','reviewing','aha_achieved','pending_consolidation')),
    review_summary   TEXT,
    reviewed_at      TIMESTAMPTZ,
    aha_at           TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wrong_answers_student_status  ON wrong_answer_records(student_id, review_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_wrong_answers_question        ON wrong_answer_records(question_id);
CREATE INDEX IF NOT EXISTS idx_wrong_answers_unreview        ON wrong_answer_records(student_id, review_status, created_at DESC) WHERE review_status != 'aha_achieved';
CREATE INDEX IF NOT EXISTS idx_wrong_answers_question_student ON wrong_answer_records(question_id, student_id);  -- 补充: 高频错题 Top10 聚合
COMMENT ON TABLE  wrong_answer_records                  IS '错题记录表（UUID主键），跨模块共享：训练模块写入，助教模块读取并更新状态';
COMMENT ON COLUMN wrong_answer_records.source_session_id IS 'Q3决策：VARCHAR(64)有意兼容两种ID，与 source_module 联合区分';
COMMENT ON COLUMN wrong_answer_records.review_status     IS 'unreview→reviewing→aha_achieved(终态) 或 pending_consolidation';

-- ㉔ training_answer_records（训练答题记录表）
CREATE TABLE IF NOT EXISTS training_answer_records (
    id               BIGSERIAL    PRIMARY KEY,
    session_id       UUID         NOT NULL REFERENCES training_sessions(id) ON DELETE RESTRICT,
    question_id      BIGINT       NOT NULL REFERENCES questions(id)         ON DELETE RESTRICT,
    question_index   SMALLINT     NOT NULL,
    power_type       VARCHAR(20)  NOT NULL
                     CHECK (power_type IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    student_answer   TEXT,
    answer_quality   DECIMAL(3,2),
    is_correct       BOOLEAN,
    ai_score_status  VARCHAR(20)  CHECK (ai_score_status IN ('pending','completed','timeout','skipped')),
    time_spent_sec   SMALLINT     NOT NULL,
    hint_level_used  SMALLINT     NOT NULL DEFAULT 0,
    rag_generated    BOOLEAN      NOT NULL DEFAULT FALSE,
    rag_content      TEXT,
    generation_status VARCHAR(20) CHECK (generation_status IN ('pending','completed','failed','degraded')),
    rag_feedback     VARCHAR(20)  CHECK (rag_feedback IN ('helpful','unhelpful')),
    is_seed_data     BOOLEAN      NOT NULL DEFAULT FALSE,
    answered_at      TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(session_id, question_index)
);
CREATE INDEX IF NOT EXISTS idx_training_answers_session       ON training_answer_records(session_id, question_index);
CREATE INDEX IF NOT EXISTS idx_training_answers_student_power ON training_answer_records(session_id, power_type, is_correct);
COMMENT ON TABLE  training_answer_records              IS '训练答题记录表';
COMMENT ON COLUMN training_answer_records.power_type   IS 'Q4: 本题主训练力，INSIGHT/CONSTRUCT/DEDUCE/ADAPT/MIGRATE';
COMMENT ON COLUMN training_answer_records.answer_quality IS '答案质量系数 0~1，选择题按选项得分归一化';
COMMENT ON COLUMN training_answer_records.hint_level_used IS '使用的最高提示级别，0=未使用';

-- ㉕ test_answer_records（测试答题记录表）
CREATE TABLE IF NOT EXISTS test_answer_records (
    id              BIGSERIAL    PRIMARY KEY,
    session_id      BIGINT       NOT NULL REFERENCES test_sessions(id)            ON DELETE RESTRICT,
    question_id     INT          NOT NULL REFERENCES cognitive_test_questions(id) ON DELETE RESTRICT,
    question_index  SMALLINT     NOT NULL,
    selected_option VARCHAR(5),
    answer_quality  DECIMAL(3,2),
    time_spent_sec  SMALLINT     NOT NULL,
    modify_count    SMALLINT     NOT NULL DEFAULT 0,
    is_rushed       BOOLEAN      NOT NULL DEFAULT FALSE,
    is_timeout      BOOLEAN      NOT NULL DEFAULT FALSE,
    base_score      DECIMAL(6,2),
    answered_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(session_id, question_index)
);
CREATE INDEX IF NOT EXISTS idx_test_answers_session ON test_answer_records(session_id);
COMMENT ON TABLE  test_answer_records           IS '五力测试答题记录表';
COMMENT ON COLUMN test_answer_records.is_rushed IS '是否极速作答（<5秒）';

-- ㉖ five_power_profiles（五力测试画像表）
CREATE TABLE IF NOT EXISTS five_power_profiles (
    id                  BIGSERIAL   PRIMARY KEY,
    student_id          BIGINT      NOT NULL REFERENCES students(id)     ON DELETE RESTRICT,
    test_session_id     BIGINT      NOT NULL REFERENCES test_sessions(id) ON DELETE RESTRICT UNIQUE,
    -- ① 能力分（来自客观题，0~100）Q4: 字段名统一
    insight_ability     SMALLINT    NOT NULL,
    construct_ability   SMALLINT    NOT NULL,   -- 原 structure_ability
    deduce_ability      SMALLINT    NOT NULL,   -- 原 inference_ability
    adapt_ability       SMALLINT    NOT NULL,   -- 原 adaptation_ability
    migrate_ability     SMALLINT    NOT NULL,   -- 原 transfer_ability
    -- ② 偏好分（来自偏好题，五者总和=100）
    insight_preference  SMALLINT    NOT NULL,
    construct_preference SMALLINT   NOT NULL,
    deduce_preference   SMALLINT    NOT NULL,
    adapt_preference    SMALLINT    NOT NULL,
    migrate_preference  SMALLINT    NOT NULL,
    -- ③ 综合分（ability×0.70 + preference×0.30）
    insight_final       SMALLINT    NOT NULL,
    construct_final     SMALLINT    NOT NULL,
    deduce_final        SMALLINT    NOT NULL,
    adapt_final         SMALLINT    NOT NULL,
    migrate_final       SMALLINT    NOT NULL,
    -- ④ 画像标签（Q4: 值域统一）
    primary_weakness    VARCHAR(20) CHECK (primary_weakness  IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    secondary_weakness  VARCHAR(20) CHECK (secondary_weakness IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    primary_strength    VARCHAR(20) CHECK (primary_strength  IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    primary_entry       VARCHAR(20) CHECK (primary_entry     IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    secondary_entry     VARCHAR(20) CHECK (secondary_entry   IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    recommended_mode    VARCHAR(30) CHECK (recommended_mode  IN ('TRAIN_WEAKNESS','LEARN_BY_STRENGTH')),
    preferred_force     VARCHAR(20) CHECK (preferred_force   IN ('INSIGHT','CONSTRUCT','DEDUCE','ADAPT','MIGRATE')),
    profile_confidence  DECIMAL(3,2),
    -- ⑤ 状态
    is_latest           BOOLEAN     NOT NULL DEFAULT FALSE,
    ai_analysis_text    TEXT,
    ai_analysis_status  VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (ai_analysis_status IN ('pending','processing','completed','failed')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ability_range CHECK (
        insight_ability   BETWEEN 0 AND 100 AND construct_ability BETWEEN 0 AND 100 AND
        deduce_ability    BETWEEN 0 AND 100 AND adapt_ability     BETWEEN 0 AND 100 AND
        migrate_ability   BETWEEN 0 AND 100
    ),
    CONSTRAINT chk_preference_range CHECK (
        insight_preference   BETWEEN 0 AND 100 AND construct_preference BETWEEN 0 AND 100 AND
        deduce_preference    BETWEEN 0 AND 100 AND adapt_preference     BETWEEN 0 AND 100 AND
        migrate_preference   BETWEEN 0 AND 100
    )
);
CREATE INDEX IF NOT EXISTS idx_five_power_profiles_student_latest ON five_power_profiles(student_id, is_latest);
CREATE INDEX IF NOT EXISTS idx_five_power_profiles_student_time   ON five_power_profiles(student_id, created_at DESC);
COMMENT ON TABLE  five_power_profiles                  IS '五力测试画像表，每次测试产生一条，is_latest 标记最新';
COMMENT ON COLUMN five_power_profiles.construct_ability IS 'Q4: 建构力能力分（原 structure_ability）';
COMMENT ON COLUMN five_power_profiles.is_latest         IS '当前最新画像标记，同一学生仅一条为 TRUE（应用层保证）';

-- ────────────────────────────────────────────────────────────
-- 第 10 批：依赖第 9 批 + 第 1 批
-- ────────────────────────────────────────────────────────────

-- ㉗ ai_chat_sessions（助教对话会话表）
CREATE TABLE IF NOT EXISTS ai_chat_sessions (
    id                         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id                 BIGINT      NOT NULL REFERENCES students(id)           ON DELETE RESTRICT,
    session_mode               VARCHAR(30) NOT NULL
                               CHECK (session_mode IN ('free_chat','wrong_review','training_error_guidance')),
    status                     VARCHAR(20) NOT NULL DEFAULT 'active'
                               CHECK (status IN ('active','completed','timeout')),
    linked_question_id         BIGINT      REFERENCES questions(id)          ON DELETE RESTRICT,
    linked_wrong_id            UUID        REFERENCES wrong_answer_records(id) ON DELETE RESTRICT,
    parent_training_session_id UUID        REFERENCES training_sessions(id)   ON DELETE RESTRICT,
    silence_mode               BOOLEAN     NOT NULL DEFAULT FALSE,
    silence_scope              VARCHAR(20) CHECK (silence_scope IN ('question','session')),
    silence_triggered_at       TIMESTAMPTZ,
    proactive_count            SMALLINT    NOT NULL DEFAULT 0,
    aha_count                  SMALLINT    NOT NULL DEFAULT 0,
    session_summary            TEXT,
    started_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at                   TIMESTAMPTZ,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_student_status ON ai_chat_sessions(student_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active         ON ai_chat_sessions(student_id, status) WHERE status = 'active';
COMMENT ON TABLE  ai_chat_sessions                IS '助教对话会话表（UUID主键）';
COMMENT ON COLUMN ai_chat_sessions.proactive_count IS 'AI 主动介入次数，达3次后不再主动（应用层控制）';
COMMENT ON COLUMN ai_chat_sessions.silence_mode    IS '学生明确拒绝提示时进入沉默模式';

-- ────────────────────────────────────────────────────────────
-- 第 11 批：依赖第 10 批 + 第 1 批
-- ────────────────────────────────────────────────────────────

-- ㉘ ai_student_strategy_profiles（学生策略有效性档案表）
CREATE TABLE IF NOT EXISTS ai_student_strategy_profiles (
    id                  BIGSERIAL    PRIMARY KEY,
    student_id          BIGINT       NOT NULL REFERENCES students(id)                ON DELETE RESTRICT,
    strategy_id         VARCHAR(32)  NOT NULL REFERENCES ai_heuristic_strategies(strategy_id) ON DELETE RESTRICT,
    total_uses          INT          NOT NULL DEFAULT 0,
    effective_count     INT          NOT NULL DEFAULT 0,
    ineffective_count   INT          NOT NULL DEFAULT 0,
    positive_ratings    INT          NOT NULL DEFAULT 0,
    negative_ratings    INT          NOT NULL DEFAULT 0,
    effectiveness_score DECIMAL(5,2) NOT NULL DEFAULT 50.0,
    last_used_at        TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, strategy_id),
    CONSTRAINT chk_effectiveness_score CHECK (effectiveness_score BETWEEN 0 AND 100)
);
CREATE INDEX IF NOT EXISTS idx_strategy_profiles_student ON ai_student_strategy_profiles(student_id, effectiveness_score DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_score            ON ai_student_strategy_profiles(student_id, effectiveness_score DESC) WHERE total_uses > 0;
COMMENT ON TABLE  ai_student_strategy_profiles                    IS '学生策略有效性档案，每生每策略维护一条';
COMMENT ON COLUMN ai_student_strategy_profiles.effectiveness_score IS 'ES=(effective+positive×0.5)/(total+1)×100，初始50（冷启动保护）';

-- ㉙ ai_chat_messages（助教对话消息表）
CREATE TABLE IF NOT EXISTS ai_chat_messages (
    id             BIGSERIAL   PRIMARY KEY,
    session_id     UUID        NOT NULL REFERENCES ai_chat_sessions(id)       ON DELETE RESTRICT,
    role           VARCHAR(20) NOT NULL CHECK (role IN ('student','assistant','system')),
    content        TEXT        NOT NULL,
    image_url      VARCHAR(512),
    strategy_id    VARCHAR(32) REFERENCES ai_heuristic_strategies(strategy_id) ON DELETE RESTRICT,
    is_proactive   BOOLEAN     NOT NULL DEFAULT FALSE,
    is_aha_trigger BOOLEAN     NOT NULL DEFAULT FALSE,
    student_rating VARCHAR(10) CHECK (student_rating IN ('like','dislike')),
    tokens_used    INT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session      ON ai_chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_time ON ai_chat_messages(session_id, created_at DESC);
COMMENT ON TABLE  ai_chat_messages                IS '助教对话消息表';
COMMENT ON COLUMN ai_chat_messages.is_proactive   IS 'AI 主动介入消息标记';
COMMENT ON COLUMN ai_chat_messages.is_aha_trigger IS '是否触发学生理解突破';

-- ㉚ ai_strategy_events（策略事件日志表）
CREATE TABLE IF NOT EXISTS ai_strategy_events (
    id               BIGSERIAL   PRIMARY KEY,
    session_id       UUID        NOT NULL REFERENCES ai_chat_sessions(id)        ON DELETE RESTRICT,
    student_id       BIGINT      NOT NULL REFERENCES students(id)                ON DELETE RESTRICT,
    event_type       VARCHAR(30) NOT NULL
                     CHECK (event_type IN ('strategy_start','strategy_switch','aha_moment','silence_mode','proactive_trigger')),
    from_strategy_id VARCHAR(32) REFERENCES ai_heuristic_strategies(strategy_id) ON DELETE RESTRICT,
    to_strategy_id   VARCHAR(32) REFERENCES ai_heuristic_strategies(strategy_id) ON DELETE RESTRICT,
    switch_reason    VARCHAR(100),
    linked_message_id BIGINT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_strategy_events_session ON ai_strategy_events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_strategy_events_student ON ai_strategy_events(student_id, event_type, created_at DESC);
COMMENT ON TABLE ai_strategy_events IS '策略事件日志表，记录策略使用/切换/突破/沉默等关键事件';

-- ────────────────────────────────────────────────────────────
-- 第 12 批：依赖第 11 批 + 第 1 批
-- ────────────────────────────────────────────────────────────

-- ㉛ student_prompt_insights（学生洞察条目历史表）
CREATE TABLE IF NOT EXISTS student_prompt_insights (
    id                BIGSERIAL    PRIMARY KEY,
    student_id        BIGINT       NOT NULL REFERENCES students(id)         ON DELETE RESTRICT,
    content           TEXT         NOT NULL,
    insight_type      VARCHAR(30)  NOT NULL
                      CHECK (insight_type IN ('interest','mood','life_event','analogy_pref','family','learning_attitude','other')),
    is_sensitive      BOOLEAN      NOT NULL DEFAULT FALSE,
    source            VARCHAR(10)  NOT NULL CHECK (source IN ('AI','ADMIN')),
    source_session_id UUID         REFERENCES ai_chat_sessions(id) ON DELETE RESTRICT,
    added_by_admin_id BIGINT       REFERENCES admin_users(id)      ON DELETE RESTRICT,
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    weight            DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    archived_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_insights_student_active ON student_prompt_insights(student_id, is_active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_insights_session        ON student_prompt_insights(source_session_id) WHERE source_session_id IS NOT NULL;
COMMENT ON TABLE  student_prompt_insights              IS '学生洞察条目历史表（v2.1新增），支持时效性管理（>90天自动归档）';
COMMENT ON COLUMN student_prompt_insights.insight_type IS 'interest/mood/life_event/analogy_pref/family/learning_attitude/other';
COMMENT ON COLUMN student_prompt_insights.is_sensitive IS '敏感信息不注入 Prompt，仅管理员可见';
COMMENT ON COLUMN student_prompt_insights.weight       IS '权重 0~1，随时间衰减（定时任务维护）';

-- ────────────────────────────────────────────────────────────
-- 第 13 批：日志类表
-- ────────────────────────────────────────────────────────────

-- ㉜ ai_token_usage_log（AI Token 消耗日志表）
CREATE TABLE IF NOT EXISTS ai_token_usage_log (
    id                BIGSERIAL    PRIMARY KEY,
    student_id        BIGINT       REFERENCES students(id) ON DELETE RESTRICT,   -- 可空：后台任务无 student
    module            VARCHAR(20)  NOT NULL CHECK (module IN ('training','assistant','test','admin')),
    call_type         VARCHAR(30)  NOT NULL CHECK (call_type IN ('rag','chat','analysis','annotation','embedding')),
    provider          VARCHAR(30)  NOT NULL,
    model             VARCHAR(50)  NOT NULL,
    prompt_tokens     INT          NOT NULL,
    completion_tokens INT          NOT NULL DEFAULT 0,
    total_tokens      INT          NOT NULL,
    cost_usd          DECIMAL(10,6),
    session_id        VARCHAR(64),
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_token_log_student ON ai_token_usage_log(student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_log_date    ON ai_token_usage_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_log_module  ON ai_token_usage_log(module, created_at DESC);
-- idx_token_log_daily: DATE(TIMESTAMPTZ) 非 IMMUTABLE 无法建函数索引
-- 日期范围查询由 idx_token_log_date (created_at DESC) 覆盖，应用层用 DATE_TRUNC('day', created_at AT TIME ZONE 'Asia/Shanghai') 过滤
COMMENT ON TABLE  ai_token_usage_log                   IS 'AI Token 消耗日志，student_id 可为 NULL（后台标注任务）';
COMMENT ON COLUMN ai_token_usage_log.completion_tokens IS 'Embedding 调用无 completion，默认 0';

-- ㉝ system_downgrade_log（系统降级日志表）
CREATE TABLE IF NOT EXISTS system_downgrade_log (
    id           BIGSERIAL   PRIMARY KEY,
    module       VARCHAR(20) NOT NULL CHECK (module IN ('training','assistant')),
    error_type   VARCHAR(50) NOT NULL
                 CHECK (error_type IN ('rag_timeout','llm_unavailable','vector_db_error','embedding_error')),
    error_detail TEXT,
    student_id   BIGINT      REFERENCES students(id) ON DELETE RESTRICT,
    session_id   VARCHAR(64),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_downgrade_log_time ON system_downgrade_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_downgrade_log_type ON system_downgrade_log(error_type, created_at DESC);
COMMENT ON TABLE system_downgrade_log IS '系统降级日志：RAG超时/LLM不可用/ChromaDB错误/向量化失败';

-- ㉞ admin_audit_logs（管理员审计日志表）
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id          BIGSERIAL   PRIMARY KEY,
    admin_id    BIGINT      NOT NULL REFERENCES admin_users(id) ON DELETE RESTRICT,
    action      VARCHAR(50) NOT NULL,
    target_type VARCHAR(30),
    target_id   VARCHAR(64),
    detail      JSONB,
    ip_address  VARCHAR(50) NOT NULL,
    user_agent  VARCHAR(200),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin  ON admin_audit_logs(admin_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON admin_audit_logs(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_time   ON admin_audit_logs(created_at DESC);
COMMENT ON TABLE  admin_audit_logs        IS '管理员审计日志，记录所有管理操作';
COMMENT ON COLUMN admin_audit_logs.action IS 'LOGIN/LOGOUT/CREATE_QUESTION/CONFIRM_ANNOTATION/CREATE_ADMIN 等';
COMMENT ON COLUMN admin_audit_logs.detail IS 'JSONB：操作前后值对比快照';

-- ============================================================
-- §5. 视图
-- ============================================================

CREATE OR REPLACE VIEW v_cognitive_test_status AS
SELECT
    COUNT(*) FILTER (WHERE status = 'published')  AS published_count,
    COUNT(*) FILTER (WHERE status = 'draft')      AS draft_count,
    COUNT(*) FILTER (WHERE status = 'archived')   AS archived_count,
    (COUNT(*) FILTER (WHERE status = 'published')) = 20 AS test_available
FROM cognitive_test_questions;

COMMENT ON VIEW v_cognitive_test_status IS '五力测试可用状态：test_available=true 表示已发布恰好20题，可开放测试功能';

-- ============================================================
-- §6. 触发器（批量为所有含 updated_at 的表挂载）
-- ============================================================

DO $$
DECLARE
    tbl TEXT;
    tbls TEXT[] := ARRAY[
        'admin_users',
        'system_configs',
        'ai_heuristic_strategies',
        'students',
        'parent_student_bindings',
        'five_power_training_profiles',
        'student_ai_prompt_summaries',
        'chapters',
        'knowledge_points',
        'questions',
        'question_analyses',
        'training_dimension_configs',
        'cognitive_test_questions',
        'ai_student_strategy_profiles',
        'student_kp_stats'
    ];
BEGIN
    FOREACH tbl IN ARRAY tbls LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_%s_updated_at ON %I;
             CREATE TRIGGER trg_%s_updated_at
                 BEFORE UPDATE ON %I
                 FOR EACH ROW EXECUTE FUNCTION update_updated_at();',
            tbl, tbl, tbl, tbl
        );
    END LOOP;
    RAISE NOTICE '已为 % 张表挂载 updated_at 触发器', array_length(tbls, 1);
END $$;

-- ============================================================
-- §7. 额外业务约束
-- ============================================================

-- 答案质量系数约束（0~1 或 NULL）
ALTER TABLE training_answer_records
    DROP CONSTRAINT IF EXISTS chk_answer_quality;
ALTER TABLE training_answer_records
    ADD  CONSTRAINT chk_answer_quality
    CHECK (answer_quality IS NULL OR answer_quality BETWEEN 0 AND 1);

-- 画像置信度约束（0~1 或 NULL）
ALTER TABLE five_power_profiles
    DROP CONSTRAINT IF EXISTS chk_confidence;
ALTER TABLE five_power_profiles
    ADD  CONSTRAINT chk_confidence
    CHECK (profile_confidence IS NULL OR profile_confidence BETWEEN 0 AND 1);

-- 洞察条目权重约束（0~1）
ALTER TABLE student_prompt_insights
    DROP CONSTRAINT IF EXISTS chk_insight_weight;
ALTER TABLE student_prompt_insights
    ADD  CONSTRAINT chk_insight_weight
    CHECK (weight BETWEEN 0 AND 1);

-- ============================================================
-- §8. 应用用户权限（Q12: mesh_app 低权限用户）
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mesh_app') THEN
        CREATE USER mesh_app WITH PASSWORD 'MeshApp2026!Change_Me';
        RAISE NOTICE '已创建应用用户 mesh_app，请立即修改密码';
    ELSE
        RAISE NOTICE '应用用户 mesh_app 已存在，跳过创建';
    END IF;
END $$;

GRANT CONNECT ON DATABASE mesh_edu TO mesh_app;
GRANT USAGE   ON SCHEMA public TO mesh_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES   IN SCHEMA public TO mesh_app;
GRANT USAGE, SELECT                  ON ALL SEQUENCES IN SCHEMA public TO mesh_app;

-- 对未来新建的表自动授权
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES    TO mesh_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT                  ON SEQUENCES TO mesh_app;

-- ============================================================
-- 完成
-- ============================================================
DO $$ BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'init_db.sql 执行完毕';
    RAISE NOTICE '数据库: mesh_edu  |  共 34 张表';
    RAISE NOTICE '请执行 seed.sql 写入初始化数据';
    RAISE NOTICE '请修改 mesh_app 用户密码！';
    RAISE NOTICE '========================================';
END $$;

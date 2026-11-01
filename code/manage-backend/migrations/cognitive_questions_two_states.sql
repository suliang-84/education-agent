-- 测试题状态收敛为两态（已启用 published / 已停用 archived）
-- 1) 存量草稿迁移为已停用（保持不参与测试，管理员可编辑后启用）
UPDATE cognitive_test_questions SET status = 'archived' WHERE status = 'draft';
-- 2) 默认值改为 archived（新建即已停用）
ALTER TABLE cognitive_test_questions ALTER COLUMN status SET DEFAULT 'archived';
-- 说明：status 的 CHECK 约束仍保留 'draft' 取值（不再产生，无需重建约束）

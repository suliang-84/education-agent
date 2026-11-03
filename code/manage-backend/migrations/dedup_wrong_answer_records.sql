-- 错题集改版：同一学生同一道题只保留一条错题记录（合并去重），并加唯一约束
-- review_status：'unreview' = 待攻克，'aha_achieved' = 已攻克
-- 合并规则：保留最近一条（created_at 最大），其余删除；执行前请先备份：
--   CREATE TABLE wrong_answer_records_bak AS SELECT * FROM wrong_answer_records;
DELETE FROM wrong_answer_records w
USING (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY student_id, question_id ORDER BY created_at DESC, id) AS rn
    FROM wrong_answer_records
) d
WHERE w.id = d.id AND d.rn > 1;

-- 历史状态统一：复盘中 / 待巩固都视为待攻克
UPDATE wrong_answer_records SET review_status = 'unreview' WHERE review_status IN ('reviewing', 'pending_consolidation');

CREATE UNIQUE INDEX IF NOT EXISTS uq_wrong_answers_student_question
    ON wrong_answer_records(student_id, question_id);

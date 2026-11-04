-- 个人洞察：把「管理员确认的部分」和「AI 补充的部分」分开存，AI 更新时只改自己的部分，管理员写的内容不会被改写 / 丢掉
-- personal_insight = insight_admin_text + 换行 + insight_ai_text（页面展示和助教提示词读取的仍是 personal_insight）
ALTER TABLE student_ai_prompt_summaries ADD COLUMN IF NOT EXISTS insight_admin_text TEXT;
ALTER TABLE student_ai_prompt_summaries ADD COLUMN IF NOT EXISTS insight_ai_text    TEXT;
-- 已有内容全部视为「已确认」，受保护
UPDATE student_ai_prompt_summaries
   SET insight_admin_text = personal_insight
 WHERE personal_insight IS NOT NULL AND personal_insight <> '' AND insight_admin_text IS NULL;

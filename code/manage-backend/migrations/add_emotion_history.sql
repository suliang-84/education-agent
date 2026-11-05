-- AI 助教对话的情绪判断记录（画像预警「聊天出现负面情绪」使用）
-- 每次对话摘要更新（退出助教页 / 小程序退到后台）时判断一次，只存判断等级和一句依据，不存聊天原文
-- 数组元素：{"at": ISO 时间, "level": "normal|mild|significant|urgent", "reason": "一句话依据"}，只保留最近 10 条
ALTER TABLE student_ai_prompt_summaries
    ADD COLUMN IF NOT EXISTS emotion_history JSONB NOT NULL DEFAULT '[]'::jsonb;

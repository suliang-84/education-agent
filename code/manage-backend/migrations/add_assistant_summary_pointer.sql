-- AI 助教：永久会话没有「结束」，按消息累积滚动生成摘要；记录已摘要到的最新消息 id
ALTER TABLE ai_chat_sessions ADD COLUMN IF NOT EXISTS summary_message_id BIGINT NOT NULL DEFAULT 0;
COMMENT ON COLUMN ai_chat_sessions.summary_message_id IS '已生成摘要覆盖到的最新消息 id（滚动摘要用）';

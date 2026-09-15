from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AiHeuristicStrategy(Base, TimestampMixin):
    __tablename__ = "ai_heuristic_strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicable_powers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    default_priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    example_phrase: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SystemConfig(Base, TimestampMixin):
    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False, default="string")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class AiChatSession(Base):
    """AI 对话会话（无 updated_at）"""
    __tablename__ = "ai_chat_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    session_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    linked_question_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    linked_wrong_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    parent_training_session_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    silence_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    silence_scope: Mapped[str | None] = mapped_column(String(20), nullable=True)
    silence_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proactive_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    aha_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    session_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AiChatMessage(Base):
    """AI 对话消息（无 updated_at）"""
    __tablename__ = "ai_chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    strategy_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_proactive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_aha_trigger: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    student_rating: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AiStrategyEvent(Base):
    """AI 策略事件（无 updated_at）"""
    __tablename__ = "ai_strategy_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    from_strategy_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_strategy_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    switch_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linked_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AiStudentStrategyProfile(Base):
    """学生 AI 策略效果档案（有 updated_at 触发器）"""
    __tablename__ = "ai_student_strategy_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(32), nullable=False)
    total_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    effective_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ineffective_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    positive_ratings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    negative_ratings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    effectiveness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=50.0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AiTokenUsageLog(Base):
    """AI Token 用量日志（无 updated_at）"""
    __tablename__ = "ai_token_usage_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    module: Mapped[str] = mapped_column(String(20), nullable=False)
    call_type: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StudentAiPromptSummary(Base, TimestampMixin):
    """学生 AI 对话摘要"""
    __tablename__ = "student_ai_prompt_summaries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    learning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_summary_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    learning_summary_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    personal_insight: Mapped[str | None] = mapped_column(Text, nullable=True)
    personal_insight_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    insight_updated_by: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class StudentPromptInsight(Base):
    """学生个人 prompt 洞察（无 updated_at）"""
    __tablename__ = "student_prompt_insights"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    insight_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    source_session_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    added_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    weight: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=1.00)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SystemDowngradeLog(Base):
    """系统降级日志（无 updated_at）"""
    __tablename__ = "system_downgrade_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    module: Mapped[str] = mapped_column(String(20), nullable=False)
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

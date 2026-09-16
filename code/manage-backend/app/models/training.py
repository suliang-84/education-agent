from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrainingDimensionConfig(Base):
    """训练维度配置（无 updated_at，由触发器维护）"""

    __tablename__ = "training_dimension_configs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dimension: Mapped[str] = mapped_column(String(20), nullable=False)
    version_number: Mapped[str] = mapped_column(String(20), nullable=False)
    questions_per_session: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=5)
    dedup_window_size: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=30)
    difficulty_ratio: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    wrong_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_question_mix_ratio: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    remove_after_correct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TrainingConfigVersion(Base):
    """训练全局配置版本"""

    __tablename__ = "training_config_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    version_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    training_total_questions: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=5)
    difficulty_ratio: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dedup_window_size: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=30)
    is_correct_threshold: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    rag_trigger_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="all")
    rag_topk_questions: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    rag_topk_strategies: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2)
    rag_similarity_threshold: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    rag_timeout_seconds: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=8)
    profile_decay_coefficient: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TrainingSession(Base):
    """训练会话（无 updated_at）"""

    __tablename__ = "training_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    config_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dimension_config_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    training_dimension: Mapped[str] = mapped_column(
        String(20), nullable=False, default="KNOWLEDGE_POINT"
    )
    knowledge_point_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    chapter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    semester_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    training_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    training_focus_power: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_force: Mapped[str | None] = mapped_column(String(20), nullable=True)
    five_power_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    question_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    session_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    total_questions: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    correct_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ai_trigger_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    linked_chat_session_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    parent_chat_session_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    is_early_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TrainingAnswerRecord(Base):
    """训练答题记录（无 updated_at）"""

    __tablename__ = "training_answer_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    question_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    power_type: Mapped[str] = mapped_column(String(20), nullable=False)
    student_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_quality: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ai_score_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    time_spent_sec: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hint_level_used: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    rag_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rag_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rag_feedback: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_seed_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

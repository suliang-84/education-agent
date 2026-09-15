from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_type: Mapped[str] = mapped_column(String(10), nullable=False, default="STUDENT")
    openid_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 加密存储
    phone_masked: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    subject_prefs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_minor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)


class ParentStudentBinding(Base, TimestampMixin):
    __tablename__ = "parent_student_bindings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    parent_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bind_method: Mapped[str] = mapped_column(String(20), nullable=False)
    bind_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)


class InviteCode(Base):
    """邀请码（无 updated_at）"""
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    used_by_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SmsCode(Base):
    """短信验证码（无 updated_at）"""
    __tablename__ = "sms_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    phone_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fail_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FivePowerProfile(Base):
    """五力测评档案（仅 created_at）"""
    __tablename__ = "five_power_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    test_session_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    insight_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    construct_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    deduce_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    adapt_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    migrate_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    insight_preference: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    construct_preference: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    deduce_preference: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    adapt_preference: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    migrate_preference: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    insight_final: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    construct_final: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    deduce_final: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    adapt_final: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    migrate_final: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    primary_weakness: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_weakness: Mapped[str | None] = mapped_column(String(20), nullable=True)
    primary_strength: Mapped[str | None] = mapped_column(String(20), nullable=True)
    primary_entry: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_entry: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommended_mode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    preferred_force: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_analysis_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_analysis_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FivePowerTrainingProfile(Base):
    """五力训练档案（有 updated_at 触发器）"""
    __tablename__ = "five_power_training_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    insight_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=50)
    construct_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=50)
    deduce_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=50)
    adapt_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=50)
    migrate_ability: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=50)
    total_training_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestSession(Base):
    """五力测试会话（无 updated_at）"""
    __tablename__ = "test_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    session_status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    config_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_retest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retest_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    total_time_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interrupted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_question_index: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestAnswerRecord(Base):
    """测试答题记录（无 updated_at）"""
    __tablename__ = "test_answer_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)
    question_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    selected_option: Mapped[str | None] = mapped_column(String(5), nullable=True)
    answer_quality: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    time_spent_sec: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    modify_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    is_rushed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_timeout: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    base_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WrongAnswerRecord(Base):
    """错题记录（无 updated_at）"""
    __tablename__ = "wrong_answer_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_module: Mapped[str] = mapped_column(String(20), nullable=False)
    source_session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    student_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="unreview")
    review_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aha_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StudentKpStat(Base, TimestampMixin):
    """学生知识点统计"""
    __tablename__ = "student_kp_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    knowledge_point_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_stat_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

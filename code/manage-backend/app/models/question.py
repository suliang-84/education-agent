from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    semester_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chapter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    knowledge_point_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    question_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    answer: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    common_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    power_solutions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    five_power_weights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    primary_power: Mapped[str | None] = mapped_column(String(20), nullable=True)
    transfer_direction: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    analysis_round: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    embedded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_seed_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)


class QuestionAnalysis(Base, TimestampMixin):
    __tablename__ = "question_analyses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    question_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    round: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    rejection_reason_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_grade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_semester_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_chapter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ai_knowledge_point_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ai_difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_common_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_power_solutions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_five_power_weights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_transfer_directions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ai_question_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_answer: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

from datetime import datetime

from sqlalchemy import BigInteger, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CognitiveTestQuestion(Base, TimestampMixin):
    __tablename__ = "cognitive_test_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_no: Mapped[int] = mapped_column(Integer, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    answers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reference_time_sec: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=90)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

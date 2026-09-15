from sqlalchemy import BigInteger, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Grade(Base, TimestampMixin):
    __tablename__ = "grades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Semester(Base, TimestampMixin):
    __tablename__ = "semesters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grade_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(5), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class KnowledgePoint(Base, TimestampMixin):
    __tablename__ = "knowledge_points"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chapter_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

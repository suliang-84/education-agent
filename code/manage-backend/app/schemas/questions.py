"""题库管理 Pydantic Schemas"""
from typing import Any
from pydantic import BaseModel, Field


class QuestionCreateReq(BaseModel):
    stem: str = Field(..., min_length=1, max_length=1000)
    image_url: str | None = None


class RejectReq(BaseModel):
    rejection_reason: str = Field(..., min_length=1, max_length=500)


class PublishPayload(BaseModel):
    subject_id: int
    grade_id: int
    semester_id: int
    chapter_id: int | None = None
    knowledge_point_ids: list[int] = []
    difficulty: str = Field(..., pattern=r'^(basic|advanced|challenge)$')
    solution: str
    common_error: str | None = None
    power_solutions: dict[str, str] | None = None
    five_power_weights: dict[str, int]
    transfer_directions: list[str] = []
    question_type: str | None = None
    answer: dict[str, Any] | None = None

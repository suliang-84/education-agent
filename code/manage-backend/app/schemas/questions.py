"""题库管理 Pydantic Schemas"""
from typing import Any
from pydantic import BaseModel, Field


class QuestionCreateReq(BaseModel):
    stem: str = Field(..., min_length=1, max_length=1000)
    image_url: str | None = None


class RejectReq(BaseModel):
    rejection_reason: str = Field(..., min_length=1, max_length=500)


class SetActiveReq(BaseModel):
    is_active: bool


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


class ContentUpdateReq(PublishPayload):
    """已发布/已停用题目的内容修改，字段同发布，另可修改题干"""
    stem: str | None = Field(None, min_length=1, max_length=1000)


class ReviewSaveReq(BaseModel):
    """审核页暂存：只保存编辑内容，字段全部可选，不做发布校验，不改变题目状态"""
    stem: str | None = Field(None, min_length=1, max_length=1000)
    subject_id: int | None = None
    grade_id: int | None = None
    semester_id: int | None = None
    chapter_id: int | None = None
    knowledge_point_ids: list[int] = []
    question_type: str | None = None
    answer: dict[str, Any] | None = None
    difficulty: str | None = Field(None, pattern=r'^(basic|advanced|challenge)$')
    solution: str | None = None
    common_error: str | None = None
    power_solutions: dict[str, str] | None = None
    five_power_weights: dict[str, int] | None = None
    transfer_directions: list[str] = []


class BatchIdsReq(BaseModel):
    """批量操作请求体；数量/合法性由 service.normalize_batch_ids 校验（QBATCH-001/002）"""
    question_ids: list[Any] = []

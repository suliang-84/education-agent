"""五力测试题模块 Pydantic Schemas"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ── 请求体 ────────────────────────────────────────────────────

class AnswerInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    force_weights: dict[str, int]

    @model_validator(mode='after')
    def validate_weights(self) -> 'AnswerInput':
        required = {'INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'}
        keys = set(self.force_weights.keys())
        if keys != required:
            raise ValueError(f'force_weights 必须包含且仅包含 {required}')
        for k, v in self.force_weights.items():
            if not isinstance(v, int) or v < 0:
                raise ValueError(f'{k} 必须为非负整数')
        if sum(self.force_weights.values()) != 10:
            raise ValueError('force_weights 五项之和必须等于 10')
        return self


class CognitiveQuestionCreateReq(BaseModel):
    description: str | None = Field(default=None, max_length=200)
    stem: str = Field(..., min_length=1, max_length=800)
    image_url: str | None = None
    answers: list[AnswerInput] = Field(..., min_length=2, max_length=8)
    reference_time_sec: int = Field(default=90, ge=30, le=600)


class CognitiveQuestionUpdateReq(BaseModel):
    description: str | None = Field(default=None, max_length=200)
    stem: str | None = Field(default=None, min_length=1, max_length=800)
    image_url: str | None = None
    answers: list[AnswerInput] | None = Field(default=None, min_length=2, max_length=8)
    reference_time_sec: int | None = Field(default=None, ge=30, le=600)


class StatusChangeReq(BaseModel):
    status: str = Field(..., pattern=r'^(published|archived)$')


# ── 响应体 ────────────────────────────────────────────────────

class CognitiveQuestionItem(BaseModel):
    id: int
    question_no: int
    description: str | None
    stem: str
    image_url: str | None
    answers: list[Any]
    reference_time_sec: int
    status: str
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime


class CognitiveListResp(BaseModel):
    published_count: int
    test_available: bool
    list: list[CognitiveQuestionItem]

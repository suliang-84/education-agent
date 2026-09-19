"""用户管理模块 Pydantic v2 Schemas"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── 学生相关 ──────────────────────────────────────────────────

class StudentListItem(BaseModel):
    id: int
    nickname: str | None
    grade: str | None
    is_minor: bool
    has_five_power_profile: bool
    training_count: int
    bound_parents_count: int
    last_login_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentListResp(BaseModel):
    list: list[StudentListItem]
    total: int
    page: int
    limit: int
    total_pages: int


# ── 家长相关 ──────────────────────────────────────────────────

class BoundStudentItem(BaseModel):
    student_id: int
    nickname: str | None
    grade: str | None
    bind_method: str
    bind_date: datetime


class ParentListItem(BaseModel):
    id: int
    nickname: str | None
    is_confirmed: bool
    bound_students: list[BoundStudentItem]
    last_login_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ParentListResp(BaseModel):
    list: list[ParentListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class UnbindParentReq(BaseModel):
    parent_id: int


class UnbindStudentReq(BaseModel):
    student_id: int


class BindParentReq(BaseModel):
    parent_phone: str = Field(..., pattern=r'^\d{11}$')


class BindParentResp(BaseModel):
    binding_id: int
    parent_id: int
    parent_created: bool


# ── 管理员相关 ────────────────────────────────────────────────

class AdminUserListItem(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    is_active: int
    last_login_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdminUserListResp(BaseModel):
    list: list[AdminUserListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class CreateAdminReq(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    display_name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., pattern=r'^\d{11}$')
    email: str | None = None
    password: str = Field(..., min_length=1)
    role: str = Field(default="ADMIN", pattern=r'^(SUPER_ADMIN|ADMIN)$')


class CreateAdminResp(BaseModel):
    id: int
    username: str
    initial_password: str


class SetAdminStatusReq(BaseModel):
    is_active: int = Field(..., ge=0, le=1)


class ResetPasswordResp(BaseModel):
    new_password: str


# ── AI 提示词摘要相关 ─────────────────────────────────────────

class LearningSummaryInfo(BaseModel):
    content: str | None
    version: int
    updated_at: datetime | None


class PersonalInsightInfo(BaseModel):
    content: str | None
    updated_at: datetime | None
    updated_by: str | None


class InsightEntry(BaseModel):
    id: int
    content: str
    insight_type: str
    source: str
    is_sensitive: bool
    weight: float
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AiPromptSummaryResp(BaseModel):
    student_id: int
    nickname: str | None
    is_enabled: bool
    learning_summary: LearningSummaryInfo
    personal_insight: PersonalInsightInfo
    insights: list[InsightEntry]


class UpdatePersonalInsightReq(BaseModel):
    personal_insight: str = Field(..., min_length=1, max_length=2000)


class AddInsightEntryReq(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    insight_type: str = Field(default='other')
    is_sensitive: bool = False


class RegenerateSummaryResp(BaseModel):
    learning_summary: str
    version: int
    updated_at: datetime


# ── 知识点统计相关 ────────────────────────────────────────────

class KpStatItem(BaseModel):
    kp_id: int
    kp_name: str
    chapter_name: str | None
    total_attempts: int
    error_count: int | None
    error_rate: float | None
    is_stat_valid: bool
    last_practiced_at: datetime | None


class SubjectKpStats(BaseModel):
    subject_code: str
    subject_name: str
    knowledge_points: list[KpStatItem]


class KpStatsResp(BaseModel):
    student_id: int
    nickname: str | None
    grade: str | None
    semester: str | None
    stat_summary: dict
    subjects: list[SubjectKpStats]

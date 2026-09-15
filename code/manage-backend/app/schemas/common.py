from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PageResp(BaseModel, Generic[T]):
    """游标分页响应结构"""
    list: list[T]
    total: int
    has_more: bool
    next_cursor: int | None = None


class PageParams(BaseModel):
    """游标分页查询参数"""
    limit: int = 20
    before_id: int | None = None

    model_config = ConfigDict(extra="ignore")

from pydantic import BaseModel, ConfigDict, Field


class PageResp[T](BaseModel):
    """页码分页响应结构"""

    list: list[T]
    total: int
    page: int
    limit: int
    total_pages: int


class PageParams(BaseModel):
    """页码分页查询参数"""

    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    model_config = ConfigDict(extra="ignore")

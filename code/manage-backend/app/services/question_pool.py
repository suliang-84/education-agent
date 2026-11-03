"""训练抽取池的查询条件（小程序出题 / 知识点页统计共用，保证两处口径一致）"""
from sqlalchemy import or_

from app.models.question import Question


def pool_filters() -> list:
    """抽取池 = 后台「训练题管理」页里状态为「已启用」的题。
    该页只展示已发布（published）的题，启用 / 停用（is_active）只对它们有意义；
    草稿、待审核等未发布的题虽然 is_active 默认是 true，但不在该页出现，不能抽给学生。"""
    return [
        Question.status == "published",
        Question.is_active == True,  # noqa: E712
        Question.deleted_at == None,  # noqa: E711
    ]


def kp_overlap(kp_ids: list[int]):
    """题目的 knowledge_point_ids（JSONB 数组，元素为整数）与 kp_ids 有交集。
    JSONB 的 ?| 只匹配字符串元素，对整数无效，所以逐个用 @> 包含判断再 OR；空列表恒不匹配。"""
    if not kp_ids:
        return Question.id == None  # noqa: E711
    return or_(*[Question.knowledge_point_ids.contains([k]) for k in kp_ids])

"""训练抽取池的查询条件（小程序出题 / 知识点页统计共用，保证两处口径一致）"""
from sqlalchemy import or_

from app.models.question import Question


def pool_filters() -> list:
    """后台「启用」的题目即进入抽取池；与发布状态独立，已删除、已归档的不抽"""
    return [
        Question.is_active == True,  # noqa: E712
        Question.deleted_at == None,  # noqa: E711
        Question.status != "archived",
    ]


def kp_overlap(kp_ids: list[int]):
    """题目的 knowledge_point_ids（JSONB 数组，元素为整数）与 kp_ids 有交集。
    JSONB 的 ?| 只匹配字符串元素，对整数无效，所以逐个用 @> 包含判断再 OR；空列表恒不匹配。"""
    if not kp_ids:
        return Question.id == None  # noqa: E711
    return or_(*[Question.knowledge_point_ids.contains([k]) for k in kp_ids])

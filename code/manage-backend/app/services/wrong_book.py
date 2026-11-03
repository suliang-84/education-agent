"""错题集（待攻克 / 已攻克）：状态规则与「待攻克 / 已攻克 → 单元 → 知识点」统计树

状态：review_status = 'unreview' 为待攻克（历史遗留的 reviewing / pending_consolidation 视同待攻克），
      'aha_achieved' 为已攻克。同一学生同一道题只有一条记录（合并去重）。

归类规则：
- 任何训练里答错 → 待攻克（已攻克的退回待攻克；没有记录则新建）
- 只有在错题集训练（ERROR_QUESTIONS）里答对一道待攻克的题 → 已攻克；其它训练里答对不改变状态
"""
from typing import Iterable

PENDING = "unreview"
MASTERED = "aha_achieved"
PENDING_STATUSES = ("unreview", "reviewing", "pending_consolidation")
MASTERED_STATUSES = (MASTERED,)


def next_status(current: str | None, is_correct: bool, dimension: str | None) -> str | None:
    """答题后错题记录应变成的状态；返回 None 表示不需要改动。current 为 None 表示还没有记录"""
    if not is_correct:
        return PENDING
    if dimension == "ERROR_QUESTIONS" and current in PENDING_STATUSES:
        return MASTERED
    return None


def build_tree(
    chapters: Iterable[tuple[int, str]],
    kps: Iterable[tuple[int, str, int]],
    questions: Iterable[tuple[int, list[int]]],
) -> dict:
    """统计树。chapters = [(章节id, 名称)]；kps = [(知识点id, 名称, 章节id)]；questions = [(题目id, [知识点id])]。
    题目只统计落在这些知识点里的；一道题属于多个知识点时，在每个知识点下各算一次，章节和总数按题目去重。"""
    kps = list(kps)
    kp_chapter = {k[0]: k[2] for k in kps}
    kp_qids: dict[int, set[int]] = {k[0]: set() for k in kps}
    ch_qids: dict[int, set[int]] = {c[0]: set() for c in chapters}
    all_qids: set[int] = set()
    for qid, ids in questions:
        for kid in set(ids or []):
            if kid in kp_chapter:
                kp_qids[kid].add(qid)
                ch_qids[kp_chapter[kid]].add(qid)
                all_qids.add(qid)
    return {
        "count": len(all_qids),
        "chapters": [
            {
                "id": cid,
                "name": name,
                "count": len(ch_qids[cid]),
                "points": [
                    {"id": kid, "name": kname, "count": len(kp_qids[kid])}
                    for kid, kname, kch in kps if kch == cid
                ],
            }
            for cid, name in chapters
        ],
    }

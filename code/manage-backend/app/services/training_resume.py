"""训练中断恢复：把客户端保存的快照与数据库里真实的作答记录对齐（纯函数，便于单元测试）

背景：中断记录只在学生点「退出并保存」时才写入。如果学生从中断记录恢复后继续作答，又没有再正常退出
（直接关掉小程序），中断记录里的 answers_snapshot 就是过期的——数据库里这些题已经答过，快照里却显示未答，
恢复后学生会对已答过的题再提交一次。恢复时以数据库为准，把快照补全即可。
"""


def merge_answers_snapshot(snapshot: list[dict] | None, records: list) -> list[dict]:
    """以数据库的答题记录为准补全 / 覆盖快照。

    snapshot : 客户端保存的 [{question_index, student_answer, is_correct}, ...]
    records  : 该会话的 TrainingAnswerRecord（需要 question_index / student_answer / is_correct 属性）
    返回按 question_index 升序排列的列表。
    """
    merged: dict[int, dict] = {int(a["question_index"]): dict(a) for a in (snapshot or [])}
    for r in records:
        merged[int(r.question_index)] = {
            "question_index": int(r.question_index),
            "student_answer": r.student_answer or "",
            "is_correct": bool(r.is_correct),
        }
    return [merged[k] for k in sorted(merged)]


def resume_index(stored_index: int, answered: set[int], total: int) -> int:
    """恢复后应当停在哪一题：保存时所在的题如果已经答过，就顺延到下一道没答的题；全部答完则停在最后一题（只读查看）"""
    if total <= 0:
        return 0
    idx = max(0, min(stored_index, total - 1))
    while idx in answered and idx < total - 1:
        idx += 1
    return idx

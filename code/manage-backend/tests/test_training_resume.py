"""训练中断恢复：快照与数据库对齐"""
from types import SimpleNamespace as N

from app.services.training_resume import merge_answers_snapshot, resume_index


def rec(i, ans, ok): return N(question_index=i, student_answer=ans, is_correct=ok)


def test_merge_fills_answers_missing_from_stale_snapshot():
    # 过期快照：一题都没答；数据库里第 0 题已经答过
    out = merge_answers_snapshot([], [rec(0, None, False)])
    assert out == [{"question_index": 0, "student_answer": "", "is_correct": False}]


def test_merge_db_wins_and_keeps_snapshot_only_items():
    snap = [{"question_index": 1, "student_answer": "B", "is_correct": True},
            {"question_index": 0, "student_answer": "旧", "is_correct": False}]
    out = merge_answers_snapshot(snap, [rec(0, "新", True), rec(2, "C", False)])
    assert [a["question_index"] for a in out] == [0, 1, 2]        # 升序
    assert out[0] == {"question_index": 0, "student_answer": "新", "is_correct": True}   # 数据库为准
    assert out[1]["student_answer"] == "B"                        # 只在快照里的保留
    assert out[2]["is_correct"] is False


def test_merge_handles_none_snapshot():
    assert merge_answers_snapshot(None, []) == []


def test_resume_index_skips_answered():
    assert resume_index(0, set(), 5) == 0
    assert resume_index(0, {0}, 5) == 1                 # 当前题已答 → 顺延
    assert resume_index(0, {0, 1, 2}, 5) == 3
    assert resume_index(2, {0, 1}, 5) == 2              # 当前题没答 → 不动
    assert resume_index(0, {0, 1, 2, 3, 4}, 5) == 4     # 全答完 → 停在最后一题（只读查看）
    assert resume_index(9, set(), 5) == 4               # 越界保护
    assert resume_index(0, set(), 0) == 0

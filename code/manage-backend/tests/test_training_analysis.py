"""训练答题「智能解答」：提示词拼装（纯函数）"""
from types import SimpleNamespace as N

from app.services.training_analysis import build_user_content, format_standard_answer


def test_format_standard_answer_by_type():
    assert format_standard_answer("SINGLE_CHOICE", {"correct": "C"}) == "选项 C"
    assert format_standard_answer("MULTIPLE_CHOICE", {"correct": ["A", "C", "D"]}) == "选项 A、C、D"
    assert format_standard_answer("TRUE_FALSE", {"correct": True}) == "对"
    assert format_standard_answer("TRUE_FALSE", {"correct": False}) == "错"
    assert format_standard_answer("FILL_BLANK", {"correct": ["55", "145"]}) == "第1空：55；第2空：145"
    out = format_standard_answer("APPLICATION", {"final_answer": "60°和120°", "key_steps": ["设小角为x", "x+2x=180°"]})
    assert "最终答案：60°和120°" in out and "1. 设小角为x" in out and "2. x+2x=180°" in out
    assert "未提供" in format_standard_answer("SINGLE_CHOICE", None)
    # 缺 question_type 时回退到 answer.type
    assert format_standard_answer(None, {"type": "single_choice", "correct": "B"}) == "选项 B"


def test_build_user_content_choice_splits_options_and_marks_wrong():
    q = N(question_type="SINGLE_CHOICE", answer={"type": "SINGLE_CHOICE", "correct": "C"},
          stem="下列说法正确的是（ ）\nA. 甲\nB. 乙\nC. 丙\nD. 丁", solution="丙正确。", common_error="选了甲")
    text = build_user_content(q, "B", False)
    assert "【题型】单选题" in text
    assert "【题目】下列说法正确的是（ ）" in text           # 题干里不再重复选项
    assert "A. 甲" in text and "D. 丁" in text               # 选项单独列出
    assert "【标准答案】选项 C" in text
    assert "【参考解析】丙正确。" in text and "【常见错误】选了甲" in text
    assert "【学生作答】B" in text and "【判题结果】错误" in text


def test_build_user_content_unanswered_and_correct():
    q = N(question_type="TRUE_FALSE", answer={"correct": True}, stem="同角的补角相等。（ ）", solution=None, common_error=None)
    text = build_user_content(q, None, False)
    assert "【学生作答】（未作答）" in text and "【判题结果】错误" in text
    assert "【参考解析】" not in text and "【常见错误】" not in text   # 没有的字段不出现
    assert "【判题结果】正确" in build_user_content(q, "对", True)

"""训练答题：题干选项拆分 + 判题规则（纯函数单元测试）"""
from types import SimpleNamespace as N

import pytest

from app.services.answer_judge import (
    blank_count_of, judge_answer, normalize_answer, question_type_of, split_stem_options,
)


# ── 题干 / 选项拆分 ───────────────────────────────────────────────────────
def test_split_options_one_per_line():
    stem = "下列说法正确的是（ ）\nA. 两个锐角的和一定是锐角\nB. 一个角的补角一定是钝角\nC. 互余的两角一定都是锐角\nD. 钝角的余角是负角"
    s, o = split_stem_options(stem)
    assert s == "下列说法正确的是（ ）"
    assert [x["key"] for x in o] == ["A", "B", "C", "D"]
    assert o[2]["text"] == "互余的两角一定都是锐角"


def test_split_options_same_line_fullwidth_space():
    stem = "下列用科学记数法表示正确的是（ ）\nA. 0.36×10³　B. 36×10²　C. 3.6×10³　D. 3.6×10⁰"
    s, o = split_stem_options(stem)
    assert s == "下列用科学记数法表示正确的是（ ）"
    assert [x["text"] for x in o] == ["0.36×10³", "36×10²", "3.6×10³", "3.6×10⁰"]


@pytest.mark.parametrize("stem", [
    "一个数不是正数就是负数。（ ）",              # 判断题，没有选项
    "点A. 在直线上",                              # 只有一个 A，不构成选项序列
    "A. 只有一项\n没有 B 项",                     # 至少要 A、B 两项
    "",
])
def test_split_options_not_options(stem):
    s, o = split_stem_options(stem)
    assert o is None and s == stem


def test_split_options_empty_option_text_falls_back():
    stem = "题干\nA.\nB. 有内容"
    s, o = split_stem_options(stem)
    assert o is None and s == stem


# ── 标准化 ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw,expected", [
    ("1.4x10^9", "1.4×10⁹"),
    ("1.4X10^9", "1.4×10⁹"),
    ("1.4*10^9", "1.4×10⁹"),
    ("1.4×10⁹", "1.4×10⁹"),
    ("10^-3", "10⁻³"),
    ("  1 . 4 × 10⁹ ", "1.4×10⁹"),
    ("2x+1", "2x+1"),            # 字母变量不受影响
    ("（x+1）", "(x+1)"),
])
def test_normalize(raw, expected):
    assert normalize_answer(raw) == expected


# ── 单选 / 多选 / 判断 ─────────────────────────────────────────────────────
def test_single_choice():
    a = {"type": "SINGLE_CHOICE", "correct": "C"}
    assert judge_answer(a, "SINGLE_CHOICE", "c")
    assert not judge_answer(a, "SINGLE_CHOICE", "B")
    assert not judge_answer(a, "SINGLE_CHOICE", None)
    assert not judge_answer(a, "SINGLE_CHOICE", "")


def test_multiple_choice_order_and_separator_free():
    a = {"type": "MULTIPLE_CHOICE", "correct": ["C", "D"]}
    for ok in ("CD", "DC", "C,D", "c d"):
        assert judge_answer(a, "MULTIPLE_CHOICE", ok)
    for bad in ("C", "CDA", "AB"):
        assert not judge_answer(a, "MULTIPLE_CHOICE", bad)


def test_true_false():
    assert judge_answer({"correct": False}, "TRUE_FALSE", "错")
    assert judge_answer({"correct": False}, "TRUE_FALSE", "×")
    assert not judge_answer({"correct": False}, "TRUE_FALSE", "对")
    assert judge_answer({"correct": True}, "TRUE_FALSE", "对")
    assert judge_answer({"correct": True}, "TRUE_FALSE", "√")


# ── 填空 ───────────────────────────────────────────────────────────────────
def test_fill_blank_single_with_math_variants():
    a = {"type": "FILL_BLANK", "correct": ["1.4×10⁹"]}
    for ok in ("1.4×10⁹", "1.4x10^9", "1.4*10^9", " 1.4 × 10⁹ "):
        assert judge_answer(a, "FILL_BLANK", ok)
    assert not judge_answer(a, "FILL_BLANK", "14×10⁸")


def test_fill_blank_multi_by_text_split():
    a = {"type": "FILL_BLANK", "correct": ["55", "145"]}
    assert judge_answer(a, "FILL_BLANK", "55，145")
    assert judge_answer(a, "FILL_BLANK", "55;145")
    assert not judge_answer(a, "FILL_BLANK", "145,55")   # 必须按顺序


def test_fill_blank_by_list_not_split_on_commas():
    # 答案本身带逗号：按文本拆会被误拆，按列表逐空比对则正确
    a = {"type": "FILL_BLANK", "correct": ["1,000", "(1,2)"]}
    assert judge_answer(a, "FILL_BLANK", None, student_answers=["1,000", "(1,2)"])
    assert not judge_answer(a, "FILL_BLANK", None, student_answers=["1,000"])          # 少一个空
    assert not judge_answer(a, "FILL_BLANK", None, student_answers=["(1,2)", "1,000"])  # 顺序错


def test_fill_blank_empty_list_is_wrong():
    a = {"type": "FILL_BLANK", "correct": ["55", "145"]}
    assert not judge_answer(a, "FILL_BLANK", None, student_answers=["", ""])


# ── 应用题 ─────────────────────────────────────────────────────────────────
def test_application_uses_final_answer_only():
    a = {"type": "APPLICATION", "final_answer": "共35人，总价10600元"}
    # 只看最终答案栏：过程里再多数字也不算
    assert judge_answer(a, "APPLICATION", "过程里写了35和10600", final_answer="35人，10600元")
    assert judge_answer(a, "APPLICATION", "x", final_answer="10,600元，35人")      # 千分位
    assert not judge_answer(a, "APPLICATION", "过程里写了35和10600", final_answer="")  # 最终答案栏为空
    assert not judge_answer(a, "APPLICATION", "过程里写了35和10600", final_answer="35人")


def test_application_fallback_to_whole_text_when_no_final_field():
    a = {"type": "APPLICATION", "final_answer": "共35人，总价10600元"}
    assert judge_answer(a, "APPLICATION", "答：35人，10600元")
    assert not judge_answer(a, "APPLICATION", "答：35人")


# ── 通用边界 ───────────────────────────────────────────────────────────────
def test_no_answer_or_unknown_type_is_wrong():
    assert not judge_answer(None, "SINGLE_CHOICE", "A")
    assert not judge_answer({"correct": "A"}, "SHORT_ANSWER", "A")   # 简答题暂不支持自动判题 → 判错
    assert not judge_answer({"correct": "A"}, None, "A")


def test_type_and_blank_count_helpers():
    q = N(question_type="fill_blank", answer={"correct": ["3", "5"]})
    assert question_type_of(q) == "FILL_BLANK" and blank_count_of(q) == 2
    q = N(question_type=None, answer={"type": "single_choice", "correct": "B"})
    assert question_type_of(q) == "SINGLE_CHOICE" and blank_count_of(q) is None
    q = N(question_type="FILL_BLANK", answer=None)
    assert blank_count_of(q) is None

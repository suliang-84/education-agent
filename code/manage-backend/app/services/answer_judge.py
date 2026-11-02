"""小程序训练答题：题干选项拆分 + 答案判题（纯函数，不依赖数据库，便于单元测试）

判题只在服务端做，标准答案不下发给客户端。
"""
import re

# ── 题型 ─────────────────────────────────────────────────────────────────
SINGLE_CHOICE = "SINGLE_CHOICE"
MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
TRUE_FALSE = "TRUE_FALSE"
FILL_BLANK = "FILL_BLANK"
APPLICATION = "APPLICATION"


def question_type_of(q) -> str | None:
    """题型：优先用 question_type 字段，缺失时回退到 answer 里自带的 type"""
    t = q.question_type or (q.answer or {}).get("type")
    return str(t).upper() if t else None


def blank_count_of(q) -> int | None:
    """填空题的空数（从标准答案数组长度得出，只下发数量，不下发答案内容）"""
    if question_type_of(q) != FILL_BLANK:
        return None
    correct = (q.answer or {}).get("correct")
    return len(correct) if isinstance(correct, list) else None


# ── 题干 / 选项拆分 ───────────────────────────────────────────────────────
# 题库里选项直接写在题干文本中，两种常见排版：
#   每项一行：   "下列说法正确的是（ ）\nA. xxx\nB. xxx\nC. xxx\nD. xxx"
#   同行排列：   "下列……（ ）\nA. xxx　B. xxx　C. xxx　D. xxx"（项间用全角空格或空格分隔）
# 选项标记 = 行首或空白之后的「大写字母 + . / ． / 、 / : / ：」，且字母必须从 A 开始依次递增（至少 A、B 两项）
_OPTION_MARK = re.compile(r"(?m)(?:^|(?<=[\s　]))([A-H])[\.．、:：]\s*")
_STRIP = " \t\r\n　"


def split_stem_options(stem: str) -> tuple[str, list[dict] | None]:
    """把题干拆成「纯题干 + 选项列表」。拆不出来（格式不规整）时返回 (原题干, None)，前端退回文本框作答。"""
    if not stem:
        return stem, None
    marks = list(_OPTION_MARK.finditer(stem))
    seq: list[re.Match] = []
    for i, m in enumerate(marks):
        if m.group(1) != "A":
            continue
        seq = [m]
        for nxt in marks[i + 1:]:
            if nxt.group(1) == chr(ord("A") + len(seq)):
                seq.append(nxt)
        if len(seq) >= 2:
            break
    if len(seq) < 2:
        return stem, None

    options: list[dict] = []
    for j, m in enumerate(seq):
        end = seq[j + 1].start() if j + 1 < len(seq) else len(stem)
        text = stem[m.end():end].strip(_STRIP)
        if not text:
            return stem, None
        options.append({"key": m.group(1), "text": text})
    pure_stem = stem[:seq[0].start()].rstrip(_STRIP)
    if not pure_stem:
        return stem, None
    return pure_stem, options


# ── 答案标准化 ─────────────────────────────────────────────────────────────
_SUP = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")
_SUP_CHARS = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def normalize_answer(s: str) -> str:
    """去除所有空白、统一全半角和常见数学写法、转小写。
    学生在手机上很难输入上标和 ×，所以把常见替代写法统一成题库里的写法：
      1.4x10^9 / 1.4*10^9 / 1.4×10^9  →  1.4×10⁹
      全角括号 / 减号 → 半角；中文逗号 / 句号 → 英文
    标准答案也走同一个函数，所以两边写法一致即可判对。
    """
    s = s.strip().lower()
    s = (s.replace("，", ",").replace("。", ".")
          .replace("（", "(").replace("）", ")")
          .replace("－", "-").replace("−", "-"))
    s = re.sub(r"\s+", "", s)                                   # 含制表符 / 全角空格
    s = re.sub(r"\^\(?([+-]?\d+)\)?", lambda m: m.group(1).translate(_SUP), s)   # ^9 → ⁹
    # 数字 / 上标 / 右括号 与 数字 / 左括号 之间的 x * · 视为乘号（字母变量如 2x+1 不受影响）
    s = re.sub(rf"(?<=[\d{_SUP_CHARS})\.])[x*·](?=[\d(])", "×", s)
    return s


def _numbers_text(s: str) -> str:
    """去掉千分位逗号（10,600 → 10600），便于数字比对"""
    return re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", s)


# ── 判题 ─────────────────────────────────────────────────────────────────
def judge_answer(
    answer: dict | None,
    question_type: str | None,
    student_answer: str | None,
    student_answers: list[str] | None = None,
    final_answer: str | None = None,
) -> bool:
    """按题型比对答案，无法判断时返回 False。

    student_answer   ：整段作答文本（单选 'C'、多选 'CD'、判断 '对'、填空 / 应用题的展示文本）
    student_answers  ：填空题按空分别作答的列表，传了就按列表逐空比对（避免答案里本身带逗号时被误拆）
    final_answer     ：应用题的「最终答案」一栏，传了就只用它来比对数字（不再从整段过程里凑数字）
    """
    if not answer:
        return False
    qtype = (question_type or answer.get("type", "")).upper()

    # 填空题允许只传 student_answers
    if qtype == FILL_BLANK and student_answers is not None:
        correct_list = [normalize_answer(str(c)) for c in answer.get("correct", [])]
        return [normalize_answer(p) for p in student_answers] == correct_list

    # 应用题允许只传 final_answer（未传过程文本时 student_answer 可能为空）
    if qtype == APPLICATION and final_answer is not None:
        return _judge_application(answer, final_answer)

    if not student_answer:
        return False
    sa = normalize_answer(student_answer)

    if qtype == SINGLE_CHOICE:
        correct = str(answer.get("correct", "")).upper()
        return sa.upper() == correct

    if qtype == MULTIPLE_CHOICE:
        correct = set(str(c).upper() for c in answer.get("correct", []))
        submitted = set(re.findall(r"[A-Da-d]", student_answer.upper()))
        return submitted == correct

    if qtype == TRUE_FALSE:
        correct = answer.get("correct", None)
        true_vals = {"true", "对", "正确", "√", "yes", "1"}
        false_vals = {"false", "错", "错误", "×", "no", "0"}
        if correct is True:
            return sa in true_vals
        if correct is False:
            return sa in false_vals
        return False

    if qtype == FILL_BLANK:
        correct_list = [normalize_answer(str(c)) for c in answer.get("correct", [])]
        # 单空直接比；多空按逗号 / 分号拆分
        if len(correct_list) == 1:
            return sa == correct_list[0]
        parts = [normalize_answer(p) for p in re.split(r"[,;，；]", student_answer)]
        return parts == correct_list

    if qtype == APPLICATION:
        return _judge_application(answer, student_answer)

    return False


def _judge_application(answer: dict, text: str) -> bool:
    """应用题：标准答案 final_answer 里的所有数字都必须出现在作答文本中"""
    final = _numbers_text(normalize_answer(str(answer.get("final_answer", ""))))
    nums = re.findall(r"\d+\.?\d*", final)
    if not nums:
        return False
    target = _numbers_text(normalize_answer(text or ""))
    return all(n in target for n in nums)

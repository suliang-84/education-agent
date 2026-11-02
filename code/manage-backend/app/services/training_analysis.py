"""训练答题「智能解答」：按需调用大模型生成参考解析

触发时机：学生在答题页点击「智能解答」按钮时才调用（不再是答错后立即触发）。
"""
import asyncio

from app.services.answer_judge import (
    APPLICATION, FILL_BLANK, MULTIPLE_CHOICE, SINGLE_CHOICE, TRUE_FALSE,
    question_type_of, split_stem_options,
)

# 大模型调用的整体超时（秒）：要小于小程序端请求超时（90 秒），超时后降级为静态解析，不让前端一直等
LLM_TIMEOUT_SEC = 75

TYPE_LABELS = {
    SINGLE_CHOICE: "单选题",
    MULTIPLE_CHOICE: "多选题",
    TRUE_FALSE: "判断题",
    FILL_BLANK: "填空题",
    APPLICATION: "应用题",
}

SYSTEM_PROMPT = """你是 MESH 数理化 AI 助教，面向初高中学生。请根据题目、标准答案和学生的作答，写一份简洁、易懂的「参考解析」。

写作要求：
1. 只用纯文本，不要使用 Markdown 符号（不要 #、*、```、表格）；需要分点时用「1.」「2.」，小标题用【】括起来，段落之间空一行。
2. 按下面的结构写，没有内容的部分可以省略：
   【正确答案】直接给出答案。
   【解题思路】分步骤讲清楚怎么想、怎么算，关键公式或定义要点明。
   【你的作答】学生答错时，指出错在哪一步、为什么会错，语气鼓励；学生答对时，用一句话肯定，并补充一个更好的思路或易错点。
   【小结】一句话提炼本题考查的方法，方便举一反三。
3. 总字数控制在 400 字以内，语言口语化，不要重复题目原文。
4. 如果提供了「参考解析」，以它为依据，不要与标准答案矛盾；不要编造题目里没有的条件。"""


def format_standard_answer(question_type: str | None, answer: dict | None) -> str:
    """把题库里的结构化标准答案转成给大模型看的文字"""
    if not answer:
        return "（题库未提供标准答案）"
    t = (question_type or answer.get("type") or "").upper()
    if t == SINGLE_CHOICE:
        return f"选项 {answer.get('correct')}"
    if t == MULTIPLE_CHOICE:
        return "选项 " + "、".join(str(c) for c in answer.get("correct", []))
    if t == TRUE_FALSE:
        return "对" if answer.get("correct") is True else "错"
    if t == FILL_BLANK:
        return "；".join(f"第{i + 1}空：{c}" for i, c in enumerate(answer.get("correct", [])))
    if t == APPLICATION:
        steps = answer.get("key_steps") or []
        final = answer.get("final_answer", "")
        step_text = "".join(f"\n  {i + 1}. {s}" for i, s in enumerate(steps))
        return f"最终答案：{final}" + (f"\n关键步骤：{step_text}" if step_text else "")
    return str(answer)


def build_user_content(q, student_answer: str | None, is_correct: bool | None) -> str:
    """拼装用户消息：题目（含拆分后的选项）、标准答案、参考解析、常见错误、学生作答与对错"""
    qtype = question_type_of(q)
    stem, options = q.stem, None
    if qtype in (SINGLE_CHOICE, MULTIPLE_CHOICE):
        stem, options = split_stem_options(q.stem)

    lines = [f"【题型】{TYPE_LABELS.get(qtype or '', '未知题型')}", f"【题目】{stem}"]
    if options:
        lines.append("【选项】\n" + "\n".join(f"{o['key']}. {o['text']}" for o in options))
    lines.append(f"【标准答案】{format_standard_answer(qtype, q.answer)}")
    if getattr(q, "solution", None):
        lines.append(f"【参考解析】{q.solution}")
    if getattr(q, "common_error", None):
        lines.append(f"【常见错误】{q.common_error}")
    sa = (student_answer or "").strip()
    lines.append(f"【学生作答】{sa if sa else '（未作答）'}")
    verdict = "正确" if is_correct else "错误"
    lines.append(f"【判题结果】{verdict}")
    return "\n".join(lines)


async def generate_analysis(q, student_answer: str | None, is_correct: bool | None) -> str:
    """调用大模型生成参考解析；失败（未配置 / 超时 / 返回为空）时抛异常，由调用方降级"""
    from app.core import llm  # 延迟导入：便于单元测试纯函数时不依赖 httpx 配置

    text = await asyncio.wait_for(
        llm.chat(SYSTEM_PROMPT, build_user_content(q, student_answer, is_correct)),
        timeout=LLM_TIMEOUT_SEC,
    )
    text = (text or "").strip()
    if not text:
        raise RuntimeError("大模型返回内容为空")
    return text

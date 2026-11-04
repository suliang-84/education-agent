"""个人洞察：一段总结概括的文字，描述「这个学生是什么样的人」，给 AI 助教看

闭环：
  聊天（每累积 10 条新消息）→ 大模型把「已有的个人洞察 + 学生最近说的话」更新成一段新的总结
      → 写入 student_ai_prompt_summaries.personal_insight（管理员在摘要页看到的那段文字，可直接修改）
      → AI 助教每次回复前读取这段文字（services/assistant/service.py → core.build_system_prompt）

规则：
- 是一段概括，不是条目列表；内容包括兴趣爱好、学习 / 类比偏好、近期状态、生活事件、家庭情况、学习态度
- 管理员改过的内容会作为「已有洞察」交给大模型，要求保留（除非和聊天里的新信息明显矛盾），所以不会被覆盖掉
- 不存聊天原文，不写姓名 / 号码 / 学校 / 住址；总长度 ≤ 400 字
- 情绪、生活事件、家庭相关的句子前加「【敏感】」，助教只用来调整语气，不会直接向学生提起
"""
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import StudentAiPromptSummary

SENSITIVE_PREFIX = "【敏感】"
MAX_CHARS = 400

INSIGHT_PROMPT = """你是学习分析助手，负责维护一名学生的「个人洞察」：一段总结概括的文字，帮助 AI 学习伙伴之后更贴合地辅导他。
我会给你「已有的个人洞察」（可能为空，也可能包含老师手写的内容）和「学生最近说的话」。请输出更新后的个人洞察。

要求：
1. 只输出这一段文字本身，不要标题、不要编号、不要列表、不要解释。
2. 内容覆盖对辅导有帮助的个人特点：兴趣爱好、学习 / 类比偏好、近期状态、重要生活事件、家庭情况、学习态度。没有信息的方面不用写。
3. 已有洞察里的信息要保留（包括老师手写的），除非学生最近说的话与之明显矛盾；新信息要融合进来，不要简单拼接，也不要重复。
4. 用第三人称、平实的语言概括，一段话，总长不超过 300 字；不要出现学生原话，不要写姓名、手机号、学校、住址等能识别个人的信息。
5. 涉及情绪、家庭、生活事件的句子，句首加「【敏感】」。
6. 学生最近说的话里没有任何值得补充的个人信息时，原样输出已有洞察。"""


def clean_paragraph(text: str | None, max_chars: int = MAX_CHARS) -> str:
    """整理大模型输出：去掉代码块 / 引号 / 多余空行，超长时在句末截断"""
    t = (text or "").strip()
    t = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", t).strip().strip("\"“”")
    t = re.sub(r"^(个人洞察|更新后的个人洞察)[:：]\s*", "", t)
    t = re.sub(r"\n{2,}", "\n", t).strip()
    if len(t) > max_chars:
        cut = t[:max_chars]
        m = max(cut.rfind(c) for c in "。！？；")
        t = cut[: m + 1] if m >= max_chars * 0.5 else cut
    return t


def accept_update(old: str | None, new: str) -> bool:
    """是否采用大模型给出的新洞察：空、没变化、或在已有较长内容时被缩成很短（疑似丢失信息）都不采用，也不含大段号码"""
    old = (old or "").strip()
    if not new or new == old:
        return False
    if re.search(r"\d{6,}", new):
        return False
    if len(old) >= 40 and len(new) < len(old) * 0.4:
        return False
    return True


async def apply_update(db: AsyncSession, student_id: int, new_text: str, source: str = "AI") -> None:
    now = datetime.now(UTC)
    summ = (await db.execute(select(StudentAiPromptSummary).where(StudentAiPromptSummary.student_id == student_id))).scalar_one_or_none()
    if summ is None:
        summ = StudentAiPromptSummary(student_id=student_id)
        db.add(summ)
    summ.personal_insight = new_text
    summ.personal_insight_updated_at = now
    summ.insight_updated_by = source
    await db.flush()

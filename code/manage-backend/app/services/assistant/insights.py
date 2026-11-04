"""个人洞察：一段总结概括的文字，描述「这个学生是什么样的人」，给 AI 助教看

存储：student_ai_prompt_summaries
  - insight_admin_text  管理员确认的部分（管理员在页面上保存的整段文字）——AI 永远不改写
  - insight_ai_text     AI 补充的部分（AI 根据聊天概括出的、管理员文字里还没有的内容）——AI 只改这一块
  - personal_insight    = 管理员部分 + 换行 + AI 部分；页面展示、助教提示词读取的都是它

闭环：
  聊天（退出助教页 / 小程序退到后台 / 累积 10 条消息）
      → 大模型只更新「AI 补充」部分（输入：管理员确认的部分 + 此前的 AI 补充 + 学生最近说的话）
      → 重新拼出 personal_insight
  管理员在摘要页修改并保存 → 保存的整段文字成为新的「管理员确认的部分」，AI 补充清空，之后 AI 只在它后面补充

所以管理员写的 / 保留下来的内容不会被 AI 更新弄丢，这是结构上的保证，不依赖大模型听不听话。
（并发：AI 写入前重新读取最新的管理员部分再拼接，管理员刚保存的内容不会被 AI 用旧数据覆盖。）

规则：不存聊天原文，不写姓名 / 号码 / 学校 / 住址；AI 补充部分 ≤ 200 字；情绪、生活事件、家庭相关的句子前加「【敏感】」，
助教只用来调整语气，不会直接向学生提起。
"""
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import StudentAiPromptSummary

SENSITIVE_PREFIX = "【敏感】"
MAX_CHARS = 700          # 给助教的个人洞察总长上限（管理员部分 + AI 部分）
MAX_AI_CHARS = 200       # AI 补充部分上限

INSIGHT_PROMPT = """你是学习分析助手，负责为一名学生补充「个人洞察」：一段总结概括的文字，帮助 AI 学习伙伴之后更贴合地辅导他。
我会给你三部分：
- 【老师确认的个人洞察】：已经确认的内容，你不能改动、也不要重复其中已有的信息；
- 【此前 AI 概括的补充】：你之前补充的内容（可能为空）；
- 【学生最近说的话】。
请输出「更新后的 AI 补充」。

要求：
1. 只输出这一段补充文字本身，不要标题、不要编号、不要列表、不要解释。
2. 只写【老师确认的个人洞察】里还没有的信息：兴趣爱好、学习 / 类比偏好、近期状态、重要生活事件、家庭情况、学习态度。
3. 把此前的补充和学生新说的话融合成一段，不要简单拼接，不要重复；与老师确认的内容有出入时，以老师确认的为准，不要写与之矛盾的内容。
4. 用第三人称、平实的语言概括，一段话，总长不超过 150 字；不要出现学生原话，不要写姓名、手机号、学校、住址等能识别个人的信息。
5. 涉及情绪、家庭、生活事件的句子，句首加「【敏感】」。
6. 学生说的话里没有任何值得补充的新信息、「此前 AI 概括的补充」也不需要改动时，只输出「无变化」三个字，不要输出「（空）」「无」之类的占位文字。"""


# 大模型在「没有新信息」时常输出的占位文字，一律当作空，绝不能写进洞察
_PLACEHOLDER = re.compile(r"^[（(【\[\s]*(无变化|无更新|无新增|无补充|暂无|没有|无|空|none|null|n/a)[）)】\]\s。.]*$", re.I)


def _is_placeholder(t: str) -> bool:
    return not t or bool(_PLACEHOLDER.match(t.strip()))


def clean_paragraph(text: str | None, max_chars: int = MAX_AI_CHARS) -> str:
    """整理大模型输出：去掉代码块 / 引号 / 多余空行，超长时在句末截断"""
    t = (text or "").strip()
    t = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", t).strip().strip("\"“”")
    t = re.sub(r"^(个人洞察|AI 补充|更新后的 AI 补充|更新后的个人洞察)[:：]\s*", "", t)
    t = re.sub(r"\n{2,}", "\n", t).strip()
    if _is_placeholder(t):
        return ""
    if len(t) > max_chars:
        cut = t[:max_chars]
        m = max(cut.rfind(c) for c in "。！？；")
        t = cut[: m + 1] if m >= max_chars * 0.5 else cut
    return t


def accept_update(old_ai: str | None, new_ai: str) -> bool:
    """是否采用大模型给出的新「AI 补充」：没变化、含大段号码都不采用；已有较长补充（≥40 字）被缩得很短（疑似丢信息）也不采用。
    新补充为空：此前也为空才算没变化；此前有内容却输出空，视为丢信息，不采用。"""
    old_ai = (old_ai or "").strip()
    if new_ai == old_ai:
        return False
    if not new_ai:
        return False
    if re.search(r"\d{6,}", new_ai):
        return False
    if len(old_ai) >= 40 and len(new_ai) < len(old_ai) * 0.4:
        return False
    return True


def compose(admin_text: str | None, ai_text: str | None, max_chars: int = MAX_CHARS) -> str:
    """personal_insight = 管理员部分 + 换行 + AI 部分。超长时只截 AI 部分，管理员部分原样保留"""
    a = (admin_text or "").strip()
    b = (ai_text or "").strip()
    if not b:
        return a
    if not a:
        return b[:max_chars]
    room = max_chars - len(a) - 1
    if room <= 0:
        return a
    return a + "\n" + b[:room]


async def load(db: AsyncSession, student_id: int) -> tuple[str, str]:
    """当前的 (管理员确认的部分, AI 补充的部分)；老数据没有拆分字段时，把整段 personal_insight 当作管理员确认的部分"""
    s = (await db.execute(select(StudentAiPromptSummary).where(StudentAiPromptSummary.student_id == student_id))).scalar_one_or_none()
    if s is None:
        return "", ""
    admin = s.insight_admin_text if s.insight_admin_text is not None else (s.personal_insight or "")
    return admin.strip(), (s.insight_ai_text or "").strip()


async def apply_update(db: AsyncSession, student_id: int, new_ai_text: str) -> str:
    """写入新的「AI 补充」。写入前重新读取最新的管理员部分再拼接：管理员刚保存的内容不会被 AI 用旧数据覆盖"""
    now = datetime.now(UTC)
    summ = (await db.execute(select(StudentAiPromptSummary).where(StudentAiPromptSummary.student_id == student_id))).scalar_one_or_none()
    if summ is None:
        summ = StudentAiPromptSummary(student_id=student_id)
        db.add(summ)
    admin = (summ.insight_admin_text if summ.insight_admin_text is not None else (summ.personal_insight or "")).strip()
    summ.insight_admin_text = admin
    summ.insight_ai_text = new_ai_text
    summ.personal_insight = compose(admin, new_ai_text)
    summ.personal_insight_updated_at = now
    summ.insight_updated_by = "AI"
    await db.flush()
    return summ.personal_insight

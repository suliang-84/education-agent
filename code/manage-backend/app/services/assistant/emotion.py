"""对话情绪判断：每次对话摘要更新时，让大模型根据学生最近说的话判断一次情绪状态。

用途：学生画像预警「聊天出现负面情绪」读取这里的判断记录（student_ai_prompt_summaries.emotion_history）。
只存判断等级和一句依据，不存聊天原文；判断失败不影响摘要和洞察的更新，也不会改动已有记录。
"""
import json
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.models.ai import StudentAiPromptSummary

LEVELS = ["normal", "mild", "significant", "urgent"]
LEVEL_LABELS = {"normal": "正常", "mild": "轻度低落", "significant": "明显低落", "urgent": "需要重点关注"}
LEVEL_RANK = {k: i for i, k in enumerate(LEVELS)}
KEEP = 10
MAX_REASON = 60

EMOTION_PROMPT = """你是学校里细心的心理观察员，要根据一名初高中学生对 AI 学习助教说的话，判断他最近的情绪状态。
我只给你学生自己说的话。请输出 JSON，不要任何其他文字：
{"level": "normal|mild|significant|urgent", "reason": "一句话依据"}

等级含义：
- normal：正常。包括对作业多、题目难、考试紧张的普通抱怨（如「作业好多好烦」「这题好难」），这些不算情绪问题；
- mild：轻度低落或烦躁，有一些负面情绪，但没有持续、严重的迹象；
- significant：明显低落，如反复表达难过、压抑、没有动力、孤独、被排挤、对自己很失望，已经影响学习和生活；
- urgent：出现绝望、不想活、伤害自己或他人等表达，需要立刻有人关心。

要求：
1. 只有话里有明确信号才判为 mild 及以上；信息不足或只是闲聊时判 normal，不要过度解读。
2. reason 不超过 40 个字，用第三人称概括依据，不要引用学生原话，不要出现姓名、学校、住址等能识别个人的信息。
3. 只输出 JSON。"""


def parse(text: str | None) -> dict | None:
    """从大模型输出里取出 {level, reason}；格式不对返回 None"""
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        d = json.loads(m.group())
    except (ValueError, TypeError):
        return None
    level = str(d.get("level", "")).strip().lower()
    if level not in LEVEL_RANK:
        return None
    reason = str(d.get("reason", "")).strip().replace("\n", " ")[:MAX_REASON]
    return {"level": level, "reason": reason}


async def record(db, student_id: int, judgment: dict) -> None:
    """追加一条判断记录（只保留最近 KEEP 条）；调用方负责 commit"""
    summ = (await db.execute(select(StudentAiPromptSummary).where(StudentAiPromptSummary.student_id == student_id))).scalar_one_or_none()
    if summ is None:
        summ = StudentAiPromptSummary(student_id=student_id)
        db.add(summ)
        summ.emotion_history = []
    hist = list(summ.emotion_history or [])
    hist.append({"at": datetime.now(UTC).isoformat(), **judgment})
    summ.emotion_history = hist[-KEEP:]
    flag_modified(summ, "emotion_history")
    await db.flush()

"""智能训练：从 AI 助手聊天里提取「近期困惑的知识点」

- 只看学生最近 14 天说的话（学生消息 + 会话摘要），让大模型把「老师最近讲的某某我不太懂」映射到当前学期的知识点
- 结果缓存到 student_learning_signals（只存知识点 id、置信度、时间和 100 字内的摘要，不存聊天原文）
- 聊天为空 / 没有新消息 / 大模型不可用：直接返回，智能训练照常按其它信号出题，不报错
- 创建训练时不阻塞等待：有缓存就用缓存，有新消息就后台刷新；只有「从没分析过」的第一次才最多等几秒
"""
import asyncio
import json
import re
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.ai import AiChatMessage, AiChatSession
from app.models.knowledge import Chapter, Grade, KnowledgePoint, Semester, Subject
from app.models.student import Student, StudentLearningSignal

CHAT_WINDOW_DAYS = 14
MAX_MESSAGES = 40
FIRST_TIME_WAIT_SEC = 8

SYSTEM_PROMPT = """你是学习分析助手。下面是一名学生最近和 AI 学习助手的对话里，学生自己说的话，以及他当前学期的知识点清单。
请判断学生在哪些知识点上表达了「困惑、不懂、做不对、老师讲了没听懂」之类的学习困难，并把它们对应到清单里的知识点。

要求：
1. 只输出一个 JSON 对象，不要任何解释，格式：
   {"intents":[{"kp_id":知识点编号,"confidence":0到1之间的小数}],"summary":"不超过100字的学习情况摘要"}
2. kp_id 必须来自清单；学生只是闲聊、或没有表达学习困难的，intents 为空数组。
3. confidence：学生明确说不懂 / 不会取 0.8~1.0，隐约提到有困难取 0.4~0.7。
4. summary 用第三人称概括学生最近在学习上遇到的情况和提到的知识点，不要出现学生的原话和隐私信息。"""


def parse_llm_json(text: str) -> dict:
    """从大模型输出里取出 JSON（容忍外面包了代码块或多余文字）"""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("no json")
    return json.loads(m.group(0))


def validate_intents(raw: list, valid_kp_ids: set[int], at: datetime) -> list[dict]:
    """只保留清单里的知识点；置信度限制在 0~1；同一知识点取最大"""
    best: dict[int, float] = {}
    for it in raw or []:
        try:
            kid, conf = int(it["kp_id"]), float(it["confidence"])
        except (KeyError, ValueError, TypeError):
            continue
        if kid in valid_kp_ids and conf > 0:
            best[kid] = max(best.get(kid, 0.0), min(conf, 1.0))
    return [{"kp_id": k, "confidence": round(c, 2), "mentioned_at": at.isoformat()} for k, c in best.items()]


async def _latest_student_message(db: AsyncSession, student_id: int) -> tuple[int, datetime | None]:
    row = (await db.execute(
        select(func.max(AiChatMessage.id), func.max(AiChatMessage.created_at))
        .join(AiChatSession, AiChatSession.id == AiChatMessage.session_id)
        .where(AiChatSession.student_id == student_id, AiChatMessage.role == "student")
    )).one()
    return (row[0] or 0), row[1]


async def refresh(db: AsyncSession, student: Student) -> bool:
    """重新分析聊天并写入缓存；返回是否做了分析。没有聊天 / 没有候选知识点 / 大模型失败时返回 False"""
    now = datetime.now(UTC)
    last_id, last_at = await _latest_student_message(db, student.id)
    if last_id == 0:
        return False   # 聊天为空：没有信号

    msgs = (await db.execute(
        select(AiChatMessage.content, AiChatMessage.created_at)
        .join(AiChatSession, AiChatSession.id == AiChatMessage.session_id)
        .where(AiChatSession.student_id == student.id, AiChatMessage.role == "student",
               AiChatMessage.created_at > now - timedelta(days=CHAT_WINDOW_DAYS))
        .order_by(AiChatMessage.created_at.desc()).limit(MAX_MESSAGES)
    )).all()
    summaries = (await db.execute(
        select(AiChatSession.session_summary).where(
            AiChatSession.student_id == student.id, AiChatSession.session_summary.is_not(None),
            AiChatSession.created_at > now - timedelta(days=CHAT_WINDOW_DAYS),
        ).order_by(AiChatSession.created_at.desc()).limit(5)
    )).scalars().all()
    if not msgs and not summaries:
        return False

    # 候选知识点：学生当前年级学期下所有科目的知识点
    kps = []
    if student.grade and student.semester:
        kps = (await db.execute(
            select(KnowledgePoint.id, KnowledgePoint.name, Chapter.name, Subject.name)
            .join(Chapter, KnowledgePoint.chapter_id == Chapter.id)
            .join(Semester, Chapter.semester_id == Semester.id)
            .join(Grade, Semester.grade_id == Grade.id)
            .join(Subject, Grade.subject_id == Subject.id)
            .where(Grade.code == student.grade, Semester.code == student.semester)
            .order_by(KnowledgePoint.id)
        )).all()

    from app.core import llm   # 延迟导入
    user_content = (
        "【知识点清单】（编号：科目·章节·知识点）\n"
        + "\n".join(f"{k[0]}：{k[3]}·{k[2]}·{k[1]}" for k in kps)
        + "\n\n【学生最近说的话】（新的在前）\n"
        + "\n".join(f"- {m[0][:200]}" for m in msgs)
        + ("\n\n【会话摘要】\n" + "\n".join(f"- {s[:200]}" for s in summaries) if summaries else "")
    )
    try:
        out = parse_llm_json(await asyncio.wait_for(llm.chat(SYSTEM_PROMPT, user_content), timeout=60))
    except Exception as e:   # 未配置 / 超时 / 返回格式不对：智能训练照常出题，只是没有聊天信号
        logger.warning(f"聊天困惑提取失败 student={student.id}: {e}")
        return False

    mentioned_at = (msgs[0][1] if msgs else last_at) or now
    intents = validate_intents(out.get("intents", []), {k[0] for k in kps}, mentioned_at)
    summary = (out.get("summary") or "").strip()[:200] or None

    row = (await db.execute(
        select(StudentLearningSignal).where(StudentLearningSignal.student_id == student.id)
    )).scalar_one_or_none()
    if row is None:
        row = StudentLearningSignal(student_id=student.id)
        db.add(row)
    row.intents = intents
    row.chat_summary = summary
    row.source_message_id = last_id
    row.refreshed_at = now
    await db.commit()

    # 同步更新后台「学生管理 → 摘要 → 学习信息摘要」（失败不影响智能训练）
    try:
        from app.services.users_service import regenerate_learning_summary
        await regenerate_learning_summary(db, student.id)
        await db.commit()
    except Exception as e:
        logger.warning(f"刷新学习信息摘要失败 student={student.id}: {e}")
    return True


async def refresh_in_background(student_id: int) -> None:
    """后台刷新（用独立的数据库会话，不占用请求的连接）；任何异常都只记日志"""
    try:
        async with AsyncSessionLocal() as db:
            student = (await db.execute(select(Student).where(Student.id == student_id))).scalar_one_or_none()
            if student:
                await refresh(db, student)
    except Exception as e:
        logger.warning(f"后台刷新聊天信号失败 student={student_id}: {e}")


async def ensure_fresh(db: AsyncSession, student: Student) -> None:
    """创建智能训练前调用：
    - 聊天为空 → 什么都不做
    - 从没分析过：最多等 FIRST_TIME_WAIT_SEC 秒，让第一次训练就能用上聊天信号
    - 已有缓存但有新消息：后台刷新，本次用旧缓存
    """
    last_id, _ = await _latest_student_message(db, student.id)
    if last_id == 0:
        return
    row = (await db.execute(
        select(StudentLearningSignal).where(StudentLearningSignal.student_id == student.id)
    )).scalar_one_or_none()
    if row is not None and row.source_message_id >= last_id:
        return
    if row is None:
        try:
            await asyncio.wait_for(refresh(db, student), timeout=FIRST_TIME_WAIT_SEC)
        except Exception as e:
            logger.warning(f"首次聊天分析超时 / 失败 student={student.id}: {e}")
            asyncio.create_task(refresh_in_background(student.id))
    else:
        asyncio.create_task(refresh_in_background(student.id))

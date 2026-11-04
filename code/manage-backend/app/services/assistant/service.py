"""AI 助教：数据库与大模型的编排（逻辑规则见 core.py）"""
import asyncio
import base64
import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import AppException
from app.models.ai import (
    AiChatMessage, AiChatSession, AiHeuristicStrategy, AiStrategyEvent, AiStudentStrategyProfile,
    AiTokenUsageLog, StudentAiPromptSummary, SystemConfig,
)
from app.models.knowledge import KnowledgePoint
from app.models.student import FivePowerProfile, Student, StudentLearningSignal
from app.services.assistant import core, insights

UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "uploads"

HISTORY_FOR_LLM = 12      # 带给大模型的最近消息条数
PAGE_SIZE = 30
# 推理型模型的「思考」也占 token，上限给足，避免回复写到一半被截断
LLM_MAX_TOKENS = 2000


# ── 会话 ─────────────────────────────────────────────────────────────────────

async def get_or_create_session(db: AsyncSession, student: Student) -> tuple[AiChatSession, bool]:
    """单一永久会话：有就复用，没有就新建并写入个性化开场白。返回 (会话, 是否新建)"""
    s = (await db.execute(
        select(AiChatSession).where(AiChatSession.student_id == student.id, AiChatSession.session_mode == "free_chat")
        .order_by(AiChatSession.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    created = False
    if s is None:
        now = datetime.now(UTC)
        s = AiChatSession(id=str(uuid.uuid4()), student_id=student.id, session_mode="free_chat", status="active",
                          started_at=now, created_at=now)
        db.add(s)
        await db.flush()
        created = True
    elif s.status != "active":
        s.status = "active"     # 永久会话始终是 active（历史上点过「结束」的会话重新激活）
        s.ended_at = None
    n = (await db.execute(select(func.count()).select_from(AiChatMessage).where(AiChatMessage.session_id == s.id))).scalar_one()
    if n == 0:
        db.add(AiChatMessage(session_id=s.id, role="assistant", content=await opening_text(db, student),
                             created_at=datetime.now(UTC)))
    await db.commit()
    return s, created


async def opening_text(db: AsyncSession, student: Student) -> str:
    """个性化开场白（模板，不调用大模型，进入页面立刻可见）"""
    hint = ""
    try:
        from app.services.smart_training.signals import load_signals
        from app.services.smart_training.core import smoothed_error, merge_params
        sig = await load_signals(db, student, [])
        params = merge_params(None)
        ranked = sorted(((k, smoothed_error(a, e, params["prior"])) for k, (a, e) in sig.kp_stats.items() if a >= 1.5),
                        key=lambda x: -x[1])
        ids = [k for k, r in ranked[:1]] + sorted(sig.intents, key=lambda k: -sig.intents[k])[:1]
        if ids:
            names = dict((await db.execute(select(KnowledgePoint.id, KnowledgePoint.name).where(KnowledgePoint.id.in_(ids)))).all())
            first = next((names[i] for i in ids[::-1] if i in names), None)
            if first:
                hint = f"我注意到你最近在「{first}」上可能有些吃力，想一起看看吗？"
    except Exception as e:
        logger.warning(f"生成开场白依据失败 student={student.id}: {e}")
    return "你好！我是你的 AI 学习伙伴。" + (hint or "有什么数理化问题想聊聊？") + "也可以直接把题目发给我，我们一步步想。"


def _silence(session: AiChatSession, now: datetime, timeout_min: int) -> bool:
    return core.silence_active(session.silence_mode, session.silence_triggered_at, now, timeout_min)


async def _timeout_min(db: AsyncSession) -> int:
    row = (await db.execute(select(SystemConfig.value).where(SystemConfig.key == "chat_silence_timeout_min"))).scalar_one_or_none()
    try:
        return int(row) if row else core.SILENCE_TIMEOUT_MIN
    except ValueError:
        return core.SILENCE_TIMEOUT_MIN


def message_dict(m: AiChatMessage) -> dict:
    return {
        "message_id": m.id,
        "role": m.role,
        "content": m.content,
        "image_url": m.image_url,
        "is_aha_trigger": m.is_aha_trigger,
        "rating": m.student_rating,
        "created_at": m.created_at.isoformat(),
    }


async def get_session_of(db: AsyncSession, student: Student, session_id: str) -> AiChatSession:
    s = (await db.execute(select(AiChatSession).where(AiChatSession.id == session_id, AiChatSession.student_id == student.id))).scalar_one_or_none()
    if not s:
        raise AppException("会话不存在", 404)
    return s


async def page_messages(db: AsyncSession, session_id: str, before_id: int | None, limit: int = PAGE_SIZE) -> tuple[list[dict], bool]:
    """按时间倒着取一页（新的在前），返回时翻成正序；has_more 表示还有更早的"""
    q = select(AiChatMessage).where(AiChatMessage.session_id == session_id, AiChatMessage.role != "system")
    if before_id:
        q = q.where(AiChatMessage.id < before_id)
    rows = (await db.execute(q.order_by(AiChatMessage.id.desc()).limit(limit + 1))).scalars().all()
    has_more = len(rows) > limit
    rows = list(reversed(rows[:limit]))
    return [message_dict(m) for m in rows], has_more


# ── 上下文 ───────────────────────────────────────────────────────────────────

async def _strategies(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(select(AiHeuristicStrategy).where(AiHeuristicStrategy.is_active == True))).scalars().all()  # noqa: E712
    return [{"id": r.strategy_id, "name": r.strategy_name, "description": r.description or "", "example": r.example_phrase,
             "powers": list(r.applicable_powers or []), "priority": r.default_priority} for r in rows]


async def _scores(db: AsyncSession, student_id: int) -> dict[str, float]:
    rows = (await db.execute(select(AiStudentStrategyProfile).where(AiStudentStrategyProfile.student_id == student_id))).scalars().all()
    return {r.strategy_id: float(r.effectiveness_score) for r in rows}


async def _profile_row(db: AsyncSession, student_id: int, strategy_id: str) -> AiStudentStrategyProfile:
    row = (await db.execute(select(AiStudentStrategyProfile).where(
        AiStudentStrategyProfile.student_id == student_id, AiStudentStrategyProfile.strategy_id == strategy_id))).scalar_one_or_none()
    if row is None:
        row = AiStudentStrategyProfile(student_id=student_id, strategy_id=strategy_id, total_uses=0, effective_count=0,
                                       ineffective_count=0, positive_ratings=0, negative_ratings=0, effectiveness_score=50,
                                       updated_at=datetime.now(UTC))
        db.add(row)
        await db.flush()
    return row


def _refresh_score(row: AiStudentStrategyProfile) -> None:
    row.effectiveness_score = core.effectiveness_score(row.positive_ratings, row.negative_ratings, row.effective_count, row.ineffective_count)


async def _state_text(db: AsyncSession, student: Student) -> tuple[str, str, str | None]:
    """(学习状态文字, 个人洞察文字, 最弱的一力)"""
    from app.services.smart_training.signals import learning_state_text
    try:
        state = await learning_state_text(db, student)
    except Exception as e:
        logger.warning(f"组装学习状态失败 student={student.id}: {e}")
        state = ""
    summ = (await db.execute(select(StudentAiPromptSummary).where(StudentAiPromptSummary.student_id == student.id))).scalar_one_or_none()
    insight = (summ.personal_insight or "").strip() if summ else ""
    prof = (await db.execute(select(FivePowerProfile).where(FivePowerProfile.student_id == student.id, FivePowerProfile.is_latest == True))).scalar_one_or_none()  # noqa: E712
    return state[:900], insight[:insights.MAX_CHARS], (prof.primary_weakness if prof else None)


async def _recent_strategies(db: AsyncSession, session_id: str, limit: int = 4) -> list[str]:
    rows = (await db.execute(
        select(AiChatMessage.strategy_id).where(AiChatMessage.session_id == session_id, AiChatMessage.role == "assistant",
                                                AiChatMessage.strategy_id.is_not(None), AiChatMessage.is_aha_trigger == False)  # noqa: E712
        .order_by(AiChatMessage.id.desc()).limit(limit)
    )).scalars().all()
    return list(reversed(rows))


async def _llm(messages: list[dict], max_tokens: int = 700, temperature: float | None = 0.7, has_image: bool = False) -> dict:
    from app.core import llm
    try:
        return await asyncio.wait_for(llm.chat_messages(messages, max_tokens=max_tokens, temperature=temperature), timeout=100 if has_image else 80)   # 含上游繁忙时的自动重试
    except Exception as e:
        logger.warning(f"AI 助教调用大模型失败: {type(e).__name__}: {e}")
        status = getattr(getattr(e, "response", None), "status_code", None)
        if has_image and status in (400, 415, 422):
            # 配置的模型不接受图片输入：明确告诉学生，不假装识别
            raise AppException("当前 AI 模型暂不支持看图，请把题目文字输入后再问我", 503, "ASST-008")
        if status in (429, 502, 503, 504):
            # 大模型服务商那边繁忙（已自动重试 3 次仍失败）：明确告诉学生是对方繁忙，稍后再试即可
            raise AppException("AI 服务现在比较繁忙，请过一会儿再试", 503, "ASST-005")
        raise AppException("AI 暂时无法回复，请稍后重试", 503, "ASST-005")


async def _log_tokens(db: AsyncSession, student_id: int, session_id: str, res: dict) -> None:
    u = res.get("usage") or {}
    if not u.get("total_tokens"):
        return
    db.add(AiTokenUsageLog(student_id=student_id, module="assistant", call_type="chat", provider="deepseek", model=res.get("model") or "",
                           prompt_tokens=u["prompt_tokens"], completion_tokens=u["completion_tokens"], total_tokens=u["total_tokens"],
                           session_id=session_id, created_at=datetime.now(UTC)))


def _image_data_url(path: str) -> str | None:
    """上传的图片读成 data URL 随消息发给大模型（大模型访问不到本机地址）；文件不存在返回 None"""
    f = UPLOAD_ROOT / path.removeprefix("/uploads/")
    try:
        raw = f.read_bytes()
    except OSError:
        return None
    mt = core.sniff_image_type(raw)
    if not mt:
        return None
    return f"data:{mt[0]};base64,{base64.b64encode(raw).decode()}"


def _user_content(text: str, image_path: str | None):
    """学生消息的内容：带图片时是 [图片, 文字] 的多模态格式，文字为空用默认提问"""
    if image_path:
        url = _image_data_url(image_path)
        if url:
            return [{"type": "image_url", "image_url": {"url": url}},
                    {"type": "text", "text": text or core.DEFAULT_IMAGE_QUESTION}]
    return text or core.DEFAULT_IMAGE_QUESTION if image_path else text


def _history_messages(rows: list[AiChatMessage], vision_last: bool = False) -> list[dict]:
    """历史消息给大模型：较早消息里的图片只留「[图片]」标记（省 token）；vision_last 时最后一条学生消息带上图片本身（重新生成用）"""
    rows = [m for m in rows if m.role in ("student", "assistant")]
    out = []
    for i, m in enumerate(rows):
        role = "user" if m.role == "student" else "assistant"
        if m.image_url and vision_last and i == len(rows) - 1 and role == "user":
            out.append({"role": role, "content": _user_content(m.content, m.image_url)})
        else:
            out.append({"role": role, "content": ("[图片] " if m.image_url else "") + m.content})
    return out


async def _history(db: AsyncSession, session_id: str, upto_id: int | None = None) -> list[AiChatMessage]:
    q = select(AiChatMessage).where(AiChatMessage.session_id == session_id, AiChatMessage.role.in_(("student", "assistant")))
    if upto_id:
        q = q.where(AiChatMessage.id <= upto_id)
    rows = (await db.execute(q.order_by(AiChatMessage.id.desc()).limit(HISTORY_FOR_LLM))).scalars().all()
    return list(reversed(rows))


# ── 发送消息 ─────────────────────────────────────────────────────────────────

async def send_message(db: AsyncSession, student: Student, session: AiChatSession, content: str, image_url: str | None = None) -> dict:
    content = (content or "").strip()
    if image_url and not (core.valid_image_path(image_url) and (UPLOAD_ROOT / image_url.removeprefix("/uploads/")).is_file()):
        raise AppException("图片已失效，请重新上传", 400, "ASST-006")
    if not content and not image_url:
        raise AppException("请输入想问的问题", 400, "ASST-004")
    if len(content) > core.MAX_INPUT_CHARS:
        raise AppException(f"消息不能超过 {core.MAX_INPUT_CHARS} 字", 400, "ASST-003")
    if core.is_blocked(content):
        raise AppException("该内容无法回复，换个方式试试？", 400, "ASST-002")

    now = datetime.now(UTC)
    timeout_min = await _timeout_min(db)
    silent = _silence(session, now, timeout_min)

    # 学生说「我自己想」→ 进入沉默模式，只回一句确认，不调用大模型
    if core.wants_silence(content):
        session.silence_mode, session.silence_scope, session.silence_triggered_at = True, "session", now
        sm = AiChatMessage(session_id=session.id, role="student", content=content, created_at=now)
        db.add(sm)
        await db.flush()
        am = AiChatMessage(session_id=session.id, role="assistant", created_at=datetime.now(UTC),
                           content="好的，你先自己想想～我不打扰你。想到了或者卡住了，随时告诉我；过一会儿我也会自动回来。")
        db.add(am)
        db.add(AiStrategyEvent(session_id=session.id, student_id=student.id, event_type="silence_mode", linked_message_id=sm.id, created_at=now))
        await db.commit()
        return {**message_dict(am), "student_message_id": sm.id, "silence": True}
    if silent and core.wants_resume(content):
        session.silence_mode = False
        silent = False

    # 理解突破：关键词初筛 → 大模型确认 → 成就感反馈
    if not image_url and core.aha_prefilter(content):
        hist = await _history(db, session.id)
        res = await _llm([{"role": "system", "content": core.AHA_CONFIRM_PROMPT}] + _history_messages(hist)[-6:]
                         + [{"role": "user", "content": content}], max_tokens=200, temperature=0)
        aha, insight = _parse_aha(res["text"])
        await _log_tokens(db, student.id, session.id, res)
        if aha:
            ach = await _llm([{"role": "system", "content": core.ACHIEVEMENT_PROMPT.format(insight=insight or "学生用自己的话讲清了思路")}]
                             + _history_messages(hist)[-4:] + [{"role": "user", "content": content}], max_tokens=300)
            await _log_tokens(db, student.id, session.id, ach)
            sm = AiChatMessage(session_id=session.id, role="student", content=content, image_url=image_url, created_at=now)
            db.add(sm)
            await db.flush()
            last = (await _recent_strategies(db, session.id, 1))
            am = AiChatMessage(session_id=session.id, role="assistant", content=core.trim_reply(ach["text"], 200), is_aha_trigger=True,
                               strategy_id=last[0] if last else None, tokens_used=ach["usage"]["total_tokens"], created_at=datetime.now(UTC))
            db.add(am)
            session.aha_count = (session.aha_count or 0) + 1
            db.add(AiStrategyEvent(session_id=session.id, student_id=student.id, event_type="aha_moment", linked_message_id=sm.id, created_at=now))
            if last:
                row = await _profile_row(db, student.id, last[0])
                row.effective_count += 1
                _refresh_score(row)
            await db.commit()
            await _maybe_summarize(session.id, student.id)
            return {**message_dict(am), "student_message_id": sm.id, "silence": False}

    # 普通回复：选策略 → 组装提示词 → 调用大模型
    strategies = await _strategies(db)
    state, insight_txt, weak = await _state_text(db, student)
    recent = await _recent_strategies(db, session.id)
    sid, switched = core.pick_strategy(strategies, await _scores(db, student.id), recent, weak)
    strat = next((s for s in strategies if s["id"] == sid), None)
    hist = await _history(db, session.id)
    messages = ([{"role": "system", "content": core.build_system_prompt(strat, state, insight_txt, silent, student.nickname)}]
                + _history_messages(hist) + [{"role": "user", "content": _user_content(content, image_url)}])
    res = await _llm(messages, max_tokens=LLM_MAX_TOKENS, has_image=bool(image_url))
    reply = core.finalize_reply(res["text"], res.get("truncated", False))
    if not reply:
        raise AppException("AI 暂时无法回复，请稍后重试", 503, "ASST-005")

    sm = AiChatMessage(session_id=session.id, role="student", content=content, image_url=image_url, created_at=now)
    db.add(sm)
    await db.flush()
    am = AiChatMessage(session_id=session.id, role="assistant", content=reply, strategy_id=sid,
                       tokens_used=res["usage"]["total_tokens"], created_at=datetime.now(UTC))
    db.add(am)
    await db.flush()
    await _after_reply(db, student.id, session.id, sid, recent[-1] if recent else None, switched, am.id)
    await _log_tokens(db, student.id, session.id, res)
    await db.commit()
    await _maybe_summarize(session.id, student.id)
    return {**message_dict(am), "student_message_id": sm.id, "silence": silent}


def _parse_aha(text: str) -> tuple[bool, str]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return False, ""
    try:
        d = json.loads(m.group(0))
        return bool(d.get("aha")), str(d.get("insight") or "")[:60]
    except (ValueError, TypeError):
        return False, ""


async def _after_reply(db: AsyncSession, student_id: int, session_id: str, sid: str | None, prev: str | None, switched: bool, message_id: int) -> None:
    """记录策略使用 / 切换事件，更新该策略的使用次数；被切走的策略记一次「无效」"""
    if not sid:
        return
    now = datetime.now(UTC)
    row = await _profile_row(db, student_id, sid)
    row.total_uses += 1
    row.last_used_at = now
    _refresh_score(row)
    if switched and prev:
        db.add(AiStrategyEvent(session_id=session_id, student_id=student_id, event_type="strategy_switch", from_strategy_id=prev,
                               to_strategy_id=sid, switch_reason="同一策略连续2次无明显进展", linked_message_id=message_id, created_at=now))
        old = await _profile_row(db, student_id, prev)
        old.ineffective_count += 1
        _refresh_score(old)
    elif not prev:
        db.add(AiStrategyEvent(session_id=session_id, student_id=student_id, event_type="strategy_start", to_strategy_id=sid,
                               linked_message_id=message_id, created_at=now))


# ── 重新生成 / 评分 / 沉默 ───────────────────────────────────────────────────

async def regenerate(db: AsyncSession, student: Student, session: AiChatSession, message_id: int) -> dict:
    m = (await db.execute(select(AiChatMessage).where(AiChatMessage.id == message_id, AiChatMessage.session_id == session.id,
                                                      AiChatMessage.role == "assistant"))).scalar_one_or_none()
    if not m or m.is_aha_trigger or not m.strategy_id:
        raise AppException("这条消息不能重新生成", 400, "ASST-007")
    prev_student = (await db.execute(select(AiChatMessage).where(AiChatMessage.session_id == session.id, AiChatMessage.role == "student",
                                                                 AiChatMessage.id < m.id).order_by(AiChatMessage.id.desc()).limit(1))).scalar_one_or_none()
    if not prev_student:
        raise AppException("这条消息不能重新生成", 400, "ASST-007")

    strategies = await _strategies(db)
    state, insight_txt, weak = await _state_text(db, student)
    sid, _ = core.pick_strategy(strategies, await _scores(db, student.id), [m.strategy_id], weak, exclude=m.strategy_id)
    strat = next((s for s in strategies if s["id"] == sid), None)
    silent = _silence(session, datetime.now(UTC), await _timeout_min(db))
    hist = [h for h in await _history(db, session.id, prev_student.id)]
    messages = [{"role": "system", "content": core.build_system_prompt(strat, state, insight_txt, silent, student.nickname)
                 + "\n\n学生对上一次回答不满意，请换一种方式重新讲解。"}] + _history_messages(hist, vision_last=True)
    res = await _llm(messages, max_tokens=LLM_MAX_TOKENS, temperature=0.9, has_image=bool(prev_student.image_url))
    reply = core.finalize_reply(res["text"], res.get("truncated", False))
    if not reply:
        raise AppException("AI 暂时无法回复，请稍后重试", 503, "ASST-005")
    old = m.strategy_id
    m.content, m.strategy_id, m.student_rating, m.tokens_used = reply, sid, None, res["usage"]["total_tokens"]
    await db.flush()
    await _after_reply(db, student.id, session.id, sid, old, sid != old, m.id)
    await _log_tokens(db, student.id, session.id, res)
    await db.commit()
    return message_dict(m)


async def rate(db: AsyncSession, student: Student, message_id: int, rating: str) -> None:
    if rating not in ("like", "dislike"):
        raise AppException("评分只能是 like 或 dislike", 400)
    m = (await db.execute(select(AiChatMessage).join(AiChatSession, AiChatSession.id == AiChatMessage.session_id)
                          .where(AiChatMessage.id == message_id, AiChatSession.student_id == student.id, AiChatMessage.role == "assistant"))).scalar_one_or_none()
    if not m:
        raise AppException("消息不存在", 404)
    if m.student_rating == rating:
        return
    if m.strategy_id:
        row = await _profile_row(db, student.id, m.strategy_id)
        if m.student_rating == "like":
            row.positive_ratings = max(0, row.positive_ratings - 1)
        elif m.student_rating == "dislike":
            row.negative_ratings = max(0, row.negative_ratings - 1)
        if rating == "like":
            row.positive_ratings += 1
        else:
            row.negative_ratings += 1
        _refresh_score(row)
    m.student_rating = rating
    await db.commit()


# ── 滚动摘要 ─────────────────────────────────────────────────────────────────

async def _maybe_summarize(session_id: str, student_id: int) -> None:
    """每累积 SUMMARY_EVERY 条新消息，后台滚动生成一次对话摘要（≤100 字）；失败只记日志"""
    try:
        async with AsyncSessionLocal() as db:
            s = (await db.execute(select(AiChatSession).where(AiChatSession.id == session_id))).scalar_one_or_none()
            if not s:
                return
            n = (await db.execute(select(func.count()).select_from(AiChatMessage).where(
                AiChatMessage.session_id == session_id, AiChatMessage.id > s.summary_message_id))).scalar_one()
            if not core.summary_due(n):
                return
    except Exception as e:
        logger.warning(f"检查摘要条件失败: {e}")
        return
    asyncio.create_task(summarize_in_background(session_id, student_id))


async def summarize_in_background(session_id: str, student_id: int) -> None:
    try:
        async with AsyncSessionLocal() as db:
            s = (await db.execute(select(AiChatSession).where(AiChatSession.id == session_id))).scalar_one_or_none()
            if not s:
                return
            rows = (await db.execute(select(AiChatMessage).where(AiChatMessage.session_id == session_id, AiChatMessage.id > s.summary_message_id,
                                                                 AiChatMessage.role.in_(("student", "assistant"))).order_by(AiChatMessage.id).limit(40))).scalars().all()
            if not rows:
                return
            text = "\n".join(("学生：" if m.role == "student" else "助教：") + ("[图片] " if m.image_url else "") + m.content[:150] for m in rows)
            res = await _llm([{"role": "system", "content": core.SUMMARY_PROMPT},
                              {"role": "user", "content": f"【已有摘要】\n{s.session_summary or '（无）'}\n\n【新增对话】\n{text}"}], max_tokens=300, temperature=0.3)
            s.session_summary = res["text"].strip()[:200]
            s.summary_message_id = rows[-1].id
            await _log_tokens(db, student_id, session_id, res)
            await db.commit()
            await _extract_insights(db, student_id, session_id, rows)
        from app.services.smart_training import intents
        await intents.refresh_in_background(student_id)   # 摘要更新后同步更新聊天困惑信号和后台学生摘要
    except Exception as e:
        logger.warning(f"生成对话摘要失败 session={session_id}: {e}")


async def _extract_insights(db: AsyncSession, student_id: int, session_id: str, rows: list[AiChatMessage]) -> None:
    """用学生最近说的话更新「个人洞察」：一段总结概括的文字（不是条目），已有内容（含管理员手写的）要保留。
    只存概括后的文字，不存聊天原文；失败不影响其它流程。"""
    said = [m.content.strip()[:200] for m in rows if m.role == "student" and m.content.strip()]
    if not said:
        return
    try:
        summ = (await db.execute(select(StudentAiPromptSummary).where(StudentAiPromptSummary.student_id == student_id))).scalar_one_or_none()
        old = (summ.personal_insight or "").strip() if summ else ""
        res = await _llm([{"role": "system", "content": insights.INSIGHT_PROMPT},
                          {"role": "user", "content": f"【已有的个人洞察】\n{old or '（暂无）'}\n\n【学生最近说的话】\n" + "\n".join(f"- {t}" for t in said[-20:])}],
                         max_tokens=800, temperature=0.2)
        await _log_tokens(db, student_id, session_id, res)
        new = insights.clean_paragraph(res["text"])
        if insights.accept_update(old, new):
            await insights.apply_update(db, student_id, new, source="AI")
            logger.info(f"AI 更新了个人洞察 student={student_id}")
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.warning(f"更新个人洞察失败 student={student_id}: {e}")


# ── 快捷建议问题 ─────────────────────────────────────────────────────────────

async def suggestions(db: AsyncSession, student: Student) -> list[str]:
    from app.services.smart_training.signals import load_signals, POWER_NAMES
    from app.services.smart_training.core import merge_params, smoothed_error
    out: list[str] = []
    try:
        sig = await load_signals(db, student, [])
        params = merge_params(None)
        ranked = sorted(((k, smoothed_error(a, e, params["prior"])) for k, (a, e) in sig.kp_stats.items() if a >= 1.5), key=lambda x: -x[1])
        ids = list(dict.fromkeys(sorted(sig.intents, key=lambda k: -sig.intents[k])[:1] + [k for k, _ in ranked[:2]]))
        names = dict((await db.execute(select(KnowledgePoint.id, KnowledgePoint.name).where(KnowledgePoint.id.in_(ids)))).all()) if ids else {}
        for k in ids[:2]:
            if k in names:
                out.append(f"我想搞懂「{names[k]}」")
        if sig.pending:
            out.append("帮我分析一下最近做错的题")
        if sig.powers:
            weak = min(sig.powers, key=lambda p: sig.powers[p])
            out.append(f"怎么提高我的{POWER_NAMES[weak]}？")
    except Exception as e:
        logger.warning(f"生成快捷问题依据失败 student={student.id}: {e}")
    for d in ("给我讲一道有意思的数学题", "怎么才能学好物理？", "我最近老是粗心，怎么办？"):
        if len(out) >= 4:
            break
        out.append(d)
    return out[:4]

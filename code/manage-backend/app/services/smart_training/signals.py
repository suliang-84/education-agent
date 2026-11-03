"""智能训练的数据库查询：把学生的各类数据装配成 Signals / 抽取池，并生成「学习状态」文字（学生管理 → 摘要）"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgePoint
from app.models.question import Question
from app.models.student import (
    FivePowerProfile, QuestionFavorite, Student, StudentLearningSignal, WrongAnswerRecord,
)
from app.models.training import TrainingAnswerRecord, TrainingSession
from app.services import wrong_scope
from app.services.question_pool import kp_overlap, pool_filters
from app.services.smart_training.core import POWERS, QInfo, Signals, decay, merge_params, smoothed_error
from app.services.wrong_book import MASTERED_STATUSES, PENDING_STATUSES

HISTORY_DAYS = 120   # 只看最近 120 天的做题记录
POWER_NAMES = {"INSIGHT": "洞察力", "CONSTRUCT": "建构力", "DEDUCE": "推演力", "ADAPT": "调适力", "MIGRATE": "迁移力"}
TYPE_NAMES = {
    "SINGLE_CHOICE": "单选题", "MULTIPLE_CHOICE": "多选题", "TRUE_FALSE": "判断题",
    "FILL_BLANK": "填空题", "APPLICATION": "应用题",
}


def _int_ids(raw) -> list[int]:
    """题目的 knowledge_point_ids 里个别历史数据混有知识点名称（字符串），只取整数 id"""
    out = []
    for k in raw or []:
        if isinstance(k, bool):
            continue
        if isinstance(k, int):
            out.append(k)
        elif isinstance(k, str) and k.strip().isdigit():
            out.append(int(k.strip()))
    return out


async def load_pool(db: AsyncSession, student: Student, subject_code: str | None) -> tuple[list[QInfo], list[tuple]]:
    """智能训练的抽取池：当前学期、该科目下后台已启用的题。返回 (QInfo 列表, 学期的知识点 [(id,name,chapter_id)])"""
    _chapters, kps = await wrong_scope.semester_structure(db, student, subject_code)
    if not kps:
        return [], []
    rows = (await db.execute(
        select(Question).where(*pool_filters(), kp_overlap([k[0] for k in kps]))
    )).scalars().all()
    pool = []
    for q in rows:
        weights = {k: float(v) for k, v in (q.five_power_weights or {}).items() if k in POWERS}
        pool.append(QInfo(
            id=q.id, question_type=q.question_type, difficulty=q.difficulty,
            kp_ids=_int_ids(q.knowledge_point_ids),
            primary_power=q.primary_power, power_weights=weights,
        ))
    return pool, kps


async def load_signals(db: AsyncSession, student: Student, recent_ids: list[int], override: dict | None = None,
                       now: datetime | None = None) -> Signals:
    now = now or datetime.now(UTC)
    params = merge_params(override)
    sig = Signals(now=now, recent_ids=set(recent_ids))

    # 五力
    prof = (await db.execute(
        select(FivePowerProfile).where(FivePowerProfile.student_id == student.id, FivePowerProfile.is_latest == True)  # noqa: E712
    )).scalar_one_or_none()
    if prof:
        sig.powers = {
            "INSIGHT": prof.insight_final, "CONSTRUCT": prof.construct_final, "DEDUCE": prof.deduce_final,
            "ADAPT": prof.adapt_final, "MIGRATE": prof.migrate_final,
        }

    # 做题历史 → 知识点 / 题型薄弱度（带时间衰减）
    rows = (await db.execute(
        select(TrainingAnswerRecord.question_id, TrainingAnswerRecord.is_correct,
               func.coalesce(TrainingAnswerRecord.answered_at, TrainingAnswerRecord.created_at),
               Question.question_type, Question.knowledge_point_ids)
        .join(TrainingSession, TrainingSession.id == TrainingAnswerRecord.session_id)
        .join(Question, Question.id == TrainingAnswerRecord.question_id)
        .where(TrainingSession.student_id == student.id,
               TrainingAnswerRecord.created_at > now - timedelta(days=HISTORY_DAYS),
               TrainingAnswerRecord.is_correct.is_not(None))
    )).all()
    for qid, ok, at, qtype, kp_ids in rows:
        w = decay((now - at).total_seconds() / 86400, params["half_life_days"])
        err = 0.0 if ok else 1.0
        for kid in set(_int_ids(kp_ids)):
            a, e = sig.kp_stats.get(kid, (0.0, 0.0))
            sig.kp_stats[kid] = (a + w, e + w * err)
        if qtype:
            a, e = sig.type_stats.get(qtype, (0.0, 0.0))
            sig.type_stats[qtype] = (a + w, e + w * err)
        prev = sig.answered.get(qid)
        if prev is None or at > prev[0]:
            sig.answered[qid] = (at, bool(ok))

    # 错题集
    for qid, status, aha_at in (await db.execute(
        select(WrongAnswerRecord.question_id, WrongAnswerRecord.review_status, WrongAnswerRecord.aha_at)
        .where(WrongAnswerRecord.student_id == student.id)
    )).all():
        if status in PENDING_STATUSES:
            sig.pending.add(qid)
        elif status in MASTERED_STATUSES:
            sig.mastered[qid] = aha_at or now

    # 收藏
    sig.favorites = set((await db.execute(
        select(QuestionFavorite.question_id).where(QuestionFavorite.student_id == student.id)
    )).scalars().all())

    # 聊天里提取的近期困惑（缓存，已按时间衰减）
    row = (await db.execute(
        select(StudentLearningSignal).where(StudentLearningSignal.student_id == student.id)
    )).scalar_one_or_none()
    if row:
        for it in row.intents or []:
            try:
                at = datetime.fromisoformat(it["mentioned_at"])
                w = float(it["confidence"]) * decay((now - at).total_seconds() / 86400, params["intent_half_life_days"])
                if w >= 0.1:
                    sig.intents[int(it["kp_id"])] = max(w, sig.intents.get(int(it["kp_id"]), 0.0))
            except (KeyError, ValueError, TypeError):
                continue
    return sig


async def learning_state_text(db: AsyncSession, student: Student) -> str:
    """学生的学习状态描述（后台「学生管理 → 摘要 → 学习信息摘要」使用，也是智能训练依据的信号）"""
    sig = await load_signals(db, student, [])
    params = merge_params(None)
    parts: list[str] = []
    if sig.powers:
        order = sorted(sig.powers.items(), key=lambda kv: kv[1])
        weak, strong = order[0], order[-1]
        parts.append(
            "五力：" + "、".join(f"{POWER_NAMES[p]}{int(s)}分" for p, s in sig.powers.items())
            + f"；最弱{POWER_NAMES[weak[0]]}，最强{POWER_NAMES[strong[0]]}。"
        )
    # 当前学期错题集 / 收藏概况
    pending_n = len(sig.pending)
    parts.append(f"错题集：待攻克{pending_n}题，已攻克{len(sig.mastered)}题；收藏{len(sig.favorites)}题。")
    # 薄弱知识点（作答≥2 次且平滑错误率最高的前 3 个）
    ranked = sorted(
        ((k, smoothed_error(a, e, params["prior"]), a) for k, (a, e) in sig.kp_stats.items() if a >= 1.5),
        key=lambda x: -x[1],
    )[:3]
    names = {}
    ids = [r[0] for r in ranked] + list(sig.intents)
    if ids:
        names = dict((await db.execute(
            select(KnowledgePoint.id, KnowledgePoint.name).where(KnowledgePoint.id.in_(ids))
        )).all())
    if ranked:
        parts.append("薄弱知识点：" + "、".join(f"{names.get(k, k)}（错误率约{int(r * 100)}%）" for k, r, _ in ranked) + "。")
    # 薄弱题型
    if sig.type_stats:
        tot_a = sum(a for a, _ in sig.type_stats.values())
        tot_e = sum(e for _, e in sig.type_stats.values())
        base = smoothed_error(tot_a, tot_e, params["prior"])
        tw = sorted(
            ((t, smoothed_error(a, e, params["prior"])) for t, (a, e) in sig.type_stats.items() if a >= 2),
            key=lambda x: -x[1],
        )
        if tw and tw[0][1] > base + 0.1:
            parts.append(f"错得较多的题型：{TYPE_NAMES.get(tw[0][0], tw[0][0])}。")
    # 聊天：近期困惑与摘要
    row = (await db.execute(
        select(StudentLearningSignal).where(StudentLearningSignal.student_id == student.id)
    )).scalar_one_or_none()
    if sig.intents:
        parts.append("近期向AI助手提到的困惑：" + "、".join(str(names.get(k, k)) for k in sorted(sig.intents, key=lambda k: -sig.intents[k])[:3]) + "。")
    if row and row.chat_summary:
        parts.append(f"近期交流：{row.chat_summary}")
    return "".join(parts)

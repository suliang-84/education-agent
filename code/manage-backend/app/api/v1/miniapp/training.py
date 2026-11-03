"""小程序端训练模块 — §5"""
import random
import re
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.student import (
    FivePowerProfile, FivePowerTrainingProfile, Student, WrongAnswerRecord,
)
from app.models.training import TrainingAnswerRecord, TrainingDimensionConfig, TrainingSession, TrainingInterrupt
from app.models.question import Question
from app.models.knowledge import Chapter, Grade, KnowledgePoint, Semester, Subject
from app.services import wrong_book, wrong_scope
from app.services.question_picker import pick_questions
from app.services.question_pool import kp_overlap, pool_filters
from app.services.training_analysis import generate_analysis
from app.services.training_resume import merge_answers_snapshot, resume_index
from app.services.answer_judge import (
    SINGLE_CHOICE, MULTIPLE_CHOICE,
    blank_count_of, judge_answer, question_type_of, split_stem_options,
)

router = APIRouter()


class CreateSessionReq(BaseModel):
    training_dimension: str  # KNOWLEDGE_POINT / UNIT / SEMESTER / ERROR_QUESTIONS / RANDOM
    knowledge_point_id: int | None = None
    chapter_id: int | None = None
    semester_id: int | None = None
    subject_code: str | None = None
    wrong_status: str | None = None   # 错题集训练：pending（待攻克，默认）/ mastered（已攻克）；范围由 chapter_id / knowledge_point_id 进一步限定


class SubmitAnswerReq(BaseModel):
    session_id: str
    question_id: int
    question_index: int
    student_answer: str | None = None      # 整段作答文本（单选 'C'、多选 'CD'、判断 '对'、填空 / 应用题的展示文本），写入答题记录和错题集
    student_answers: list[str] | None = None   # 填空题：按空分别作答，传了就逐空比对（答案里本身带逗号时不会被误拆）
    final_answer: str | None = None        # 应用题：「最终答案」一栏，传了就只用它判对错（不再从整段过程里凑数字）
    time_spent_sec: int
    hint_level_used: int = 0


class SaveInterruptReq(BaseModel):
    session_id: str
    subject_code: str
    training_dimension: str
    scope_info: dict = {}
    scope_label: str = ""
    questions_snapshot: list = []
    answers_snapshot: list = []
    current_question_index: int = 0


@router.get("/wrong-summary", summary="错题科目统计（进入错题集前调用）")
async def wrong_summary(
    subject_code: str | None = Query(None),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """按科目统计待攻克题数：题目去重，资料里有年级学期时只算当前学期（与错题集页最外层「待攻克」一致）"""
    subjects = (await db.execute(
        select(Subject).where(Subject.code == subject_code) if subject_code else select(Subject)
    )).scalars().all()
    out = []
    for sub in subjects:
        cnt = await wrong_scope.pending_count(db, student, sub.code)
        if cnt > 0:
            out.append({"subject_code": sub.code, "subject_name": sub.name, "pending_count": cnt})
    return ok_response({"total_pending": sum(r["pending_count"] for r in out), "subjects": out})


async def _current_semester_id(db: AsyncSession, student: Student, subject_code: str | None) -> int | None:
    """学生当前年级 + 学期在指定科目下对应的 semesters.id；找不到返回 None"""
    q = (
        select(Semester.id)
        .join(Grade, Semester.grade_id == Grade.id)
        .join(Subject, Grade.subject_id == Subject.id)
        .where(Grade.code == student.grade, Semester.code == student.semester)
    )
    if subject_code:
        q = q.where(Subject.code == subject_code)
    return (await db.execute(q)).scalars().first()


async def _recent_question_ids(db: AsyncSession, student_id: int, limit: int) -> list[int]:
    """该学生最近做过的 limit 道题（去重，按答题时间倒序），抽题时尽量避开"""
    if limit <= 0:
        return []
    rows = (await db.execute(
        select(TrainingAnswerRecord.question_id)
        .join(TrainingSession, TrainingSession.id == TrainingAnswerRecord.session_id)
        .where(TrainingSession.student_id == student_id)
        .order_by(TrainingAnswerRecord.created_at.desc())
        .limit(limit * 3)
    )).scalars().all()
    out: list[int] = []
    for qid in rows:
        if qid not in out:
            out.append(qid)
        if len(out) >= limit:
            break
    return out


@router.post("/session", summary="创建训练会话")
async def create_session(
    body: CreateSessionReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    # 检查五力画像
    profile = (
        await db.execute(
            select(FivePowerProfile).where(
                FivePowerProfile.student_id == student.id,
                FivePowerProfile.is_latest == True,
            )
        )
    ).scalar_one_or_none()
    if not profile:
        raise AppException("请先完成五力测试", 400, "TRAIN-001")

    # 获取该维度的参数配置
    dim_config = (
        await db.execute(
            select(TrainingDimensionConfig).where(
                TrainingDimensionConfig.dimension == body.training_dimension,
                TrainingDimensionConfig.is_active == True,
            )
        )
    ).scalar_one_or_none()

    questions_per_session = dim_config.questions_per_session if dim_config else 5

    # 抽取池：后台「启用」的题目即进入抽取池（与发布状态独立；已归档的不抽）
    q_query = select(Question.id, Question.question_type, Question.difficulty).where(*pool_filters())

    if body.training_dimension == "KNOWLEDGE_POINT" and body.knowledge_point_id:
        q_query = q_query.where(
            Question.knowledge_point_ids.contains([body.knowledge_point_id])
        )
    elif body.training_dimension == "UNIT" and body.chapter_id:
        kps = (await db.execute(
            select(KnowledgePoint.id).where(KnowledgePoint.chapter_id == body.chapter_id)
        )).scalars().all()
        q_query = q_query.where(kp_overlap(list(kps)))
    elif body.training_dimension == "SEMESTER" and body.semester_id:
        chapters = (await db.execute(
            select(Chapter.id).where(Chapter.semester_id == body.semester_id)
        )).scalars().all()
        kps = (await db.execute(
            select(KnowledgePoint.id).where(KnowledgePoint.chapter_id.in_(chapters))
        )).scalars().all()
        q_query = q_query.where(kp_overlap(list(kps)))
    elif body.training_dimension == "RANDOM":
        # 随机训练：当前学期（学生资料里的年级 + 学期）该科目下的全部已启用题目
        if not student.grade or not student.semester:
            raise AppException("请先补充年级和学期", 400, "TRAIN-004")
        semester_id = await _current_semester_id(db, student, body.subject_code)
        kps = (await db.execute(
            select(KnowledgePoint.id).join(Chapter, KnowledgePoint.chapter_id == Chapter.id)
            .where(Chapter.semester_id == semester_id)
        )).scalars().all() if semester_id else []
        q_query = q_query.where(kp_overlap(list(kps)))
    elif body.training_dimension == "ERROR_QUESTIONS":
        # 错题集训练：从当前学期的「待攻克 / 已攻克」题里抽；可按单元 / 知识点进一步限定
        if not student.grade or not student.semester:
            raise AppException("请先补充年级和学期", 400, "TRAIN-004")
        mastered = body.wrong_status == "mastered"
        chapters, kps_all = await wrong_scope.semester_structure(db, student, body.subject_code)
        if body.knowledge_point_id:
            scope_kps = [k[0] for k in kps_all if k[0] == body.knowledge_point_id]
        elif body.chapter_id:
            scope_kps = [k[0] for k in kps_all if k[2] == body.chapter_id]
        else:
            scope_kps = [k[0] for k in kps_all]
        wrong_ids = [q[0] for q in await wrong_scope.wrong_questions(db, student.id, body.subject_code, mastered)]
        if not scope_kps or not wrong_ids:
            raise AppException("暂无已攻克题目" if mastered else "暂无待攻克题目", 400, "TRAIN-003")
        q_query = q_query.where(Question.id.in_(wrong_ids), kp_overlap(scope_kps))
    elif body.subject_code:
        q_query = q_query.join(Subject, Question.subject_id == Subject.id).where(
            Subject.code == body.subject_code
        )

    pool_rows = (await db.execute(q_query)).all()
    # 按题型比例 + 难度比例抽题，尽量避开最近做过的题
    dedup_n = dim_config.dedup_window_size if dim_config else 30
    recent_ids = await _recent_question_ids(db, student.id, dedup_n)
    ids = pick_questions(
        [{"id": r.id, "question_type": r.question_type, "difficulty": r.difficulty} for r in pool_rows],
        questions_per_session,
        type_ratio=dim_config.type_ratio if dim_config else None,
        difficulty_ratio=dim_config.difficulty_ratio if dim_config else None,
        avoid_ids=recent_ids,
    )
    by_id = {q.id: q for q in (await db.execute(select(Question).where(Question.id.in_(ids)))).scalars().all()} if ids else {}
    selected_qs = [by_id[i] for i in ids if i in by_id]

    if len(selected_qs) < 1:
        if body.training_dimension == "RANDOM":
            raise AppException("当前学期暂无题目", 400, "TRAIN-002")
        raise AppException("范围内题目不足，无法开始训练", 400, "TRAIN-002")

    # 确定训练模式（基于五力画像）
    training_mode = profile.recommended_mode or "TRAIN_WEAKNESS"
    focus_power = profile.primary_weakness

    scope_info: dict = {}
    if body.training_dimension == "KNOWLEDGE_POINT" and body.knowledge_point_id:
        kp = (await db.execute(
            select(KnowledgePoint).where(KnowledgePoint.id == body.knowledge_point_id)
        )).scalar_one_or_none()
        if kp:
            scope_info = {"knowledge_point_id": kp.id, "name": kp.name}
    elif body.training_dimension == "UNIT" and body.chapter_id:
        ch = (await db.execute(select(Chapter).where(Chapter.id == body.chapter_id))).scalar_one_or_none()
        if ch:
            scope_info = {"chapter_id": ch.id, "name": ch.name}
    elif body.training_dimension == "ERROR_QUESTIONS":
        label = "已攻克" if body.wrong_status == "mastered" else "待攻克"
        name = label
        if body.knowledge_point_id:
            kp = (await db.execute(select(KnowledgePoint).where(KnowledgePoint.id == body.knowledge_point_id))).scalar_one_or_none()
            name = f"{label} · {kp.name}" if kp else label
        elif body.chapter_id:
            ch = (await db.execute(select(Chapter).where(Chapter.id == body.chapter_id))).scalar_one_or_none()
            name = f"{label} · {ch.name}" if ch else label
        scope_info = {"wrong_status": body.wrong_status or "pending", "chapter_id": body.chapter_id,
                      "knowledge_point_id": body.knowledge_point_id, "name": name}

    session_id = str(uuid.uuid4())
    snapshot = {
        "question_ids": [q.id for q in selected_qs],
        "total": len(selected_qs),
    }
    five_power_snap = {
        "INSIGHT": profile.insight_final,
        "CONSTRUCT": profile.construct_final,
        "DEDUCE": profile.deduce_final,
        "ADAPT": profile.adapt_final,
        "MIGRATE": profile.migrate_final,
        "primary_weakness": profile.primary_weakness,
        "preferred_force": profile.preferred_force,
    }

    session = TrainingSession(
        id=session_id,
        student_id=student.id,
        config_version_id=1,  # 默认配置
        dimension_config_id=dim_config.id if dim_config else None,
        training_dimension=body.training_dimension,
        knowledge_point_id=body.knowledge_point_id,
        chapter_id=body.chapter_id,
        semester_id=body.semester_id,
        training_mode=training_mode,
        training_focus_power=focus_power,
        preferred_force=profile.preferred_force,
        five_power_snapshot=five_power_snap,
        question_snapshot=snapshot,
        session_status="active",
        total_questions=len(selected_qs),
        started_at=datetime.now(UTC),
    )
    db.add(session)
    await db.commit()

    return ok_response({
        "session_id": session_id,
        "training_dimension": body.training_dimension,
        "training_mode": training_mode,
        "training_focus_power": focus_power,
        "preferred_force": profile.preferred_force,
        "dimension_config": {
            "version_number": dim_config.version_number if dim_config else "default",
            "questions_per_session": questions_per_session,
        },
        "questions": [_question_payload(q, i) for i, q in enumerate(selected_qs)],
        "total_questions": len(selected_qs),
        "scope_info": scope_info,
        "tips": {
            "focus_power_name": focus_power,
            "hint": f"本次重点练习{focus_power}维度",
        },
    })


@router.post("/answer", summary="提交单题答案")
async def submit_answer(
    body: SubmitAnswerReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session = (
        await db.execute(
            select(TrainingSession).where(
                TrainingSession.id == body.session_id,
                TrainingSession.student_id == student.id,
                TrainingSession.session_status == "active",
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise AppException("训练会话不存在或已结束", 404)

    question = (
        await db.execute(select(Question).where(Question.id == body.question_id))
    ).scalar_one_or_none()
    if not question:
        raise AppException("题目不存在", 404)

    # 同一会话的同一题只能提交一次（数据库有 (session_id, question_index) 唯一约束；已提交的答案不可覆盖修改）。
    # 重复提交（恢复了一个过期的中断快照、网络重试、连点）不能报 500，而是直接返回已有的判题结果，让前端显示之前的作答。
    existing = await _find_answer_record(db, body.session_id, body.question_index)
    if existing:
        return ok_response(_answer_result(existing, already_answered=True))

    # 判题：按题型比对答案
    is_correct = judge_answer(
        question.answer, question.question_type, body.student_answer,
        student_answers=body.student_answers, final_answer=body.final_answer,
    )

    record = TrainingAnswerRecord(
        session_id=body.session_id,
        question_id=body.question_id,
        question_index=body.question_index,
        power_type=question.primary_power or "UNKNOWN",
        student_answer=body.student_answer,
        is_correct=is_correct,
        answer_quality=1.0 if is_correct else 0.0,
        time_spent_sec=body.time_spent_sec,
        hint_level_used=body.hint_level_used,
        rag_generated=False,
        generation_status=None,   # 解析改为学生点击「智能解答」时才生成，答错也不再立即触发
        answered_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    db.add(record)

    # 错题集：同一学生同一道题只有一条记录（合并去重）。
    # 任何训练答错 → 待攻克；只有在错题集训练里答对待攻克的题 → 已攻克（规则见 services/wrong_book.py）
    wrong = (await db.execute(
        select(WrongAnswerRecord).where(
            WrongAnswerRecord.student_id == student.id,
            WrongAnswerRecord.question_id == body.question_id,
        )
    )).scalar_one_or_none()
    new_status = wrong_book.next_status(wrong.review_status if wrong else None, bool(is_correct), session.training_dimension)
    if new_status:
        now = datetime.now(UTC)
        if wrong is None:
            db.add(WrongAnswerRecord(
                id=str(uuid.uuid4()),
                student_id=student.id,
                question_id=body.question_id,
                source_module="training",
                source_session_id=body.session_id,
                student_answer=body.student_answer,
                review_status=new_status,
                created_at=now,
            ))
        else:
            wrong.review_status = new_status
            wrong.aha_at = now if new_status == wrong_book.MASTERED else None
            if new_status == wrong_book.PENDING:      # 再次答错：更新为最近一次的作答
                wrong.student_answer = body.student_answer
                wrong.source_session_id = body.session_id

    try:
        await db.commit()
    except IntegrityError:
        # 并发的重复提交：另一个请求刚刚写入了同一题 → 回滚，返回已有结果
        await db.rollback()
        existing = await _find_answer_record(db, body.session_id, body.question_index)
        if existing:
            return ok_response(_answer_result(existing, already_answered=True))
        raise
    return ok_response(_answer_result(record, already_answered=False))


async def _find_answer_record(db: AsyncSession, session_id: str, question_index: int) -> TrainingAnswerRecord | None:
    return (
        await db.execute(
            select(TrainingAnswerRecord).where(
                TrainingAnswerRecord.session_id == session_id,
                TrainingAnswerRecord.question_index == question_index,
            )
        )
    ).scalar_one_or_none()


def _answer_result(record: TrainingAnswerRecord, already_answered: bool) -> dict:
    return {
        "answer_record_id": record.id,
        "is_correct": bool(record.is_correct),
        "rag_status": None,
        "proactive_trigger": False,
        "already_answered": already_answered,          # True：该题此前已提交过，本次没有新增记录
        "student_answer": record.student_answer,        # 已提交过时，前端按它显示之前的作答
    }


class AnalysisReq(BaseModel):
    session_id: str
    question_id: int
    regenerate: bool = False   # True：忽略已生成的解析，重新调用大模型


@router.post("/analysis", summary="智能解答：按需生成参考解析（调用大模型）")
async def generate_question_analysis(
    body: AnalysisReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """学生在答题页点击「智能解答」时才调用大模型，得出该题的参考解析。

    - 必须是本人的训练会话、并且已作答该题（按 session_id + question_id 取最近一条答题记录）
    - 已生成过的解析直接返回缓存（`cached=true`），不重复调用大模型；`regenerate=true` 时强制重新生成
    - 大模型不可用（未配置 / 超时 / 报错）时不报 500，降级返回题库里的静态参考解析（`status=degraded`），前端可再点重试
    """
    session = (
        await db.execute(
            select(TrainingSession).where(
                TrainingSession.id == body.session_id,
                TrainingSession.student_id == student.id,
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise AppException("训练会话不存在", 404)

    record = (
        await db.execute(
            select(TrainingAnswerRecord)
            .where(
                TrainingAnswerRecord.session_id == body.session_id,
                TrainingAnswerRecord.question_id == body.question_id,
            )
            .order_by(TrainingAnswerRecord.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not record:
        raise AppException("请先完成该题作答，再使用智能解答", 400)

    question = (
        await db.execute(select(Question).where(Question.id == body.question_id))
    ).scalar_one_or_none()
    if not question:
        raise AppException("题目不存在", 404)

    if record.rag_content and not body.regenerate:
        return ok_response({"status": "completed", "content": record.rag_content, "static_solution": None, "cached": True})

    try:
        content = await generate_analysis(question, record.student_answer, record.is_correct)
    except Exception as e:  # 未配置密钥 / 超时 / 网络 / 返回异常：降级，不影响学生继续答题
        logger.warning("智能解答生成失败 record={} {}: {}", record.id, type(e).__name__, e)
        record.generation_status = "failed"
        await db.commit()
        return ok_response({
            "status": "degraded",
            "content": None,
            "static_solution": question.solution or "暂无参考解析",
            "cached": False,
        })

    record.rag_content = content
    record.rag_generated = True
    record.generation_status = "completed"
    await db.commit()
    return ok_response({"status": "completed", "content": content, "static_solution": None, "cached": False})


class CompleteReq(BaseModel):
    session_id: str


@router.post("/complete", summary="完成训练会话")
async def complete_session(
    body: CompleteReq | None = None,                 # 接口设计说明书 §5.5：session_id 在请求体里
    session_id: str | None = Query(None),            # 兼容旧写法（查询参数）。注意：此前只支持查询参数，而小程序发的是 JSON 请求体，
                                                     # 所以「完成训练」一直 422 失败、会话永远停在 active、中断记录也清不掉
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session_id = body.session_id if body else session_id
    if not session_id:
        raise AppException("缺少 session_id", 422)
    session = (
        await db.execute(
            select(TrainingSession).where(
                TrainingSession.id == session_id,
                TrainingSession.student_id == student.id,
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise AppException("会话不存在", 404)

    records = (
        await db.execute(
            select(TrainingAnswerRecord).where(TrainingAnswerRecord.session_id == session_id)
        )
    ).scalars().all()

    correct = sum(1 for r in records if r.is_correct)
    total = len(records)

    session.session_status = "completed"
    session.correct_count = correct
    session.ended_at = datetime.now(UTC)
    session.is_early_end = total < (session.total_questions or 5)
    await db.commit()

    # 完成后自动清除关联的中断记录
    interrupt = (
        await db.execute(
            select(TrainingInterrupt).where(
                TrainingInterrupt.session_id == session_id,
                TrainingInterrupt.student_id == student.id,
            )
        )
    ).scalar_one_or_none()
    if interrupt:
        await db.delete(interrupt)
        await db.commit()

    return ok_response({
        "session_id": session_id,
        "summary": {
            "total_questions": total,
            "correct_count": correct,
            "accuracy_rate": round(correct / total, 2) if total else 0,
        },
        "profile_update_status": "pending",
        "wrong_answer_count": total - correct,
    }, "训练完成")


@router.get("/interrupt", summary="查询训练中断记录")
async def get_interrupt(
    subject_code: str = Query(...),
    training_dimension: str = Query(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    record = (
        await db.execute(
            select(TrainingInterrupt).where(
                TrainingInterrupt.student_id == student.id,
                TrainingInterrupt.subject_code == subject_code,
                TrainingInterrupt.training_dimension == training_dimension,
            )
        )
    ).scalar_one_or_none()

    if not record:
        return ok_response({"has_interrupt": False, "interrupt": None})

    # 会话已不存在 / 已结束（完成、放弃）：这条中断记录没有恢复的意义，清掉
    session = (
        await db.execute(select(TrainingSession).where(TrainingSession.id == record.session_id))
    ).scalar_one_or_none()
    if not session or session.session_status != "active":
        await db.delete(record)
        await db.commit()
        return ok_response({"has_interrupt": False, "interrupt": None})

    # 以数据库里的真实作答为准补全快照，并把当前题顺延到第一道没答的题。
    # 中断记录只在「退出并保存」时写入，恢复后继续作答又直接关掉小程序，快照就过期了，
    # 学生会对已答过的题再提交一次
    answer_records = (
        await db.execute(
            select(TrainingAnswerRecord)
            .where(TrainingAnswerRecord.session_id == record.session_id)
            .order_by(TrainingAnswerRecord.question_index)
        )
    ).scalars().all()
    answers_snapshot = merge_answers_snapshot(record.answers_snapshot, answer_records)
    current_index = resume_index(
        record.current_question_index,
        {a["question_index"] for a in answers_snapshot},
        len(record.questions_snapshot or []),
    )

    return ok_response({
        "has_interrupt": True,
        "interrupt": {
            "interrupt_id": record.id,
            "subject_code": record.subject_code,
            "training_dimension": record.training_dimension,
            "scope_label": record.scope_label,
            "scope_info": record.scope_info,
            "questions_snapshot": record.questions_snapshot,
            "answers_snapshot": answers_snapshot,
            "current_question_index": current_index,
            "total_questions": record.total_questions,
            "session_id": record.session_id,
            "interrupted_at": record.interrupted_at.isoformat() if record.interrupted_at else None,
        },
    })


@router.post("/interrupt", summary="保存训练中断状态")
async def save_interrupt(
    body: SaveInterruptReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)
    # 先查是否存在
    existing = (
        await db.execute(
            select(TrainingInterrupt).where(
                TrainingInterrupt.student_id == student.id,
                TrainingInterrupt.subject_code == body.subject_code,
                TrainingInterrupt.training_dimension == body.training_dimension,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.session_id = body.session_id
        existing.scope_label = body.scope_label
        existing.scope_info = body.scope_info
        existing.questions_snapshot = body.questions_snapshot
        existing.answers_snapshot = body.answers_snapshot
        existing.current_question_index = body.current_question_index
        existing.total_questions = len(body.questions_snapshot)
        existing.interrupted_at = now
        existing.updated_at = now
        record = existing
    else:
        record = TrainingInterrupt(
            id=str(uuid.uuid4()),
            student_id=student.id,
            subject_code=body.subject_code,
            training_dimension=body.training_dimension,
            scope_label=body.scope_label,
            scope_info=body.scope_info,
            questions_snapshot=body.questions_snapshot,
            answers_snapshot=body.answers_snapshot,
            current_question_index=body.current_question_index,
            total_questions=len(body.questions_snapshot),
            session_id=body.session_id,
            interrupted_at=now,
            updated_at=now,
        )
        db.add(record)

    await db.commit()

    return ok_response({
        "interrupt_id": record.id,
        "interrupted_at": record.interrupted_at.isoformat(),
    })


@router.delete("/interrupt", summary="删除训练中断记录")
async def delete_interrupt(
    subject_code: str = Query(...),
    training_dimension: str = Query(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    record = (
        await db.execute(
            select(TrainingInterrupt).where(
                TrainingInterrupt.student_id == student.id,
                TrainingInterrupt.subject_code == subject_code,
                TrainingInterrupt.training_dimension == training_dimension,
            )
        )
    ).scalar_one_or_none()

    if record:
        await db.delete(record)
        await db.commit()

    return ok_response(None, msg="中断记录已清除")


# ── 下发给小程序的题目结构 ─────────────────────────────────────────────────────

def _question_payload(q: Question, index: int) -> dict:
    """训练会话下发的单道题。

    - 单选 / 多选：把选项从题干文本里拆出来（stem 只留纯题干，options 为 [{key, text}]）；
      拆不出来时 stem 保持原样、options 为 None，小程序退回文本框作答
    - 填空：下发空数 blank_count（只给数量，不给答案内容）
    - 不下发标准答案 q.answer（抓包即可看到答案），判题只在服务端 judge_answer 里做
    """
    qtype = question_type_of(q)
    stem, options = q.stem, None
    if qtype in (SINGLE_CHOICE, MULTIPLE_CHOICE):
        stem, options = split_stem_options(q.stem)
    return {
        "question_id": q.id,
        "question_index": index,
        "stem": stem,
        "image_url": q.image_url,
        "difficulty": q.difficulty,
        "power_type": q.primary_power,
        "question_type": qtype,
        "options": options,
        "blank_count": blank_count_of(q),
    }

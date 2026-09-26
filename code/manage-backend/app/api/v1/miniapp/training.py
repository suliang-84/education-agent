"""小程序端训练模块 — §5"""
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.student import (
    FivePowerProfile, FivePowerTrainingProfile, Student, WrongAnswerRecord,
)
from app.models.training import TrainingAnswerRecord, TrainingDimensionConfig, TrainingSession
from app.models.question import Question
from app.models.knowledge import KnowledgePoint, Chapter, Semester, Subject

router = APIRouter()


class CreateSessionReq(BaseModel):
    training_dimension: str  # KNOWLEDGE_POINT / UNIT / SEMESTER / ERROR_QUESTIONS / RANDOM
    knowledge_point_id: int | None = None
    chapter_id: int | None = None
    semester_id: int | None = None
    subject_code: str | None = None


class SubmitAnswerReq(BaseModel):
    session_id: str
    question_id: int
    question_index: int
    student_answer: str | None = None
    time_spent_sec: int
    hint_level_used: int = 0


@router.get("/wrong-summary", summary="错题科目统计（进入错题集前调用）")
async def wrong_summary(
    subject_code: str | None = Query(None),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """按科目统计待攻克错题数（review_status in unreview/reviewing/pending_consolidation）"""
    pending_statuses = ["unreview", "reviewing", "pending_consolidation"]

    # 查询各科目错题数
    q = (
        select(Subject.code, Subject.name, func.count(WrongAnswerRecord.id).label("cnt"))
        .join(Question, WrongAnswerRecord.question_id == Question.id)
        .join(Subject, Question.subject_id == Subject.id)
        .where(
            WrongAnswerRecord.student_id == student.id,
            WrongAnswerRecord.review_status.in_(pending_statuses),
        )
        .group_by(Subject.code, Subject.name)
    )
    if subject_code:
        q = q.where(Subject.code == subject_code)

    rows = (await db.execute(q)).all()
    total = sum(r.cnt for r in rows)

    return ok_response({
        "total_pending": total,
        "subjects": [
            {"subject_code": r.code, "subject_name": r.name, "pending_count": r.cnt}
            for r in rows
        ],
    })


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

    # 选题（简化版：按维度范围随机选题）
    q_query = select(Question).where(
        Question.status == "published",
        Question.deleted_at == None,
    )

    if body.training_dimension == "KNOWLEDGE_POINT" and body.knowledge_point_id:
        q_query = q_query.where(
            Question.knowledge_point_ids.contains([body.knowledge_point_id])
        )
    elif body.training_dimension == "UNIT" and body.chapter_id:
        kps = (await db.execute(
            select(KnowledgePoint.id).where(KnowledgePoint.chapter_id == body.chapter_id)
        )).scalars().all()
        q_query = q_query.where(Question.knowledge_point_ids.overlap(kps))
    elif body.training_dimension == "SEMESTER" and body.semester_id:
        chapters = (await db.execute(
            select(Chapter.id).where(Chapter.semester_id == body.semester_id)
        )).scalars().all()
        kps = (await db.execute(
            select(KnowledgePoint.id).where(KnowledgePoint.chapter_id.in_(chapters))
        )).scalars().all()
        q_query = q_query.where(Question.knowledge_point_ids.overlap(kps))
    elif body.training_dimension == "ERROR_QUESTIONS":
        # 从错题集选题
        wrong_qids = (await db.execute(
            select(WrongAnswerRecord.question_id).where(
                WrongAnswerRecord.student_id == student.id,
                WrongAnswerRecord.review_status.in_(["unreview", "reviewing", "pending_consolidation"]),
            ).limit(50)
        )).scalars().all()
        if not wrong_qids:
            raise AppException("该科目暂无待攻克错题", 400, "TRAIN-003")
        q_query = q_query.where(Question.id.in_(wrong_qids))
    elif body.subject_code:
        q_query = q_query.join(Subject, Question.subject_id == Subject.id).where(
            Subject.code == body.subject_code
        )

    q_query = q_query.order_by(func.random()).limit(questions_per_session)
    selected_qs = (await db.execute(q_query)).scalars().all()

    if len(selected_qs) < 1:
        raise AppException("范围内题目不足，无法开始训练", 400, "TRAIN-002")

    # 确定训练模式（基于五力画像）
    training_mode = profile.recommended_mode or "TRAIN_WEAKNESS"
    focus_power = profile.primary_weakness

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
        created_at=datetime.now(UTC),
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
        "questions": [
            {
                "question_id": q.id,
                "question_index": i,
                "stem": q.stem,
                "image_url": q.image_url,
                "difficulty": q.difficulty,
                "power_type": q.primary_power,
                "answer": q.answer,
            }
            for i, q in enumerate(selected_qs)
        ],
        "total_questions": len(selected_qs),
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

    # 简单判题（Mock）
    is_correct = True  # 实际需要对比答案

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
        generation_status="pending" if not is_correct else None,
        answered_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    db.add(record)

    # 答错：写入错题集
    if not is_correct:
        wrong = WrongAnswerRecord(
            id=str(uuid.uuid4()),
            student_id=student.id,
            question_id=body.question_id,
            source_module="training",
            source_session_id=body.session_id,
            student_answer=body.student_answer,
            review_status="unreview",
            created_at=datetime.now(UTC),
        )
        db.add(wrong)

    await db.commit()
    return ok_response({
        "answer_record_id": record.id,
        "is_correct": is_correct,
        "rag_status": "pending" if not is_correct else None,
        "proactive_trigger": False,
    })


@router.get("/rag-status/{answer_record_id}", summary="查询RAG生成状态")
async def get_rag_status(
    answer_record_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Mock: 固定返回 degraded（占位实现）"""
    record = (
        await db.execute(select(TrainingAnswerRecord).where(TrainingAnswerRecord.id == answer_record_id))
    ).scalar_one_or_none()
    if not record:
        raise AppException("答题记录不存在", 404)
    return ok_response({
        "rag_status": "degraded",
        "rag_content": None,
        "static_solution": "（AI解析功能尚未开通，请查阅参考资料）",
        "retry_count": 0,
        "can_retry": False,
    })


@router.post("/rag-retry", summary="重新生成RAG")
async def rag_retry(
    answer_record_id: int,
    student: Student = Depends(get_current_student),
):
    """Mock 占位"""
    return ok_response({"rag_status": "pending", "retry_count": 1, "can_retry": False})


@router.post("/complete", summary="完成训练会话")
async def complete_session(
    session_id: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
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

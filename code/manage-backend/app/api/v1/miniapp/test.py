"""小程序端五力认知测试模块 — §3"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.cognitive import CognitiveTestQuestion
from app.models.student import FivePowerProfile, Student, TestAnswerRecord, TestSession

router = APIRouter()


class SubmitAnswerReq(BaseModel):
    session_id: int
    question_id: int
    question_index: int
    selected_option: str | None = None
    time_spent_sec: int
    modify_count: int = 0


@router.get("/questions", summary="获取测试题卷")
async def get_test_questions(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """获取20道已发布五力测试题"""
    questions = (
        await db.execute(
            select(CognitiveTestQuestion)
            .where(CognitiveTestQuestion.status == "published")
            .order_by(CognitiveTestQuestion.question_no)
        )
    ).scalars().all()

    if len(questions) < 20:
        raise AppException("测试题目数量不足，暂无法开始测试", 503)

    # 检查是否有进行中的会话（72h内可恢复）
    active_session = (
        await db.execute(
            select(TestSession)
            .where(
                TestSession.student_id == student.id,
                TestSession.session_status == "in_progress",
            )
            .order_by(TestSession.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # 创建新会话
    session = TestSession(
        student_id=student.id,
        session_status="in_progress",
        config_snapshot={"version": "v1", "question_count": 20},
        is_retest=active_session is not None,
        current_question_index=0,
        started_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()
    await db.commit()

    return ok_response({
        "session_id": session.id,
        "questions": [
            {
                "id": q.id,
                "question_no": q.question_no,
                "stem": q.stem,
                "image_url": q.image_url,
                "answers": q.answers,
                "reference_time_sec": q.reference_time_sec,
            }
            for q in questions
        ],
        "total": len(questions),
    })


@router.post("/answer", summary="提交单题答案")
async def submit_answer(
    body: SubmitAnswerReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session = (
        await db.execute(
            select(TestSession).where(
                TestSession.id == body.session_id,
                TestSession.student_id == student.id,
                TestSession.session_status == "in_progress",
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise AppException("测试会话不存在或已结束", 404)

    record = TestAnswerRecord(
        session_id=body.session_id,
        question_id=body.question_id,
        question_index=body.question_index,
        selected_option=body.selected_option,
        time_spent_sec=body.time_spent_sec,
        modify_count=body.modify_count,
        is_rushed=body.time_spent_sec < 5,
        answered_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    db.add(record)
    session.current_question_index = body.question_index + 1
    await db.commit()
    return ok_response({"question_index": body.question_index, "recorded": True})


@router.post("/complete", summary="提交测试（触发评分）")
async def complete_test(
    session_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Mock评分：返回固定的评分结构"""
    session = (
        await db.execute(
            select(TestSession).where(
                TestSession.id == session_id,
                TestSession.student_id == student.id,
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise AppException("会话不存在", 404)

    session.session_status = "completed"
    session.submitted_at = datetime.now(UTC)

    # Mock 五力画像
    profile = FivePowerProfile(
        student_id=student.id,
        test_session_id=session.id,
        insight_ability=75, construct_ability=60, deduce_ability=70,
        adapt_ability=65, migrate_ability=55,
        insight_preference=25, construct_preference=20, deduce_preference=20,
        adapt_preference=20, migrate_preference=15,
        insight_final=72, construct_final=59, deduce_final=68,
        adapt_final=63, migrate_final=53,
        primary_weakness="MIGRATE", secondary_weakness="CONSTRUCT",
        primary_strength="INSIGHT", primary_entry="INSIGHT",
        recommended_mode="TRAIN_WEAKNESS", preferred_force="INSIGHT",
        is_latest=True,
        ai_analysis_status="pending",
        created_at=datetime.now(UTC),
    )
    # 标记旧画像非最新（update旧记录）
    from sqlalchemy import update as sa_update
    await db.execute(
        sa_update(FivePowerProfile)
        .where(FivePowerProfile.student_id == student.id, FivePowerProfile.is_latest == True)
        .values(is_latest=False)
    )
    db.add(profile)
    await db.commit()

    return ok_response({
        "profile_id": profile.id,
        "ai_analysis_status": "pending",
        "forces": {
            "INSIGHT":   {"ability": 75, "preference": 25, "final": 72},
            "CONSTRUCT": {"ability": 60, "preference": 20, "final": 59},
            "DEDUCE":    {"ability": 70, "preference": 20, "final": 68},
            "ADAPT":     {"ability": 65, "preference": 20, "final": 63},
            "MIGRATE":   {"ability": 55, "preference": 15, "final": 53},
        },
        "primary_weakness": "MIGRATE",
        "recommended_mode": "TRAIN_WEAKNESS",
    }, "测试完成，正在生成AI分析")


@router.get("/result/{profile_id}", summary="轮询测试结果（AI分析）")
async def get_test_result(
    profile_id: int = Path(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    profile = (
        await db.execute(
            select(FivePowerProfile).where(
                FivePowerProfile.id == profile_id,
                FivePowerProfile.student_id == student.id,
            )
        )
    ).scalar_one_or_none()
    if not profile:
        raise AppException("画像不存在", 404)

    return ok_response({
        "profile_id": profile.id,
        "ai_analysis_status": profile.ai_analysis_status,
        "ai_analysis_text": profile.ai_analysis_text or "（AI分析生成中，请稍候）",
    })


@router.get("/history", summary="历史测试记录")
async def get_test_history(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    profiles = (
        await db.execute(
            select(FivePowerProfile)
            .where(FivePowerProfile.student_id == student.id)
            .order_by(FivePowerProfile.created_at.desc())
            .limit(10)
        )
    ).scalars().all()

    return ok_response([
        {
            "profile_id": p.id,
            "created_at": p.created_at.isoformat(),
            "is_latest": p.is_latest,
            "forces": {
                "INSIGHT": p.insight_final, "CONSTRUCT": p.construct_final,
                "DEDUCE": p.deduce_final, "ADAPT": p.adapt_final, "MIGRATE": p.migrate_final,
            },
        }
        for p in profiles
    ])

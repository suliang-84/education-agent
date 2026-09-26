"""小程序端错题集模块 — §6"""
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.student import Student, WrongAnswerRecord
from app.models.question import Question
from app.models.ai import AiChatSession

router = APIRouter()


@router.get("", summary="获取错题列表")
async def list_wrong_answers(
    review_status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    q = select(WrongAnswerRecord, Question).join(
        Question, WrongAnswerRecord.question_id == Question.id
    ).where(WrongAnswerRecord.student_id == student.id)

    if review_status:
        q = q.where(WrongAnswerRecord.review_status == review_status)
    else:
        q = q.where(
            WrongAnswerRecord.review_status.in_(["unreview", "reviewing", "pending_consolidation"])
        )

    q = q.order_by(WrongAnswerRecord.created_at.desc()).limit(limit)
    rows = (await db.execute(q)).all()

    return ok_response({
        "list": [
            {
                "wrong_id": str(w.id),
                "question": {
                    "question_id": ques.id,
                    "stem": ques.stem[:100],
                    "difficulty": ques.difficulty,
                    "primary_power": ques.primary_power,
                },
                "student_answer": w.student_answer,
                "review_status": w.review_status,
                "created_at": w.created_at.isoformat(),
            }
            for w, ques in rows
        ],
        "total": len(rows),
    })


@router.post("/{wrong_id}/review", summary="发起AI复盘")
async def start_review(
    wrong_id: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    wrong = (
        await db.execute(
            select(WrongAnswerRecord).where(
                WrongAnswerRecord.id == wrong_id,
                WrongAnswerRecord.student_id == student.id,
            )
        )
    ).scalar_one_or_none()
    if not wrong:
        raise AppException("错题记录不存在", 404)

    question = (
        await db.execute(select(Question).where(Question.id == wrong.question_id))
    ).scalar_one_or_none()

    session_id = str(uuid.uuid4())
    chat_session = AiChatSession(
        id=session_id,
        student_id=student.id,
        session_mode="wrong_review",
        status="active",
        linked_question_id=wrong.question_id,
        linked_wrong_id=wrong_id,
        started_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    db.add(chat_session)

    wrong.review_status = "reviewing"
    wrong.reviewed_at = datetime.now(UTC)
    await db.commit()

    return ok_response({
        "chat_session_id": session_id,
        "session_mode": "wrong_review",
        "wrong_id": wrong_id,
        "question_info": {
            "stem": question.stem if question else "",
            "student_answer": wrong.student_answer,
            "primary_power": question.primary_power if question else None,
        },
        "opening_message": {
            "role": "assistant",
            "content": "我看到你之前在这道题上遇到了困难，我们一起来重新看看吧。你还记得当时是怎么想的吗？",
        },
    })

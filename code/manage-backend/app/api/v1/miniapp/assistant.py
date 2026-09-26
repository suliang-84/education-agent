"""小程序端AI助教模块 — §7（Mock占位）"""
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.ai import AiChatMessage, AiChatSession
from app.models.student import Student

router = APIRouter()


class CreateSessionReq(BaseModel):
    session_mode: str = "free_chat"  # free_chat / wrong_review / training_error_guidance
    linked_question_id: int | None = None
    linked_wrong_id: str | None = None


class SendMessageReq(BaseModel):
    session_id: str
    content: str


class RateMessageReq(BaseModel):
    rating: str  # like / dislike


@router.post("/session", summary="创建对话会话")
async def create_session(
    body: CreateSessionReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session_id = str(uuid.uuid4())
    session = AiChatSession(
        id=session_id,
        student_id=student.id,
        session_mode=body.session_mode,
        status="active",
        linked_question_id=body.linked_question_id,
        started_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    db.add(session)
    await db.commit()
    return ok_response({"session_id": session_id, "session_mode": body.session_mode})


@router.post("/message", summary="发送消息（Mock）")
async def send_message(
    body: SendMessageReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Mock: 返回固定AI回复"""
    # 存学生消息
    student_msg = AiChatMessage(
        session_id=body.session_id, role="student",
        content=body.content, created_at=datetime.now(UTC),
    )
    db.add(student_msg)
    await db.flush()

    # Mock AI回复
    ai_reply = "这是一个很好的思考方向！让我们一步一步来分析这道题..."
    ai_msg = AiChatMessage(
        session_id=body.session_id, role="assistant",
        content=ai_reply, created_at=datetime.now(UTC),
    )
    db.add(ai_msg)
    await db.commit()

    return ok_response({
        "message_id": ai_msg.id,
        "role": "assistant",
        "content": ai_reply,
        "is_aha_trigger": False,
        "proactive_trigger": False,
    })


@router.get("/messages", summary="获取历史消息")
async def get_messages(
    session_id: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    msgs = (
        await db.execute(
            select(AiChatMessage)
            .where(AiChatMessage.session_id == session_id)
            .order_by(AiChatMessage.created_at)
        )
    ).scalars().all()
    return ok_response([
        {"message_id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in msgs
    ])


@router.patch("/message/{message_id}/rating", summary="消息评分")
async def rate_message(
    message_id: int = Path(...),
    body: RateMessageReq = ...,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    msg = (await db.execute(select(AiChatMessage).where(AiChatMessage.id == message_id))).scalar_one_or_none()
    if not msg:
        raise AppException("消息不存在", 404)
    msg.student_rating = body.rating
    await db.commit()
    return ok_response(None, "评分已记录")


@router.post("/session/{session_id}/end", summary="结束对话会话")
async def end_session(
    session_id: str = Path(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session = (
        await db.execute(select(AiChatSession).where(AiChatSession.id == session_id, AiChatSession.student_id == student.id))
    ).scalar_one_or_none()
    if not session:
        raise AppException("会话不存在", 404)
    session.status = "completed"
    session.ended_at = datetime.now(UTC)
    session.session_summary = "（AI摘要生成中）"
    await db.commit()
    return ok_response(None, "会话已结束")


@router.get("/sessions", summary="获取会话列表")
async def list_sessions(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    sessions = (
        await db.execute(
            select(AiChatSession)
            .where(AiChatSession.student_id == student.id)
            .order_by(AiChatSession.created_at.desc())
            .limit(20)
        )
    ).scalars().all()
    return ok_response([
        {
            "session_id": s.id,
            "session_mode": s.session_mode,
            "status": s.status,
            "aha_count": s.aha_count,
            "session_summary": s.session_summary,
            "started_at": s.started_at.isoformat(),
        }
        for s in sessions
    ])

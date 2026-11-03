"""小程序端 AI 助教模块 — §7

单一永久会话（free_chat）：进入助教页就是同一个会话，历史自动加载，没有「新对话 / 结束对话」。
启发策略、理解突破、沉默模式、重新生成、评分、滚动摘要、快捷问题、图片提问等逻辑见 app/services/assistant。
"""
import base64
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.student import Student
from app.services.assistant import core, service

router = APIRouter()


class SendMessageReq(BaseModel):
    session_id: str
    content: str = ""                 # 有图片时可以为空
    image_url: str | None = None      # POST /assistant/image 返回的图片地址


class RateMessageReq(BaseModel):
    rating: str  # like / dislike


class ImageReq(BaseModel):
    image_base64: str
    media_type: str = "image/jpeg"   # 仅供参考，服务端按文件头判断真实类型


@router.post("/session", summary="获取或创建永久会话")
async def get_session(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    s, created = await service.get_or_create_session(db, student)
    silent = core.silence_active(s.silence_mode, s.silence_triggered_at, datetime.now(UTC), await service._timeout_min(db))
    return ok_response({"session_id": s.id, "session_mode": s.session_mode, "is_new": created, "silence": silent})


@router.get("/messages", summary="获取历史消息（分页，向上翻页）")
async def get_messages(
    session_id: str,
    before_id: int | None = Query(None, description="取这条消息之前更早的消息；不传取最新一页"),
    limit: int = Query(30, ge=1, le=50),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    await service.get_session_of(db, student, session_id)
    items, has_more = await service.page_messages(db, session_id, before_id, limit)
    return ok_response({"messages": items, "has_more": has_more})


@router.post("/message", summary="发送消息")
async def send_message(
    body: SendMessageReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session = await service.get_session_of(db, student, body.session_id)
    return ok_response(await service.send_message(db, student, session, body.content, body.image_url))


@router.post("/message/{message_id}/regenerate", summary="重新生成这条 AI 回复（换一种启发策略）")
async def regenerate_message(
    message_id: int = Path(...),
    session_id: str = Query(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session = await service.get_session_of(db, student, session_id)
    return ok_response(await service.regenerate(db, student, session, message_id))


# 小程序端 wx.request 不支持 PATCH，用 PUT 发送，两种方法都接受
@router.api_route("/message/{message_id}/rating", methods=["PATCH", "PUT"], summary="消息评分（点赞 / 点踩）")
async def rate_message(
    body: RateMessageReq,
    message_id: int = Path(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    await service.rate(db, student, message_id, body.rating)
    return ok_response(None, "评分已记录")


@router.post("/silence/resume", summary="恢复 AI 引导（解除沉默模式）")
async def resume_silence(
    session_id: str = Query(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session = await service.get_session_of(db, student, session_id)
    session.silence_mode = False
    await db.commit()
    return ok_response({"silence": False})


@router.get("/suggestions", summary="快捷提问（按学生情况生成）")
async def get_suggestions(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    return ok_response({"suggestions": await service.suggestions(db, student)})


@router.post("/image", summary="上传图片（图片提问：随消息一起发给 AI 助教）")
async def upload_image(
    body: ImageReq,
    student: Student = Depends(get_current_student),
):
    """图片只保存、不解析：学生在输入框里附上问题后，图片和问题一起通过 POST /message 发给 AI 助教，由助教回答"""
    try:
        raw = base64.b64decode(body.image_base64, validate=True)
    except Exception:
        raise AppException("图片数据无效", 400, "ASST-006")
    if len(raw) > 6 * 1024 * 1024:
        raise AppException("图片不能超过 6MB", 400, "ASST-006")
    kind = core.sniff_image_type(raw)
    if not kind:
        raise AppException("仅支持 JPG / PNG / WEBP 图片", 400, "ASST-006")
    name = f"{uuid.uuid4().hex}.{kind[1]}"
    (service.UPLOAD_ROOT / "assistant").mkdir(parents=True, exist_ok=True)
    (service.UPLOAD_ROOT / "assistant" / name).write_bytes(raw)
    return ok_response({"image_url": f"/uploads/assistant/{name}"})

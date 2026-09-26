"""小程序端认证模块 — §2"""
import hashlib
import secrets
import string
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.redis import get_redis
from app.core.response import ok_response
from app.core.security import (
    create_student_access_token,
    create_student_refresh_token,
    decode_student_token,
)
from app.dependencies import get_current_student, security
from app.models.student import InviteCode, ParentStudentBinding, SmsCode, Student

router = APIRouter()
settings = get_settings()

DEV_SMS_CODE = "123456"  # 开发阶段固定验证码


# ── Schemas ──────────────────────────────────────────────────────────────

class WxLoginReq(BaseModel):
    code: str
    nickname: str | None = None
    avatar_url: str | None = None


class BindPhoneReq(BaseModel):
    phone: str = Field(..., pattern=r"^\d{11}$")
    sms_code: str
    grade: str | None = None
    semester: str | None = None  # S1 / S2


class SendSmsReq(BaseModel):
    phone: str = Field(..., pattern=r"^\d{11}$")
    purpose: str  # BIND_PHONE / LOGIN / PARENT_BIND


class RefreshTokenReq(BaseModel):
    refresh_token: str


class InviteCodeUseReq(BaseModel):
    invite_code: str


class ParentBindRequestReq(BaseModel):
    student_phone: str = Field(..., pattern=r"^\d{11}$")


class ConfirmBindReq(BaseModel):
    binding_id: int
    action: str  # accept / reject


# ── Helpers ──────────────────────────────────────────────────────────────

def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _mask_phone(phone: str) -> str:
    return phone[:3] + "****" + phone[-4:]


async def _get_wx_openid(code: str) -> tuple[str, str]:
    """调用微信 jscode2session 获取 openid 和 session_key"""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WX_APPID,
        "secret": settings.WX_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
    data = resp.json()
    if "errcode" in data and data["errcode"] != 0:
        raise AppException(f"微信登录失败: {data.get('errmsg', '未知错误')}", 400)
    return data["openid"], data.get("session_key", "")


def _build_token_resp(student: Student) -> dict:
    access_token = create_student_access_token(student.id, student.user_type)
    refresh_token = create_student_refresh_token(student.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_expires_in": 7 * 24 * 3600,
        "user_info": {
            "student_id": student.id,
            "nickname": student.nickname,
            "grade": student.grade,
            "semester": student.semester,
            "has_five_power_profile": False,  # 后续查询补充
        },
    }


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/wx-login", summary="微信登录（学生/家长）")
async def wx_login(body: WxLoginReq, db: AsyncSession = Depends(get_db)):
    openid, _ = await _get_wx_openid(body.code)
    openid_hash = _hash(openid)

    result = await db.execute(select(Student).where(Student.openid_hash == openid_hash))
    student = result.scalar_one_or_none()

    if student:
        # 已注册：更新登录时间，返回 token
        student.last_login_at = datetime.now(UTC)
        if body.nickname:
            student.nickname = body.nickname
        if body.avatar_url:
            student.avatar_url = body.avatar_url
        await db.commit()

        resp = _build_token_resp(student)
        # 检查是否有五力画像
        from app.models.student import FivePowerProfile
        has_profile = (
            await db.execute(
                select(FivePowerProfile.id)
                .where(FivePowerProfile.student_id == student.id, FivePowerProfile.is_latest == True)
            )
        ).scalar_one_or_none() is not None
        resp["user_info"]["has_five_power_profile"] = has_profile
        return ok_response(resp, "登录成功")
    else:
        # 新用户：返回 temp_token，引导绑定手机号
        temp_token = create_student_access_token(-1, "TEMP")  # sub=-1 标记临时
        # 临时存储 openid（Redis 5min）
        redis = await get_redis()
        await redis.setex(f"temp_openid:{temp_token[:32]}", 300, openid)
        return ok_response(
            {
                "temp_token": temp_token,
                "is_new_user": True,
                "nickname": body.nickname or "",
                "avatar_url": body.avatar_url or "",
            },
            "新用户，请绑定手机号",
        )


@router.post("/sms/send", summary="发送短信验证码")
async def send_sms(body: SendSmsReq, db: AsyncSession = Depends(get_db)):
    """开发阶段：固定验证码 123456，不实际发送短信"""
    phone_hash = _hash(body.phone)

    # 写入验证码记录
    sms = SmsCode(
        phone_hash=phone_hash,
        code=DEV_SMS_CODE,
        purpose=body.purpose,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        created_at=datetime.now(UTC),
    )
    db.add(sms)
    await db.commit()
    return ok_response({"expire_seconds": 300}, "验证码已发送（开发模式：123456）")


@router.post("/bind-phone-with-token", summary="绑定手机号（新用户完成注册）")
async def bind_phone_impl(
    body: BindPhoneReq,
    credentials=Depends(security),
    db: AsyncSession = Depends(get_db),
):
    import jwt as _jwt
    try:
        payload = decode_student_token(credentials.credentials)
    except _jwt.PyJWTError:
        raise AppException("temp_token 无效", 401)

    # 验证短信码
    phone_hash = _hash(body.phone)
    sms_result = await db.execute(
        select(SmsCode)
        .where(
            SmsCode.phone_hash == phone_hash,
            SmsCode.purpose == "BIND_PHONE",
            SmsCode.is_used == False,
            SmsCode.expires_at > datetime.now(UTC),
        )
        .order_by(SmsCode.created_at.desc())
        .limit(1)
    )
    sms = sms_result.scalar_one_or_none()
    if not sms or sms.code != body.sms_code:
        raise AppException("验证码错误或已过期", 400)

    # 获取 openid（从 Redis 或 payload）
    redis = await get_redis()
    token_key = credentials.credentials[:32]
    openid = await redis.get(f"temp_openid:{token_key}")
    if not openid:
        raise AppException("注册会话已过期，请重新登录微信", 400)
    if isinstance(openid, bytes):
        openid = openid.decode()

    openid_hash = _hash(openid)

    # 检查手机号是否已注册
    existing = await db.execute(
        select(Student).where(Student.phone_hash == phone_hash, Student.deleted_at == None)
    )
    if existing.scalar_one_or_none():
        raise AppException("该手机号已注册", 409)

    # 创建学生账号
    student = Student(
        user_type="STUDENT",
        openid=openid,
        openid_hash=openid_hash,
        phone=body.phone,  # 生产环境应加密
        phone_masked=_mask_phone(body.phone),
        phone_hash=phone_hash,
        grade=body.grade,
        semester=body.semester,
        is_minor=True,
        is_active=True,
        is_confirmed=True,
        last_login_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(student)
    await db.flush()

    # 标记验证码已使用
    sms.is_used = True
    await db.commit()
    await redis.delete(f"temp_openid:{token_key}")

    return ok_response(_build_token_resp(student), "注册成功")


@router.post("/token/refresh", summary="刷新 Token")
async def refresh_token(body: RefreshTokenReq, db: AsyncSession = Depends(get_db)):
    import jwt as _jwt
    try:
        payload = decode_student_token(body.refresh_token)
    except _jwt.ExpiredSignatureError:
        raise AppException("refresh_token 已过期", 401)
    except _jwt.PyJWTError:
        raise AppException("refresh_token 无效", 401)

    if payload.get("token_type") != "refresh":
        raise AppException("请传入 refresh_token", 400)

    # 检查黑名单
    redis = await get_redis()
    jti = payload.get("jti", "")
    if await redis.get(f"blacklist:{jti}"):
        raise AppException("Token 已撤销", 401)

    student_id = int(payload["sub"])
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student or not student.is_active:
        raise AppException("账号不存在或已停用", 401)

    # 旧 refresh_token 加黑名单
    remaining = int(payload["exp"] - datetime.now(UTC).timestamp())
    if remaining > 0:
        await redis.setex(f"blacklist:{jti}", remaining, "1")

    access_token = create_student_access_token(student.id, student.user_type)
    new_refresh = create_student_refresh_token(student.id)
    return ok_response(
        {"access_token": access_token, "refresh_token": new_refresh, "access_expires_in": 7 * 24 * 3600}
    )


@router.post("/logout", summary="退出登录")
async def logout(credentials=Depends(security)):
    import jwt as _jwt
    try:
        payload = decode_student_token(credentials.credentials)
        jti = payload.get("jti", "")
        remaining = int(payload.get("exp", 0) - datetime.now(UTC).timestamp())
        if jti and remaining > 0:
            redis = await get_redis()
            await redis.setex(f"blacklist:{jti}", remaining, "1")
    except _jwt.PyJWTError:
        pass
    return ok_response(None, "已退出")


@router.post("/invite-code", summary="生成家长邀请码")
async def generate_invite_code(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    # 作废旧码
    await db.execute(
        update(InviteCode)
        .where(InviteCode.student_id == student.id, InviteCode.is_used == False)
        .values(is_used=True)
    )
    # 生成新码
    alphabet = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(alphabet) for _ in range(8))
    expires_at = datetime.now(UTC) + timedelta(hours=48)
    invite = InviteCode(
        student_id=student.id,
        code=code,
        expires_at=expires_at,
        is_used=False,
        created_at=datetime.now(UTC),
    )
    db.add(invite)
    await db.commit()
    return ok_response({"code": code, "expire_at": expires_at.isoformat(), "expire_hours": 48})

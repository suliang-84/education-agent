import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.admin import AdminUser

security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise AppException("Token 已过期，请重新登录", 401)
    except jwt.PyJWTError:
        raise AppException("Token 无效，请重新登录", 401)

    # 检查 Redis 黑名单
    redis = await get_redis()
    jti = payload.get("jti", "")
    if await redis.get(f"blacklist:{jti}"):
        raise AppException("Token 已撤销，请重新登录", 401)

    # 检查角色
    if payload.get("role") != "SUPER_ADMIN":
        raise AppException("权限不足", 403)

    # 查询管理员
    admin_id = int(payload["sub"])
    result = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin:
        raise AppException("管理员不存在", 401)
    if admin.is_active == 0:
        raise AppException("账号已停用", 403)

    return admin

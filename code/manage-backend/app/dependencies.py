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

VALID_ROLES = {"SUPER_ADMIN", "ADMIN"}


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """允许所有有效管理员角色（SUPER_ADMIN / ADMIN）访问。"""
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

    # 检查角色是否合法
    if payload.get("role") not in VALID_ROLES:
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


async def require_super_admin(
    current_admin: AdminUser = Depends(get_current_admin),
) -> AdminUser:
    """仅允许 SUPER_ADMIN 访问。"""
    if current_admin.role != "SUPER_ADMIN":
        raise AppException("该操作仅超级管理员可执行", 403)
    return current_admin

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.redis import get_redis
from app.core.security import create_access_token, decode_token, verify_password
from app.models.admin import AdminUser

MAX_FAIL_COUNT = 5
LOCK_MINUTES = 30


async def login(db: AsyncSession, username: str, password: str, ip: str) -> tuple[str, AdminUser]:
    """
    验证管理员账号密码，返回 (access_token, admin)。
    失败时抛出 AppException。
    """
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    admin = result.scalar_one_or_none()

    if not admin:
        raise AppException("LOGIN-001", "账号或密码错误", 401)

    # 检查锁定
    if admin.locked_until and admin.locked_until > datetime.now(UTC):
        raise AppException("LOGIN-002", f"账号已锁定，请{LOCK_MINUTES}分钟后重试", 403)

    # 检查账号状态
    if admin.is_active == 0:
        raise AppException("AUTH-003", "账号已停用，请联系管理员", 403)

    if admin.is_active == 2:
        raise AppException("LOGIN-003", "首次登录请先修改初始密码", 403)

    # 验证密码
    if not verify_password(password, admin.password_hash):
        new_fail = admin.login_fail_count + 1
        update_vals: dict = {"login_fail_count": new_fail}
        if new_fail >= MAX_FAIL_COUNT:
            update_vals["locked_until"] = datetime.now(UTC) + timedelta(minutes=LOCK_MINUTES)
            update_vals["login_fail_count"] = 0
            await db.execute(
                update(AdminUser).where(AdminUser.id == admin.id).values(**update_vals)
            )
            await db.commit()
            raise AppException("LOGIN-002", f"密码错误次数过多，账号已锁定{LOCK_MINUTES}分钟", 403)
        remaining = MAX_FAIL_COUNT - new_fail
        await db.execute(update(AdminUser).where(AdminUser.id == admin.id).values(**update_vals))
        await db.commit()
        raise AppException("LOGIN-001", f"账号或密码错误，还可尝试{remaining}次", 401)

    # 登录成功：重置失败次数，更新 last_login
    await db.execute(
        update(AdminUser)
        .where(AdminUser.id == admin.id)
        .values(
            login_fail_count=0,
            locked_until=None,
            last_login_at=datetime.now(UTC),
            last_login_ip=ip,
        )
    )
    await db.commit()
    await db.refresh(admin)

    token = create_access_token(admin.id, admin.username, admin.role)
    return token, admin


async def logout(token: str) -> None:
    """将 token 加入 Redis 黑名单"""
    try:
        payload = decode_token(token)
        jti = payload["jti"]
        exp = payload["exp"]
        ttl = max(0, exp - int(datetime.now(UTC).timestamp()))
        redis = await get_redis()
        if ttl > 0:
            await redis.set(f"blacklist:{jti}", "revoked", ex=ttl)
    except Exception:
        pass  # token 本身无效，忽略

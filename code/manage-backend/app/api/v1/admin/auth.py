from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.response import ok_response
from app.dependencies import get_current_admin, get_db
from app.models.admin import AdminUser
from app.schemas.auth import AdminInfo, LoginReq, TokenResp
from app.services import audit_service, auth_service

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=None, summary="管理员登录")
async def login(
    body: LoginReq,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    token, admin = await auth_service.login(db, body.username, body.password, ip)

    # 写审计日志
    await audit_service.log(
        db,
        admin.id,
        admin.display_name,
        "ADMIN_LOGIN",
        "admin_users",
        str(admin.id),
        ip_address=ip,
    )
    await db.commit()

    return ok_response(
        TokenResp(
            access_token=token,
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            admin=AdminInfo(
                id=admin.id,
                username=admin.username,
                display_name=admin.display_name,
                role=admin.role,
            ),
        ).model_dump(),
        "登录成功",
    )


@router.post("/logout", summary="退出登录")
async def logout(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # 从 Header 取 token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    await auth_service.logout(token)

    await audit_service.log(
        db,
        current_admin.id,
        current_admin.display_name,
        "ADMIN_LOGOUT",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return ok_response(None, "已退出登录")

"""审计日志路由 — §9.9"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import ok_response
from app.dependencies import get_current_admin, get_db
from app.models.admin import AdminUser
from app.models.audit import AdminAuditLog

router = APIRouter()


@router.get("/audit-logs", summary="审计日志列表")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    权限规则：
    - SUPER_ADMIN：可查看所有管理员的操作记录
    - ADMIN：只能查看非 SUPER_ADMIN 角色的管理员操作记录（即其他普通管理员及自身）
    """
    offset = (page - 1) * limit

    # 构建基础查询：JOIN admin_users 获取操作人姓名和角色
    base_join = (
        select(AdminAuditLog, AdminUser.display_name, AdminUser.role)
        .join(AdminUser, AdminAuditLog.admin_id == AdminUser.id, isouter=True)
    )

    if current_admin.role == "SUPER_ADMIN":
        # 超级管理员：查看全部
        count_q = select(func.count()).select_from(AdminAuditLog)
        data_q = base_join.order_by(desc(AdminAuditLog.created_at)).offset(offset).limit(limit)
    else:
        # 普通管理员：排除 SUPER_ADMIN 的操作记录
        non_super_ids = select(AdminUser.id).where(AdminUser.role != "SUPER_ADMIN")
        count_q = (
            select(func.count())
            .select_from(AdminAuditLog)
            .where(AdminAuditLog.admin_id.in_(non_super_ids))
        )
        data_q = (
            base_join
            .where(AdminAuditLog.admin_id.in_(non_super_ids))
            .order_by(desc(AdminAuditLog.created_at))
            .offset(offset)
            .limit(limit)
        )

    total = (await db.execute(count_q)).scalar_one()
    rows = (await db.execute(data_q)).all()

    items = [
        {
            "id": log.id,
            "admin_id": log.admin_id,
            "admin_name": display_name or f"ID:{log.admin_id}",
            "admin_role": role,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
        }
        for log, display_name, role in rows
    ]

    return ok_response({
        "list": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": max(1, (total + limit - 1) // limit),
    })

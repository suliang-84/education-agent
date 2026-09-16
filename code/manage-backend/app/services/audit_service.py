from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AdminAuditLog


async def log(
    db: AsyncSession,
    admin_id: int,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
) -> None:
    entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address or "unknown",
    )
    db.add(entry)
    # 不 commit，由调用方统一 commit

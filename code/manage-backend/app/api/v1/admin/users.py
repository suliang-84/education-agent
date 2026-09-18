"""用户管理路由模块 — §9.8"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import ok_response
from app.dependencies import get_current_admin, get_db
from app.models.admin import AdminUser
from app.schemas.users import (
    BindParentReq,
    UnbindParentReq,
    UnbindStudentReq,
    CreateAdminReq,
    SetAdminStatusReq,
    AddInsightEntryReq,
    UpdatePersonalInsightReq,
)
from app.services import audit_service, users_service

router = APIRouter()


# ── 学生管理 ─────────────────────────────────────────────────

@router.get("/students", summary="学生列表")
async def list_students(
    grade: str | None = Query(None),
    has_profile: str | None = Query(None),   # 前端传 'true'/'false'/'' 字符串
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    # 空字符串或 None 均视为不筛选
    has_profile_bool: bool | None = None
    if has_profile == 'true':
        has_profile_bool = True
    elif has_profile == 'false':
        has_profile_bool = False

    data = await users_service.get_student_list(
        db, grade=grade or None, has_profile=has_profile_bool, keyword=keyword or None,
        page=page, limit=limit,
    )
    return ok_response(data)


@router.post("/students/{student_id}/bind-parent", summary="管理员绑定家长到学生")
async def bind_parent(
    student_id: int,
    body: BindParentReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    binding, parent, parent_created = await users_service.bind_parent(
        db, student_id, body.parent_phone, current_admin.id,
    )
    await audit_service.log(
        db, current_admin.id, "BIND_PARENT",
        target_type="parent_student_bindings", target_id=str(binding.id),
    )
    await db.commit()
    return ok_response(
        {"binding_id": binding.id, "parent_id": parent.id, "parent_created": parent_created},
        "已创建家长账号并完成绑定" if parent_created else "绑定成功",
    )


@router.post("/students/{student_id}/unbind-parent", summary="从学生侧解绑家长")
async def unbind_parent_from_student(
    student_id: int,
    body: UnbindParentReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await users_service.unbind_parent_from_student(db, student_id, body.parent_id)
    await audit_service.log(
        db, current_admin.id, "UNBIND_PARENT",
        target_type="parent_student_bindings",
    )
    await db.commit()
    return ok_response(None, "解绑成功")


@router.get("/students/{student_id}/kp-stats", summary="学生知识点练习统计")
async def get_kp_stats(
    student_id: int,
    subject_code: str | None = Query(None),
    only_valid: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    data = await users_service.get_kp_stats(db, student_id, subject_code=subject_code, only_valid=only_valid)
    return ok_response(data)


@router.get("/students/{student_id}/ai-prompt-summary", summary="获取AI助教提示词摘要")
async def get_ai_prompt_summary(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    data = await users_service.get_ai_prompt_summary(db, student_id)
    return ok_response(data)


@router.put("/students/{student_id}/ai-prompt-summary", summary="编辑个人洞察摘要")
async def update_ai_prompt_summary(
    student_id: int,
    body: UpdatePersonalInsightReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    result = await users_service.update_personal_insight(db, student_id, body.personal_insight)
    await audit_service.log(db, current_admin.id, "UPDATE_PERSONAL_INSIGHT",
                            target_type="student_ai_prompt_summaries", target_id=str(student_id))
    await db.commit()
    return ok_response(result, "个人洞察摘要已更新")


@router.post("/students/{student_id}/prompt-insights", summary="新增洞察条目")
async def add_insight_entry(
    student_id: int,
    body: AddInsightEntryReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    entry = await users_service.add_insight_entry(db, student_id, body, current_admin.id)
    await audit_service.log(db, current_admin.id, "ADD_INSIGHT_ENTRY",
                            target_type="student_prompt_insights", target_id=str(entry.id))
    await db.commit()
    return ok_response({"insight_id": entry.id, "created_at": entry.created_at}, "洞察条目已添加")


@router.get("/students/{student_id}/prompt-insights", summary="获取洞察条目列表")
async def get_insight_entries(
    student_id: int,
    only_active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    entries = await users_service.get_insight_entries(db, student_id, only_active=only_active)
    return ok_response([
        {
            "id": e.id,
            "content": e.content,
            "insight_type": e.insight_type,
            "source": e.source,
            "is_sensitive": e.is_sensitive,
            "weight": float(e.weight),
            "is_active": e.is_active,
            "created_at": e.created_at,
        }
        for e in entries
    ])


@router.post("/students/{student_id}/ai-prompt-summary/regenerate", summary="重新生成学习信息摘要")
async def regenerate_learning_summary(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    result = await users_service.regenerate_learning_summary(db, student_id)
    await audit_service.log(db, current_admin.id, "REGENERATE_LEARNING_SUMMARY",
                            target_type="student_ai_prompt_summaries", target_id=str(student_id))
    await db.commit()
    return ok_response(result, "学习信息摘要已重新生成")


# ── 家长管理 ─────────────────────────────────────────────────

@router.get("/parents", summary="家长列表")
async def list_parents(
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    data = await users_service.get_parent_list(db, keyword=keyword, page=page, limit=limit)
    return ok_response(data)


@router.post("/parents/{parent_id}/unbind", summary="从家长侧解绑学生")
async def unbind_student_from_parent(
    parent_id: int,
    body: UnbindStudentReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await users_service.unbind_student_from_parent(db, parent_id, body.student_id)
    await audit_service.log(db, current_admin.id, "UNBIND_PARENT",
                            target_type="parent_student_bindings")
    await db.commit()
    return ok_response(None, "解绑成功")


# ── 管理员账号管理 ───────────────────────────────────────────

@router.get("/admin-users", summary="管理员账号列表")
async def list_admin_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    data = await users_service.get_admin_list(db, page=page, limit=limit)
    items = [
        {
            "id": a.id,
            "username": a.username,
            "display_name": a.display_name,
            "role": a.role,
            "is_active": a.is_active,
            "last_login_at": a.last_login_at,
            "created_at": a.created_at,
        }
        for a in data["list"]
    ]
    return ok_response({**data, "list": items})


@router.post("/admin-users", summary="创建管理员账号")
async def create_admin_user(
    body: CreateAdminReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    admin = await users_service.create_admin(db, body, current_admin.id)
    await audit_service.log(db, current_admin.id, "CREATE_ADMIN",
                            target_type="admin_users", target_id=str(admin.id))
    await db.commit()
    return ok_response({"id": admin.id, "username": admin.username}, "管理员账号已创建")


@router.put("/admin-users/{admin_id}/status", summary="启用/停用管理员账号")
async def set_admin_status(
    admin_id: int,
    body: SetAdminStatusReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await users_service.set_admin_status(db, admin_id, body.is_active, current_admin.id)
    await audit_service.log(db, current_admin.id, "SET_ADMIN_STATUS",
                            target_type="admin_users", target_id=str(admin_id))
    await db.commit()
    return ok_response(None, "账号状态已更新")


@router.post("/admin-users/{admin_id}/reset-password", summary="重置管理员密码")
async def reset_admin_password(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await users_service.reset_admin_password(db, admin_id)
    await audit_service.log(db, current_admin.id, "RESET_ADMIN_PASSWORD",
                            target_type="admin_users", target_id=str(admin_id))
    await db.commit()
    return ok_response(None, "密码已重置为 123456")

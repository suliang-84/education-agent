"""训练配置路由：各训练方式的出题参数、智能训练算法参数、题目分析（大模型）并发与超时"""
from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import ok_response
from app.dependencies import get_current_admin, get_db
from app.models.admin import AdminUser
from app.services import training_config_service as svc

router = APIRouter()


@router.get("/training-configs", summary="获取各训练方式的配置")
async def list_training_configs(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    data = await svc.list_configs(db)
    data["analysis"] = await svc.get_analysis_config(db)
    return ok_response(data)


@router.put("/training-configs/{dimension}", summary="保存某个训练方式的配置")
async def update_training_config(
    dimension: str,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    data = await svc.update_config(db, dimension, body, admin.id)
    await db.commit()
    return ok_response(data, "已保存，学生下一次开始训练时生效")


@router.put("/analysis-config", summary="保存题目分析（大模型）配置")
async def update_analysis_config(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    data = await svc.update_analysis_config(db, body, admin.id)
    await db.commit()
    return ok_response(data, "已保存，新触发的分析按新设置执行")


@router.get("/profile-config", summary="获取学生画像配置（预警规则、学习投入度权重）")
async def get_profile_config(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    from app.services import profile_config
    return ok_response(await profile_config.get_config_view(db))


@router.put("/profile-config/rules", summary="保存画像预警规则")
async def save_profile_rules(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    from app.services import profile_config
    data = await profile_config.save_rules(db, body, admin.id)
    await db.commit()
    return ok_response(data, "已保存，管理员下次打开学生画像页时按新规则计算")


@router.put("/profile-config/weights", summary="保存学习投入度权重")
async def save_profile_weights(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    from app.services import profile_config
    data = await profile_config.save_weights(db, body, admin.id)
    await db.commit()
    return ok_response(data, "已保存")

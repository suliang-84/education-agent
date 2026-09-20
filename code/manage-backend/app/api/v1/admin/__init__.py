from fastapi import APIRouter

from app.api.v1.admin.auth import router as auth_router
from app.api.v1.admin.users import router as users_router
from app.api.v1.admin.cognitive import router as cognitive_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(users_router, tags=["用户管理"])
router.include_router(cognitive_router, tags=["五力测试题"])

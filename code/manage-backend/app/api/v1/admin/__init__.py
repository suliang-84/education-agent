from fastapi import APIRouter

from app.api.v1.admin.auth import router as auth_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["认证"])

# 后续 Task 逐步添加其他路由：
# from app.api.v1.admin.questions import router as questions_router
# router.include_router(questions_router, prefix="/questions", tags=["题库管理"])

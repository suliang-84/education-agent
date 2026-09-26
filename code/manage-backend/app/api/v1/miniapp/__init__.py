from fastapi import APIRouter
from app.api.v1.miniapp import auth, profile, test, training, wrong_answers, assistant, knowledge

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["小程序-认证"])
router.include_router(profile.router, prefix="/profile", tags=["小程序-个人信息"])
router.include_router(test.router, prefix="/test", tags=["小程序-五力测试"])
router.include_router(training.router, prefix="/training", tags=["小程序-训练"])
router.include_router(wrong_answers.router, prefix="/wrong-answers", tags=["小程序-错题集"])
router.include_router(assistant.router, prefix="/assistant", tags=["小程序-AI助教"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["小程序-知识点导航"])

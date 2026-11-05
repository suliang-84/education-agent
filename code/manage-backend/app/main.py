import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import AppException, app_exception_handler, generic_exception_handler
from app.core.logger import setup_logger
from app.core.middleware import RequestLogMiddleware
from app.core.redis import close_redis, get_redis

settings = get_settings()


WARNING_SCAN_DELAY_SEC = 60            # 启动后等一会儿再首次扫描，避免拖慢启动
WARNING_SCAN_INTERVAL_SEC = 6 * 3600   # 之后每 6 小时扫描一次全部学生的画像预警


async def _warning_scan_loop():
    """后台定时刷新全部学生的画像预警（学生列表的预警标记靠它保持最新）；出错只记日志，不影响服务"""
    from loguru import logger

    from app.core.database import AsyncSessionLocal
    from app.services import profile_warning_service

    await asyncio.sleep(WARNING_SCAN_DELAY_SEC)
    while True:
        try:
            async with AsyncSessionLocal() as db:
                logger.info("画像预警扫描完成：{}", await profile_warning_service.scan_all(db))
        except asyncio.CancelledError:
            raise
        except Exception:   # noqa: BLE001
            logger.exception("画像预警扫描失败")
        await asyncio.sleep(WARNING_SCAN_INTERVAL_SEC)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    await get_redis()  # 预热连接
    scan_task = asyncio.create_task(_warning_scan_loop())
    yield
    scan_task.cancel()
    await close_redis()


app = FastAPI(
    title="MESH Admin Backend",
    description="MESH AI助教平台后台管理系统",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
app.add_middleware(RequestLogMiddleware)

# 异常处理器
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": exc.detail, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # 取第一条错误的中文化提示
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first.get("loc", [])[1:])
    msg = f"参数错误：{field} — {first.get('msg', '')}" if field else "请求参数错误"
    return JSONResponse(
        status_code=422,
        content={"code": 422, "msg": msg, "data": None},
    )

# 注册路由
from app.api.v1.admin import router as admin_router  # noqa: E402
from app.api.v1.miniapp import router as miniapp_router  # noqa: E402

# 用户上传的文件（AI 助教图片提问）：文件名是随机 UUID，不可枚举；目录已被 .gitignore 忽略
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
(UPLOAD_DIR / "assistant").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(admin_router, prefix="/api/v1/admin")
app.include_router(miniapp_router, prefix="/api/v1")


@app.get("/health", tags=["健康检查"])
async def health():
    from app.core.response import ok

    return ok({"status": "healthy"})

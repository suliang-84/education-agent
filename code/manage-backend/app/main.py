from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import AppException, app_exception_handler, generic_exception_handler
from app.core.logger import setup_logger
from app.core.middleware import RequestLogMiddleware
from app.core.redis import close_redis, get_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    await get_redis()  # 预热连接
    yield
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

app.include_router(admin_router, prefix="/api/v1/admin")


@app.get("/health", tags=["健康检查"])
async def health():
    from app.core.response import ok

    return ok({"status": "healthy"})

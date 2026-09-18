from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.response import error, fail


class AppException(Exception):
    def __init__(self, msg: str, http_status: int = 400, code: str | None = None):
        self.msg = msg
        self.http_status = http_status
        # code 字段保留供内部日志追踪，不再透传给客户端
        self.code = code
        super().__init__(msg)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=fail(exc.http_status, exc.msg),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    from app.core.config import get_settings
    settings = get_settings()
    msg = str(exc) if settings.APP_DEBUG else "服务器内部错误，请稍后重试"
    return JSONResponse(status_code=500, content=error(msg))

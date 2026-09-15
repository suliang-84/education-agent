from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.response import error, fail


class AppException(Exception):
    def __init__(self, code: str, msg: str, http_status: int = 400):
        self.code = code
        self.msg = msg
        self.http_status = http_status
        super().__init__(msg)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=fail(exc.code, exc.msg),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=error(str(exc)))

from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None, msg: str = "操作成功") -> dict:
    return {"status": "success", "code": 0, "msg": msg, "data": data}


def fail(code: str, msg: str) -> dict:
    return {"status": "fail", "code": code, "msg": msg, "data": None}


def error(msg: str = "系统错误") -> dict:
    return {"status": "error", "code": "SYS-000", "msg": msg, "data": None}


def ok_response(data: Any = None, msg: str = "操作成功", status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ok(data, msg))


def fail_response(code: str, msg: str, http_status: int = 400) -> JSONResponse:
    return JSONResponse(status_code=http_status, content=fail(code, msg))

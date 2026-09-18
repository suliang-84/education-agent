import json
from datetime import datetime, date
from decimal import Decimal
from typing import Any

from fastapi.responses import JSONResponse


def _default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _jsonable(data: Any) -> Any:
    """递归将 data 转为 JSON 可序列化结构"""
    return json.loads(json.dumps(data, default=_default))


def ok(data: Any = None, msg: str = "操作成功") -> dict:
    return {"code": 200, "msg": msg, "data": data}


def fail(http_status: int, msg: str) -> dict:
    return {"code": http_status, "msg": msg, "data": None}


def error(msg: str = "服务器内部错误，请稍后重试") -> dict:
    return {"code": 500, "msg": msg, "data": None}


def ok_response(data: Any = None, msg: str = "操作成功", status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=_jsonable(ok(data, msg)))


def fail_response(msg: str, http_status: int = 400) -> JSONResponse:
    return JSONResponse(status_code=http_status, content=fail(http_status, msg))

# MESH Admin Backend Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 MESH 后台管理系统 FastAPI 后端骨架，包含项目初始化、核心基础设施、所有 ORM 模型、路由骨架、认证模块完整实现，以及第一个可联调的接口（管理员登录 + JWT）。

**Architecture:** 单体 FastAPI 服务，路由前缀 `/api/v1/admin/` 覆盖后台管理，预留 `/api/v1/` 供小程序端。SQLAlchemy 2.0 async 模式连接现有 PostgreSQL，Redis 用于 JWT 黑名单，审计日志统一在 service 层写入。

**Tech Stack:** Python 3.13, FastAPI 0.115+, SQLAlchemy 2.0 async, asyncpg, Pydantic v2, PyJWT, passlib[bcrypt], Redis (redis-py async), Alembic, loguru, pytest + httpx, uv

**Spec:** `docs/4.架构设计/06_接口设计说明书.md` §1、§9

## Global Constraints

- Python >= 3.13
- 数据库：`mesh_edu`，用户 `suliang`，localhost:5432（已存在，**不生成迁移**，只映射现有表）
- 统一响应格式：`{"status":"success"|"fail"|"error","code":0,"msg":"...","data":{}}`
- 游标分页：`?limit=20&before_id=5000`，禁止 OFFSET 分页
- 时间格式：ISO 8601 UTC（`2026-08-30T10:00:00Z`）
- Token：Header `Authorization: Bearer {token}`，HS256，8小时有效，Redis 黑名单
- 所有写操作自动写 `admin_audit_logs`
- 软删除：`questions`、`students`、`parent_student_bindings` 三表有 `deleted_at`，查询需过滤 `WHERE deleted_at IS NULL`
- 五力枚举以 DB 为准：`INSIGHT / CONSTRUCT / DEDUCE / ADAPT / MIGRATE`
- 管理员登录路径：`POST /api/v1/admin/auth/login`
- JWT 算法：HS256
- 五力测试题：至少 10 道开放测试，无发布上限
- `error_rate` 精度：浮点百分比（如 `58.33`）
- 看板结果：Redis 缓存 5 分钟 TTL
- Celery / 短信：第一期 mock（预留接口位置，不实现）

---

## 文件结构总览

```
code/manage-backend/
├── pyproject.toml
├── .env.example
├── .env                        # git ignore
├── alembic.ini
├── app/
│   ├── main.py
│   ├── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── security.py
│   │   ├── response.py
│   │   ├── exceptions.py
│   │   ├── middleware.py
│   │   └── logger.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── admin.py
│   │   ├── question.py
│   │   ├── cognitive.py
│   │   ├── knowledge.py
│   │   ├── training.py
│   │   ├── student.py
│   │   ├── ai.py
│   │   └── audit.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── auth.py
│   │   ├── question.py
│   │   ├── cognitive.py
│   │   ├── training.py
│   │   ├── dashboard.py
│   │   ├── user.py
│   │   ├── audit.py
│   │   └── system.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       └── admin/
│   │           ├── __init__.py   # 汇总注册
│   │           ├── auth.py
│   │           ├── questions.py
│   │           ├── cognitive.py
│   │           ├── training.py
│   │           ├── system.py
│   │           ├── dashboard.py
│   │           ├── users.py
│   │           └── audit.py
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py
│       ├── question_service.py
│       ├── cognitive_service.py
│       ├── training_service.py
│       ├── dashboard_service.py
│       ├── user_service.py
│       ├── system_service.py
│       └── audit_service.py
├── migrations/
│   ├── env.py
│   └── versions/           # 暂为空，现有 DB 已建好
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_health.py
└── scripts/
    └── create_admin.py
```

---

## Task 1: 项目初始化 + 依赖管理

**Files:**
- Create: `code/manage-backend/pyproject.toml`
- Create: `code/manage-backend/.env.example`
- Create: `code/manage-backend/.gitignore`

**Interfaces:**
- Produces: 可运行的 Python 环境，所有依赖安装完毕

- [ ] **Step 1: 创建项目目录并进入**

```bash
mkdir -p /Users/suliang/project/education-agent/code/manage-backend
cd /Users/suliang/project/education-agent/code/manage-backend
```

- [ ] **Step 2: 安装 uv（如未安装）**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env  # 或重新打开终端
uv --version  # 应输出版本号
```

- [ ] **Step 3: 初始化 uv 项目**

```bash
cd /Users/suliang/project/education-agent/code/manage-backend
uv init --no-readme
```

- [ ] **Step 4: 写入 pyproject.toml**

将以下内容完整替换 `pyproject.toml`：

```toml
[project]
name = "mesh-admin-backend"
version = "0.1.0"
description = "MESH AI教学平台 - 后台管理系统后端"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "pyjwt>=2.10.0",
    "passlib[bcrypt]>=1.7.4",
    "redis[asyncio]>=5.2.0",
    "loguru>=0.7.3",
    "python-multipart>=0.0.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
python_version = "3.13"
strict = false
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 5: 安装所有依赖**

```bash
cd /Users/suliang/project/education-agent/code/manage-backend
uv sync --all-extras
```

- [ ] **Step 6: 创建 .env.example**

```bash
cat > .env.example << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://suliang@localhost:5432/mesh_edu

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=change-this-to-a-random-64-char-string-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8

# App
APP_ENV=development
APP_DEBUG=true
CORS_ORIGINS=http://localhost:5174

# Dashboard cache TTL (seconds)
DASHBOARD_CACHE_TTL=300
EOF
```

- [ ] **Step 7: 创建 .env（本地使用）**

```bash
cp .env.example .env
# 生成随机 JWT 密钥
python3 -c "import secrets; print(secrets.token_hex(32))"
# 将输出的字符串填入 .env 的 JWT_SECRET_KEY
```

- [ ] **Step 8: 创建 .gitignore**

```bash
cat > .gitignore << 'EOF'
.env
.venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
*.egg-info/
EOF
```

- [ ] **Step 9: 提交**

```bash
cd /Users/suliang/project/education-agent
git add code/manage-backend/
git commit -m "feat(backend): 初始化 FastAPI 项目结构与依赖"
```

---

## Task 2: core 层基础设施

**Files:**
- Create: `app/core/__init__.py`
- Create: `app/core/config.py`
- Create: `app/core/database.py`
- Create: `app/core/redis.py`
- Create: `app/core/security.py`
- Create: `app/core/response.py`
- Create: `app/core/exceptions.py`
- Create: `app/core/logger.py`
- Create: `app/core/middleware.py`

**Interfaces:**
- Produces:
  - `get_settings() -> Settings`
  - `AsyncSessionLocal` (SQLAlchemy async session maker)
  - `get_redis() -> Redis`
  - `create_access_token(admin_id, username, role) -> str`
  - `verify_token(token) -> dict`
  - `verify_password(plain, hashed) -> bool`
  - `hash_password(plain) -> str`
  - `ok(data, msg) -> dict` / `fail(code, msg) -> dict`
  - `AppException(code, msg, http_status)`

- [ ] **Step 1: 创建目录结构**

```bash
cd /Users/suliang/project/education-agent/code/manage-backend
mkdir -p app/core app/models app/schemas app/api/v1/admin app/services migrations/versions tests scripts
touch app/__init__.py app/core/__init__.py app/models/__init__.py
touch app/schemas/__init__.py app/api/__init__.py
touch app/api/v1/__init__.py app/api/v1/admin/__init__.py
touch app/services/__init__.py
```

- [ ] **Step 2: 写 app/core/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://suliang@localhost:5432/mesh_edu"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8

    # App
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:5174"]

    # Dashboard cache TTL
    DASHBOARD_CACHE_TTL: int = 300


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

- [ ] **Step 3: 写 app/core/database.py**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 4: 写 app/core/redis.py**

```python
from redis.asyncio import Redis, from_url

from app.core.config import get_settings

settings = get_settings()

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
```

- [ ] **Step 5: 写 app/core/security.py**

```python
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(admin_id: int, username: str, role: str) -> str:
    import uuid

    now = datetime.now(UTC)
    payload = {
        "jti": str(uuid.uuid4()),
        "sub": str(admin_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_EXPIRE_HOURS),
        "iss": "mesh-auth-service",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并验证 JWT，抛出 jwt.PyJWTError 表示无效"""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["jti", "sub", "role", "exp"]},
    )
```

- [ ] **Step 6: 写 app/core/response.py**

```python
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
```

- [ ] **Step 7: 写 app/core/exceptions.py**

```python
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
```

- [ ] **Step 8: 写 app/core/logger.py**

```python
import sys

from loguru import logger


def setup_logger() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} - {message}",
        level="DEBUG",
        colorize=True,
    )
    logger.add(
        "logs/app.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO",
        encoding="utf-8",
    )
```

- [ ] **Step 9: 写 app/core/middleware.py**

```python
import time

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} [{duration:.1f}ms]"
        )
        return response
```

- [ ] **Step 10: 写测试验证核心模块**

创建 `tests/test_core.py`：

```python
import pytest
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.core.response import ok, fail


def test_password_hash_and_verify():
    hashed = hash_password("qwer123#")
    assert verify_password("qwer123#", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_create_and_decode():
    token = create_access_token(1, "admin", "SUPER_ADMIN")
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["role"] == "SUPER_ADMIN"
    assert payload["username"] == "admin"


def test_response_ok():
    r = ok({"id": 1})
    assert r["status"] == "success"
    assert r["code"] == 0
    assert r["data"]["id"] == 1


def test_response_fail():
    r = fail("AUTH-001", "Token 无效")
    assert r["status"] == "fail"
    assert r["code"] == "AUTH-001"
    assert r["data"] is None
```

- [ ] **Step 11: 运行测试**

```bash
cd /Users/suliang/project/education-agent/code/manage-backend
uv run pytest tests/test_core.py -v
```

Expected: 4 PASSED

- [ ] **Step 12: 提交**

```bash
git add app/core/ tests/test_core.py
git commit -m "feat(backend): 添加 core 基础设施层（config/db/redis/security/response/exceptions）"
```

---

## Task 3: SQLAlchemy ORM 模型层（映射现有 34 张表）

**Files:**
- Create: `app/models/base.py`
- Create: `app/models/admin.py`
- Create: `app/models/question.py`
- Create: `app/models/cognitive.py`
- Create: `app/models/knowledge.py`
- Create: `app/models/training.py`
- Create: `app/models/student.py`
- Create: `app/models/ai.py`
- Create: `app/models/audit.py`
- Modify: `app/models/__init__.py`

**Interfaces:**
- Produces: 所有 ORM 类，供 services 层使用

- [ ] **Step 1: 写 app/models/base.py**

```python
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [ ] **Step 2: 写 app/models/admin.py**

```python
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AdminUser(Base, TimestampMixin):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="SUPER_ADMIN")
    # 0=停用, 1=启用, 2=待首次登录
    is_active: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2)
    login_fail_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
```

- [ ] **Step 3: 写 app/models/knowledge.py**

```python
from sqlalchemy import BigInteger, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Grade(Base, TimestampMixin):
    __tablename__ = "grades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Semester(Base, TimestampMixin):
    __tablename__ = "semesters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grade_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(5), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class KnowledgePoint(Base, TimestampMixin):
    __tablename__ = "knowledge_points"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chapter_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [ ] **Step 4: 写 app/models/question.py**

```python
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    semester_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chapter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    knowledge_point_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    question_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    answer: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    common_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    power_solutions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    five_power_weights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    primary_power: Mapped[str | None] = mapped_column(String(20), nullable=True)
    transfer_direction: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    analysis_round: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    embedded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_seed_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)


class QuestionAnalysis(Base, TimestampMixin):
    __tablename__ = "question_analyses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    question_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    round: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    rejection_reason_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_grade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_semester_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_chapter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ai_knowledge_point_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ai_difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_common_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_power_solutions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_five_power_weights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_transfer_directions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ai_question_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_answer: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
```

- [ ] **Step 5: 写 app/models/cognitive.py**

```python
from datetime import datetime

from sqlalchemy import BigInteger, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CognitiveTestQuestion(Base, TimestampMixin):
    __tablename__ = "cognitive_test_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_no: Mapped[int] = mapped_column(Integer, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    answers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reference_time_sec: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=90)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
```

- [ ] **Step 6: 写 app/models/training.py**

```python
from sqlalchemy import BigInteger, Boolean, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TrainingDimensionConfig(Base, TimestampMixin):
    __tablename__ = "training_dimension_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dimension: Mapped[str] = mapped_column(String(30), nullable=False)
    version_number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class TrainingSession(Base, TimestampMixin):
    __tablename__ = "training_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dimension: Mapped[str] = mapped_column(String(30), nullable=False)
    knowledge_point_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    chapter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    semester_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    total_questions: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    answered_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    correct_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    config_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

- [ ] **Step 7: 写 app/models/student.py**

```python
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_type: Mapped[str] = mapped_column(String(10), nullable=False, default="STUDENT")
    openid_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 加密存储
    phone_masked: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    subject_prefs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_minor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)


class ParentStudentBinding(Base, TimestampMixin):
    __tablename__ = "parent_student_bindings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    parent_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bind_method: Mapped[str] = mapped_column(String(20), nullable=False)
    bind_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
```

- [ ] **Step 8: 写 app/models/ai.py**

```python
from sqlalchemy import BigInteger, Boolean, Float, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AiHeuristicStrategy(Base, TimestampMixin):
    __tablename__ = "ai_heuristic_strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicable_powers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    default_priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    example_phrase: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SystemConfig(Base, TimestampMixin):
    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False, default="string")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
```

- [ ] **Step 9: 写 app/models/audit.py**

```python
from sqlalchemy import BigInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AdminAuditLog(Base, TimestampMixin):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    admin_name: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
```

- [ ] **Step 10: 更新 app/models/__init__.py**

```python
from app.models.admin import AdminUser
from app.models.ai import AiHeuristicStrategy, SystemConfig
from app.models.audit import AdminAuditLog
from app.models.base import Base
from app.models.cognitive import CognitiveTestQuestion
from app.models.knowledge import Chapter, Grade, KnowledgePoint, Semester, Subject
from app.models.question import Question, QuestionAnalysis
from app.models.student import ParentStudentBinding, Student
from app.models.training import TrainingDimensionConfig, TrainingSession

__all__ = [
    "Base",
    "AdminUser",
    "Question", "QuestionAnalysis",
    "CognitiveTestQuestion",
    "Subject", "Grade", "Semester", "Chapter", "KnowledgePoint",
    "TrainingDimensionConfig", "TrainingSession",
    "Student", "ParentStudentBinding",
    "AiHeuristicStrategy", "SystemConfig",
    "AdminAuditLog",
]
```

- [ ] **Step 11: 验证模型可导入**

创建 `tests/test_models.py`：

```python
def test_models_import():
    from app.models import (
        AdminUser, Question, CognitiveTestQuestion,
        Subject, Grade, Semester, Chapter, KnowledgePoint,
        TrainingDimensionConfig, Student, AdminAuditLog,
        AiHeuristicStrategy, SystemConfig,
    )
    # 验证表名映射正确
    assert AdminUser.__tablename__ == "admin_users"
    assert Question.__tablename__ == "questions"
    assert CognitiveTestQuestion.__tablename__ == "cognitive_test_questions"
    assert Subject.__tablename__ == "subjects"
```

```bash
uv run pytest tests/test_models.py -v
```

Expected: 1 PASSED

- [ ] **Step 12: 提交**

```bash
git add app/models/ tests/test_models.py
git commit -m "feat(backend): 添加所有 SQLAlchemy ORM 模型（映射现有 34 张表）"
```

---

## Task 4: Pydantic Schemas + 统一响应结构

**Files:**
- Create: `app/schemas/common.py`
- Create: `app/schemas/auth.py`
- Create: `app/schemas/question.py`（骨架）
- Create: `app/schemas/cognitive.py`（骨架）
- Create: `app/schemas/user.py`（骨架）
- Create: `app/schemas/audit.py`（骨架）
- Create: `app/schemas/system.py`（骨架）
- Create: `app/schemas/dashboard.py`（骨架）
- Create: `app/schemas/training.py`（骨架）

**Interfaces:**
- Produces:
  - `PageResp[T]` 分页响应泛型
  - `LoginReq`, `TwoFAReq`, `TokenResp`

- [ ] **Step 1: 写 app/schemas/common.py**

```python
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PageResp(BaseModel, Generic[T]):
    """游标分页响应结构"""
    list: list[T]
    total: int
    has_more: bool
    next_cursor: int | None = None


class PageParams(BaseModel):
    """游标分页查询参数"""
    limit: int = 20
    before_id: int | None = None

    model_config = ConfigDict(extra="ignore")
```

- [ ] **Step 2: 写 app/schemas/auth.py**

```python
from pydantic import BaseModel, Field


class LoginReq(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class TwoFAReq(BaseModel):
    session_token: str
    code: str = Field(..., min_length=6, max_length=6)


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    admin: "AdminInfo"


class AdminInfo(BaseModel):
    id: int
    username: str
    display_name: str
    role: str


TokenResp.model_rebuild()
```

- [ ] **Step 3: 写骨架 schemas（其他模块后续填充业务字段）**

```bash
# 每个文件只写模块注释，后续 Task 填充具体 Schema
for f in question cognitive user audit system dashboard training; do
cat > app/schemas/${f}.py << EOF
"""${f} 模块 Pydantic Schemas"""
# 具体 Schema 在对应业务 Task 中填充
EOF
done
```

- [ ] **Step 4: 更新 app/schemas/__init__.py**

```python
from app.schemas.auth import AdminInfo, LoginReq, TokenResp, TwoFAReq
from app.schemas.common import PageParams, PageResp

__all__ = [
    "PageResp", "PageParams",
    "LoginReq", "TwoFAReq", "TokenResp", "AdminInfo",
]
```

- [ ] **Step 5: 提交**

```bash
git add app/schemas/
git commit -m "feat(backend): 添加 Pydantic schemas（common + auth，其余模块骨架）"
```

---

## Task 5: 依赖注入 + main.py 应用入口

**Files:**
- Create: `app/dependencies.py`
- Create: `app/main.py`

**Interfaces:**
- Produces:
  - `get_db()` → `AsyncSession`
  - `get_current_admin()` → `AdminUser`
  - FastAPI app 实例，可用 uvicorn 启动

- [ ] **Step 1: 写 app/dependencies.py**

```python
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import jwt

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.admin import AdminUser

security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise AppException("AUTH-001", "Token 已过期，请重新登录", 401)
    except jwt.PyJWTError:
        raise AppException("AUTH-001", "Token 无效，请重新登录", 401)

    # 检查 Redis 黑名单
    redis = await get_redis()
    jti = payload.get("jti", "")
    if await redis.get(f"blacklist:{jti}"):
        raise AppException("AUTH-001", "Token 已撤销，请重新登录", 401)

    # 检查角色
    if payload.get("role") != "SUPER_ADMIN":
        raise AppException("AUTH-003", "权限不足", 403)

    # 查询管理员
    admin_id = int(payload["sub"])
    result = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin:
        raise AppException("AUTH-001", "管理员不存在", 401)
    if admin.is_active == 0:
        raise AppException("AUTH-003", "账号已停用", 403)

    return admin
```

- [ ] **Step 2: 写 app/main.py**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# 注册路由
from app.api.v1.admin import router as admin_router  # noqa: E402
app.include_router(admin_router, prefix="/api/v1/admin")


@app.get("/health", tags=["健康检查"])
async def health():
    from app.core.response import ok
    return ok({"status": "healthy"})
```

- [ ] **Step 3: 写 app/api/v1/admin/__init__.py（汇总路由）**

```python
from fastapi import APIRouter

from app.api.v1.admin.auth import router as auth_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["认证"])

# 后续 Task 逐步添加其他路由：
# from app.api.v1.admin.questions import router as questions_router
# router.include_router(questions_router, prefix="/questions", tags=["题库管理"])
```

- [ ] **Step 4: 创建占位路由文件**

```bash
for f in questions cognitive training system dashboard users audit; do
cat > app/api/v1/admin/${f}.py << EOF
"""${f} 路由 - 待实现"""
from fastapi import APIRouter
router = APIRouter()
EOF
done
```

- [ ] **Step 5: 验证 FastAPI 可启动**

```bash
cd /Users/suliang/project/education-agent/code/manage-backend
uv run uvicorn app.main:app --reload --port 8000
```

浏览器访问 `http://localhost:8000/health`，应返回：
```json
{"status":"success","code":0,"msg":"操作成功","data":{"status":"healthy"}}
```

访问 `http://localhost:8000/api/docs` 应看到 Swagger UI。

- [ ] **Step 6: 写测试**

创建 `tests/conftest.py`：

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

创建 `tests/test_health.py`：

```python
import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["status"] == "healthy"
```

```bash
uv run pytest tests/test_health.py -v
```

Expected: 1 PASSED

- [ ] **Step 7: 提交**

```bash
git add app/main.py app/dependencies.py app/api/ tests/conftest.py tests/test_health.py
git commit -m "feat(backend): 添加 FastAPI 应用入口、依赖注入、CORS、中间件"
```

---

## Task 6: 认证模块完整实现（管理员登录 + JWT）

**Files:**
- Create: `app/services/auth_service.py`
- Create: `app/api/v1/admin/auth.py`
- Create: `app/services/audit_service.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes:
  - `AdminUser`（from models）
  - `LoginReq`, `TokenResp`（from schemas）
  - `hash_password`, `verify_password`, `create_access_token`（from core.security）
  - `get_db()`（from dependencies）
- Produces:
  - `POST /api/v1/admin/auth/login` → `TokenResp`
  - `POST /api/v1/admin/auth/logout`
  - `audit_service.log()`

- [ ] **Step 1: 写 app/services/audit_service.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AdminAuditLog


async def log(
    db: AsyncSession,
    admin_id: int,
    admin_name: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
) -> None:
    entry = AdminAuditLog(
        admin_id=admin_id,
        admin_name=admin_name,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(entry)
    # 不 commit，由调用方统一 commit
```

- [ ] **Step 2: 写 app/services/auth_service.py**

```python
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.redis import get_redis
from app.core.security import create_access_token, decode_token, verify_password
from app.models.admin import AdminUser

MAX_FAIL_COUNT = 5
LOCK_MINUTES = 30


async def login(db: AsyncSession, username: str, password: str, ip: str) -> tuple[str, AdminUser]:
    """
    验证管理员账号密码，返回 (access_token, admin)。
    失败时抛出 AppException。
    """
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    admin = result.scalar_one_or_none()

    if not admin:
        raise AppException("LOGIN-001", "账号或密码错误", 401)

    # 检查锁定
    if admin.locked_until and admin.locked_until > datetime.now(UTC):
        raise AppException("LOGIN-002", f"账号已锁定，请{LOCK_MINUTES}分钟后重试", 403)

    # 检查账号状态
    if admin.is_active == 0:
        raise AppException("AUTH-003", "账号已停用，请联系管理员", 403)

    # 验证密码
    if not verify_password(password, admin.password_hash):
        new_fail = admin.login_fail_count + 1
        update_vals: dict = {"login_fail_count": new_fail}
        if new_fail >= MAX_FAIL_COUNT:
            from datetime import timedelta
            update_vals["locked_until"] = datetime.now(UTC) + timedelta(minutes=LOCK_MINUTES)
            update_vals["login_fail_count"] = 0
            await db.execute(update(AdminUser).where(AdminUser.id == admin.id).values(**update_vals))
            await db.commit()
            raise AppException("LOGIN-002", f"密码错误次数过多，账号已锁定{LOCK_MINUTES}分钟", 403)
        remaining = MAX_FAIL_COUNT - new_fail
        await db.execute(update(AdminUser).where(AdminUser.id == admin.id).values(**update_vals))
        await db.commit()
        raise AppException("LOGIN-001", f"账号或密码错误，还可尝试{remaining}次", 401)

    # 登录成功：重置失败次数，更新 last_login
    await db.execute(
        update(AdminUser)
        .where(AdminUser.id == admin.id)
        .values(
            login_fail_count=0,
            locked_until=None,
            last_login_at=datetime.now(UTC),
            last_login_ip=ip,
        )
    )
    await db.commit()
    await db.refresh(admin)

    token = create_access_token(admin.id, admin.username, admin.role)
    return token, admin


async def logout(token: str) -> None:
    """将 token 加入 Redis 黑名单"""
    try:
        payload = decode_token(token)
        jti = payload["jti"]
        exp = payload["exp"]
        ttl = max(0, exp - int(datetime.now(UTC).timestamp()))
        redis = await get_redis()
        if ttl > 0:
            await redis.setex(f"blacklist:{jti}", ttl, "revoked")
    except Exception:
        pass  # token 本身无效，忽略
```

- [ ] **Step 3: 写 app/api/v1/admin/auth.py**

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.response import ok_response
from app.dependencies import get_current_admin, get_db
from app.models.admin import AdminUser
from app.schemas.auth import LoginReq, TokenResp, AdminInfo
from app.services import auth_service, audit_service

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=None, summary="管理员登录")
async def login(
    body: LoginReq,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    token, admin = await auth_service.login(db, body.username, body.password, ip)

    # 写审计日志
    await audit_service.log(
        db, admin.id, admin.display_name,
        "ADMIN_LOGIN", "admin_users", str(admin.id),
        ip_address=ip,
    )
    await db.commit()

    return ok_response(
        TokenResp(
            access_token=token,
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            admin=AdminInfo(
                id=admin.id,
                username=admin.username,
                display_name=admin.display_name,
                role=admin.role,
            ),
        ).model_dump(),
        "登录成功",
    )


@router.post("/logout", summary="退出登录")
async def logout(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # 从 Header 取 token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    await auth_service.logout(token)

    await audit_service.log(
        db, current_admin.id, current_admin.display_name,
        "ADMIN_LOGOUT", ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return ok_response(None, "已退出登录")
```

- [ ] **Step 4: 在路由汇总中注册 auth**

确认 `app/api/v1/admin/__init__.py` 已包含（Task 5 已写）：
```python
from app.api.v1.admin.auth import router as auth_router
router.include_router(auth_router, prefix="/auth", tags=["认证"])
```

- [ ] **Step 5: 写测试 tests/test_auth.py**

```python
import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "admin",
        "password": "qwer123#"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]
    assert data["data"]["admin"]["username"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert resp.status_code == 401
    data = resp.json()
    assert data["status"] == "fail"
    assert data["code"] == "LOGIN-001"


@pytest.mark.asyncio
async def test_login_wrong_username(client):
    resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "notexist",
        "password": "qwer123#"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client):
    # 先登录拿 token
    login_resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "admin",
        "password": "qwer123#"
    })
    token = login_resp.json()["data"]["access_token"]

    # 退出
    resp = await client.post(
        "/api/v1/admin/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    resp = await client.get("/api/v1/admin/questions")
    assert resp.status_code == 403  # HTTPBearer 返回 403
```

- [ ] **Step 6: 启动服务并运行测试**

```bash
# 确保 PostgreSQL 和 Redis 运行中
uv run pytest tests/test_auth.py -v
```

Expected: 5 PASSED

- [ ] **Step 7: 手动验证**

```bash
uv run uvicorn app.main:app --reload --port 8000

# 另开终端测试登录
curl -X POST http://localhost:8000/api/v1/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"qwer123#"}'
```

Expected: 返回 `{"status":"success","code":0,"data":{"access_token":"..."}}`

- [ ] **Step 8: 提交**

```bash
git add app/services/auth_service.py app/services/audit_service.py \
        app/api/v1/admin/auth.py tests/test_auth.py
git commit -m "feat(backend): 实现管理员登录/退出接口（JWT + Redis 黑名单 + 审计日志）"
```

---

## Task 7: Alembic 配置（只读现有库，不生成迁移）

**Files:**
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`

**Interfaces:**
- Produces: `alembic` 命令可用，可生成未来的迁移文件

- [ ] **Step 1: 初始化 Alembic**

```bash
cd /Users/suliang/project/education-agent/code/manage-backend
uv run alembic init migrations
```

- [ ] **Step 2: 修改 alembic.ini 连接字符串**

在 `alembic.ini` 中修改 `sqlalchemy.url`：

```ini
sqlalchemy.url = postgresql+asyncpg://suliang@localhost:5432/mesh_edu
```

- [ ] **Step 3: 修改 migrations/env.py**

将 `migrations/env.py` 完整替换为：

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from app.models.base import Base
from app.models import *  # noqa: F401,F403 导入所有模型使 Alembic 感知

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 验证 Alembic 可连接数据库**

```bash
uv run alembic current
```

Expected: 输出 `(head)`（因为现有库无 alembic_version 表，会提示无版本，不报错即可）

- [ ] **Step 5: 提交**

```bash
git add alembic.ini migrations/
git commit -m "feat(backend): 配置 Alembic（连接现有 PostgreSQL，支持未来迁移）"
```

---

## Task 8: 运行整体测试 + 最终验证

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: 运行全部测试**

```bash
cd /Users/suliang/project/education-agent/code/manage-backend
uv run pytest tests/ -v --tb=short
```

Expected: 所有测试通过（core + models + health + auth）

- [ ] **Step 2: 写一个集成测试验证完整链路**

创建 `tests/test_integration.py`：

```python
import pytest


@pytest.mark.asyncio
async def test_full_auth_flow(client):
    """完整认证流程：登录 → 访问受保护接口 → 退出 → Token 失效"""
    # 1. 登录
    resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "admin", "password": "qwer123#"
    })
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]

    # 2. 退出
    resp = await client.post(
        "/api/v1/admin/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    # 3. 再次使用同一 token（应被拒绝）
    resp = await client.post(
        "/api/v1/admin/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 401
```

```bash
uv run pytest tests/test_integration.py -v
```

Expected: 1 PASSED

- [ ] **Step 3: 代码风格检查**

```bash
uv run ruff check app/ tests/
uv run ruff format app/ tests/ --check
```

- [ ] **Step 4: 最终提交**

```bash
git add tests/test_integration.py
git commit -m "feat(backend): 完成后端骨架搭建，认证流程端到端验证通过"
```

- [ ] **Step 5: 输出启动命令供联调参考**

```bash
# 开发模式启动
cd /Users/suliang/project/education-agent/code/manage-backend
uv run uvicorn app.main:app --reload --port 8000

# API 文档：http://localhost:8000/api/docs
# 健康检查：http://localhost:8000/health
# 管理员登录：POST http://localhost:8000/api/v1/admin/auth/login
```

---

## 自查：Spec 覆盖情况

| 规范要求 | 覆盖任务 |
|---------|---------|
| 统一响应格式 `{status,code,msg,data}` | Task 2（response.py）|
| JWT HS256，8小时，Redis 黑名单 | Task 2（security.py）+ Task 6（auth_service）|
| 所有写操作写 audit_log | Task 6（audit_service）|
| 游标分页 `limit+before_id` | Task 4（schemas/common.py PageParams）|
| 软删除过滤（deleted_at IS NULL）| Task 3 模型定义，service 层查询时执行 |
| 五力枚举以 DB 为准 | Task 3 模型注释说明 |
| 管理员登录路径 `/api/v1/admin/auth/login` | Task 5 + Task 6 |
| 账号锁定（5次失败→30分钟）| Task 6（auth_service）|
| CORS 白名单 `localhost:5174` | Task 5（main.py）|
| 看板 Redis 缓存 5分钟（TODO）| Task 9+ 扩展 |
| 五力测试题最少10道开放（无上限）| Task 10+ 扩展 |
| `error_rate` 精度浮点百分比 | Task 11+ 扩展 |

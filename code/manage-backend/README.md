# MESH Admin Backend

MESH AI 助教平台 · 后台管理系统后端服务

---

## 目录

- [项目简介](#项目简介)
- [技术栈](#技术栈)
- [快速启动](#快速启动)
- [目录结构](#目录结构)
- [架构设计](#架构设计)
  - [分层说明](#分层说明)
  - [请求调用链路](#请求调用链路)
- [核心模块](#核心模块)
  - [core 基础设施层](#core-基础设施层)
  - [models ORM 模型层](#models-orm-模型层)
  - [schemas 数据校验层](#schemas-数据校验层)
  - [api 路由层](#api-路由层)
  - [services 业务逻辑层](#services-业务逻辑层)
- [认证机制](#认证机制)
- [统一规范](#统一规范)
  - [响应格式](#响应格式)
  - [错误码体系](#错误码体系)
  - [分页规范](#分页规范)
- [环境变量](#环境变量)
- [数据库](#数据库)
- [测试](#测试)
- [代码规范](#代码规范)
- [已实现接口](#已实现接口)
- [待实现模块](#待实现模块)
- [接口文档](#接口文档)

---

## 项目简介

本服务是 MESH AI 助教平台的**后台管理系统后端**，供 `SUPER_ADMIN` 角色的管理员使用，提供题库管理、五力测试题维护、训练参数配置、用户管理、数据看板等功能。

与前端（`manage-frontend`）对接，Base URL 为 `/api/v1/admin/`。

> 当前处于**骨架阶段**：核心基础设施（认证、ORM 模型、统一响应）已完整实现，业务接口模块（题库、看板等）的路由骨架已注册，Service 层待逐模块填充。

---

## 技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web 框架 | FastAPI | ≥ 0.115 | 原生 async，自动生成 OpenAPI 文档 |
| ASGI 服务器 | uvicorn | ≥ 0.30 | 开发用 `--reload`，生产用 gunicorn 管理 |
| ORM | SQLAlchemy 2.0 | ≥ 2.0.36 | async 模式，`Mapped`/`mapped_column` 语法 |
| DB 驱动 | asyncpg | ≥ 0.30 | PostgreSQL 高性能异步驱动 |
| 数据校验 | Pydantic v2 | ≥ 2.10 | Request/Response schema，类型安全 |
| 配置管理 | pydantic-settings | ≥ 2.6 | 从 `.env` 读取强类型配置 |
| 数据库迁移 | Alembic | ≥ 1.14 | async engine，支持未来迁移 |
| 认证 | PyJWT | ≥ 2.10 | HS256 签名，8小时有效 |
| 密码哈希 | bcrypt | ≥ 4.0 | 直接调用（不经 passlib）|
| 缓存/黑名单 | Redis (redis-py async) | ≥ 5.2 | JWT 黑名单、看板缓存 |
| 日志 | loguru | ≥ 0.7.3 | 结构化日志，自动轮转 |
| 依赖管理 | uv | — | 快速安装，锁定版本 |
| 代码规范 | ruff | ≥ 0.8 | lint + format 一体 |
| 测试 | pytest + httpx | — | async 支持，fakeredis mock |

---

## 快速启动

### 前置要求

- Python 3.13+
- PostgreSQL 16+（数据库 `mesh_edu` 已存在）
- Redis 7+

### 1. 安装依赖

```bash
cd code/manage-backend

# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装所有依赖（含 dev）
uv sync --all-extras
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，修改 JWT_SECRET_KEY 为随机字符串
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 启动服务

```bash
uv run uvicorn app.main:app --reload --port 8000
```

### 4. 验证运行

```
GET  http://localhost:8000/health           → {"status":"success","data":{"status":"healthy"}}
GET  http://localhost:8000/api/docs         → Swagger UI
GET  http://localhost:8000/api/openapi.json → OpenAPI JSON
```

### 默认管理员账号

```
用户名：admin
密  码：qwer123#
```

---

## 目录结构

```
code/manage-backend/
│
├── .env.example                # 环境变量模板
├── .env                        # 本地配置（git ignore）
├── pyproject.toml              # 依赖声明 + ruff/mypy/pytest 配置
├── alembic.ini                 # Alembic 配置
│
├── app/
│   ├── main.py                 # FastAPI 入口：注册路由、中间件、异常处理、lifespan
│   ├── dependencies.py         # 公共依赖注入：get_db()、get_current_admin()
│   │
│   ├── core/                   # ── 基础设施层（无业务逻辑）──────────────────
│   │   ├── config.py           # Settings（pydantic-settings 读 .env）
│   │   ├── database.py         # async engine + AsyncSession 工厂 + get_db()
│   │   ├── redis.py            # Redis 连接池单例 + get_redis() / close_redis()
│   │   ├── security.py         # JWT 签发/解码、bcrypt 密码哈希/验证
│   │   ├── response.py         # 统一响应封装：ok() / fail() / error() / ok_response()
│   │   ├── exceptions.py       # AppException + 全局异常处理器
│   │   ├── middleware.py       # RequestLogMiddleware（请求日志 + 耗时）
│   │   └── logger.py           # loguru 配置（stdout + logs/app.log）
│   │
│   ├── models/                 # ── ORM 模型层（映射现有 34 张 DB 表）──────────
│   │   ├── base.py             # Base（DeclarativeBase）+ TimestampMixin
│   │   ├── admin.py            # AdminUser（admin_users）
│   │   ├── question.py         # Question、QuestionAnalysis
│   │   ├── cognitive.py        # CognitiveTestQuestion
│   │   ├── knowledge.py        # Subject / Grade / Semester / Chapter / KnowledgePoint
│   │   ├── training.py         # TrainingDimensionConfig、TrainingConfigVersion、TrainingSession、TrainingAnswerRecord
│   │   ├── student.py          # Student、ParentStudentBinding、FivePowerProfile、FivePowerTrainingProfile
│   │   │                       # TestSession、TestAnswerRecord、WrongAnswerRecord、StudentKpStat
│   │   │                       # InviteCode、SmsCode
│   │   ├── ai.py               # AiHeuristicStrategy、SystemConfig、AiChatSession、AiChatMessage
│   │   │                       # AiStrategyEvent、AiStudentStrategyProfile、AiTokenUsageLog
│   │   │                       # StudentAiPromptSummary、StudentPromptInsight、SystemDowngradeLog
│   │   └── audit.py            # AdminAuditLog
│   │
│   ├── schemas/                # ── Pydantic 校验层（Request/Response 模型）────
│   │   ├── common.py           # PageResp[T]（游标分页）、PageParams
│   │   ├── auth.py             # LoginReq、TwoFAReq、TokenResp、AdminInfo
│   │   ├── question.py         # 待填充（题库管理）
│   │   ├── cognitive.py        # 待填充（五力测试题）
│   │   ├── training.py         # 待填充（训练参数配置）
│   │   ├── dashboard.py        # 待填充（数据看板）
│   │   ├── user.py             # 待填充（用户管理）
│   │   ├── audit.py            # 待填充（审计日志）
│   │   └── system.py           # 待填充（系统参数）
│   │
│   ├── api/
│   │   └── v1/admin/           # ── 路由层（prefix: /api/v1/admin）───────────
│   │       ├── __init__.py     # 汇总注册所有子路由
│   │       ├── auth.py         # ✅ POST /auth/login、POST /auth/logout
│   │       ├── questions.py    # 🔲 题库管理（骨架）
│   │       ├── cognitive.py    # 🔲 五力测试题（骨架）
│   │       ├── training.py     # 🔲 训练参数配置（骨架）
│   │       ├── system.py       # 🔲 系统参数 + 启发策略（骨架）
│   │       ├── dashboard.py    # 🔲 数据看板（骨架）
│   │       ├── users.py        # 🔲 用户管理（骨架）
│   │       └── audit.py        # 🔲 审计日志（骨架）
│   │
│   └── services/               # ── 业务逻辑层（所有规则在这里）─────────────
│       ├── auth_service.py     # ✅ login()、logout() — 登录验证、锁定、JWT
│       └── audit_service.py    # ✅ log() — 写 admin_audit_logs（供其他 service 调用）
│
├── migrations/                 # Alembic 迁移（现有 DB 已建好，此目录供未来迁移用）
│   ├── env.py                  # async engine 配置，自动发现所有 ORM 模型
│   └── versions/               # 迁移版本文件（当前为空）
│
├── tests/
│   ├── conftest.py             # pytest fixture：fakeredis mock + async HTTP client
│   ├── test_auth.py            # 认证接口测试（登录/退出/黑名单验证）
│   ├── test_core.py            # 核心工具测试（密码哈希、JWT、响应格式）
│   ├── test_health.py          # 健康检查测试
│   ├── test_integration.py     # 端到端认证流程集成测试
│   └── test_models.py          # ORM 模型导入和表名映射测试
│
└── scripts/                    # 运维脚本（待添加）
```

> **图例：** ✅ 已完整实现 | 🔲 骨架（路由已注册，Service 待填充）

---

## 架构设计

### 分层说明

```
┌─────────────────────────────────────────────────────┐
│  api 层（路由控制器）                                  │
│  解析请求参数、校验 Token、调用 service、返回响应       │
│  不写业务逻辑，不直接操作 DB                           │
├─────────────────────────────────────────────────────┤
│  service 层（业务逻辑）                                │
│  实现所有业务规则、编排多个 DB 操作、写审计日志         │
│  不处理 HTTP 请求/响应                                 │
├─────────────────────────────────────────────────────┤
│  model 层（ORM）                                      │
│  定义数据库表结构，映射现有 PostgreSQL 34 张表          │
│  不写业务逻辑                                          │
├─────────────────────────────────────────────────────┤
│  schema 层（Pydantic v2）                             │
│  定义请求/响应数据结构和校验规则                       │
│  不操作数据库                                          │
├─────────────────────────────────────────────────────┤
│  core 层（基础设施）                                   │
│  JWT、DB 连接、Redis、配置、日志、异常处理              │
│  不写业务逻辑                                          │
└─────────────────────────────────────────────────────┘
```

### 请求调用链路

以 `POST /api/v1/admin/auth/login` 为例：

```
HTTP Request
    ↓
RequestLogMiddleware        记录请求日志、计算耗时
    ↓
CORSMiddleware              跨域检查
    ↓
api/v1/admin/auth.py        解析 LoginReq，调用 auth_service.login()
    ↓
services/auth_service.py    查询 AdminUser，验证密码，检查锁定/状态
                            调用 create_access_token() 签发 JWT
                            调用 audit_service.log() 写审计日志
    ↓
models/admin.py             SQLAlchemy ORM 执行 SELECT/UPDATE
    ↓
PostgreSQL (mesh_edu)
    ↓
schemas/auth.py             TokenResp 序列化返回数据
    ↓
core/response.py            ok_response() 包装为统一格式
    ↓
HTTP Response: {"status":"success","code":0,"msg":"登录成功","data":{...}}
```

---

## 核心模块

### core 基础设施层

#### `core/config.py` — 配置管理

```python
from app.core.config import get_settings

settings = get_settings()
settings.DATABASE_URL    # DB 连接串
settings.JWT_SECRET_KEY  # JWT 密钥
settings.APP_DEBUG       # 是否 debug 模式
```

单例模式，全局只创建一次 `Settings` 实例。

#### `core/database.py` — 数据库连接

```python
from app.core.database import get_db  # 用于 FastAPI 依赖注入

# 路由层用法
async def my_route(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Model))
```

连接池：`pool_size=10, max_overflow=20`。

#### `core/redis.py` — Redis 连接

```python
from app.core.redis import get_redis

redis = await get_redis()
await redis.set("key", "value", ex=300)
await redis.get("key")
```

单例，应用启动时预热（lifespan），关闭时释放。

#### `core/security.py` — 认证工具

```python
from app.core.security import (
    hash_password,      # bcrypt 哈希
    verify_password,    # bcrypt 验证
    create_access_token,# 签发 JWT（HS256，8小时）
    decode_token,       # 解码并验证 JWT，失败抛 jwt.PyJWTError
)
```

JWT Payload 结构：
```json
{
  "jti": "uuid-唯一标识",
  "sub": "1",
  "username": "admin",
  "role": "SUPER_ADMIN",
  "iat": 1234567890,
  "exp": 1234567890,
  "iss": "mesh-auth-service"
}
```

#### `core/response.py` — 统一响应

```python
from app.core.response import ok, fail, error, ok_response, fail_response

# 在路由中使用
return ok_response({"id": 1}, "创建成功")          # 200
return fail_response("LOGIN-001", "密码错误", 401)   # 401

# 在 service 层构造数据时
data = ok({"list": items, "total": 100})
```

#### `core/exceptions.py` — 异常处理

```python
from app.core.exceptions import AppException

# 在 service 层抛出
raise AppException("AUTH-001", "Token 已过期", 401)
raise AppException("LOGIN-002", "账号已锁定", 403)
```

`AppException` 会被全局处理器捕获，自动转为统一响应格式。非业务异常（500）在 `APP_DEBUG=false` 时隐藏详情。

---

### models ORM 模型层

所有模型继承 `Base`（`DeclarativeBase`），需要时混入 `TimestampMixin`（提供 `created_at` / `updated_at`）。

**软删除表（查询时必须过滤 `deleted_at IS NULL`）：**

| 模型 | 表名 | 说明 |
|------|------|------|
| `Question` | `questions` | 训练题目 |
| `Student` | `students` | 学生/家长账号 |
| `ParentStudentBinding` | `parent_student_bindings` | 家长-学生绑定关系 |

**使用示例：**

```python
from app.models import Question, Student, AdminUser

# 查询时过滤软删除
result = await db.execute(
    select(Question)
    .where(Question.deleted_at.is_(None))
    .where(Question.status == "published")
)
```

**数据库表一览（34 张）：**

| 模型文件 | 包含模型 |
|---------|---------|
| `admin.py` | `AdminUser` |
| `question.py` | `Question`、`QuestionAnalysis` |
| `cognitive.py` | `CognitiveTestQuestion` |
| `knowledge.py` | `Subject`、`Grade`、`Semester`、`Chapter`、`KnowledgePoint` |
| `training.py` | `TrainingDimensionConfig`、`TrainingConfigVersion`、`TrainingSession`、`TrainingAnswerRecord` |
| `student.py` | `Student`、`ParentStudentBinding`、`FivePowerProfile`、`FivePowerTrainingProfile`、`TestSession`、`TestAnswerRecord`、`WrongAnswerRecord`、`StudentKpStat`、`InviteCode`、`SmsCode` |
| `ai.py` | `AiHeuristicStrategy`、`SystemConfig`、`AiChatSession`、`AiChatMessage`、`AiStrategyEvent`、`AiStudentStrategyProfile`、`AiTokenUsageLog`、`StudentAiPromptSummary`、`StudentPromptInsight`、`SystemDowngradeLog` |
| `audit.py` | `AdminAuditLog` |

---

### schemas 数据校验层

**已完整实现：**

```python
from app.schemas.common import PageResp, PageParams
from app.schemas.auth import LoginReq, TwoFAReq, TokenResp, AdminInfo

# 分页参数（Query Params）
class PageParams(BaseModel):
    limit: int = 20       # 每页数量，最大 100
    before_id: int | None # 游标 ID（上一页最后一条）

# 分页响应（泛型）
class PageResp[T](BaseModel):
    list: list[T]
    total: int
    has_more: bool
    next_cursor: int | None
```

**其余模块**（`question.py`, `cognitive.py`, `training.py`, `dashboard.py`, `user.py`, `audit.py`, `system.py`）目前为空骨架，对应业务模块实现时填充。

---

### api 路由层

所有管理后台路由前缀：`/api/v1/admin`

路由注册入口：`app/api/v1/admin/__init__.py`，添加新模块时在此注册：

```python
# 示例：添加题库管理路由
from app.api.v1.admin.questions import router as questions_router
router.include_router(questions_router, prefix="/questions", tags=["题库管理"])
```

**路由层职责：**
- 接收 HTTP 请求，解析 Pydantic Schema
- 通过 `Depends(get_current_admin)` 验证 Token 和权限
- 调用对应 Service
- 调用 `audit_service.log()` 写审计（service 层 add，router 层 commit）
- 返回 `ok_response()` 或 `fail_response()`

---

### services 业务逻辑层

**约定：**
- Service 函数接收 `db: AsyncSession` 参数
- Service 负责 `db.add()` 但**不 commit**，由路由层统一 `await db.commit()`
- 业务校验失败抛 `AppException`
- 写操作调用 `audit_service.log()`

**添加新 Service 示例：**

```python
# app/services/question_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AppException
from app.models.question import Question
from app.services.audit_service import log as audit_log

async def create_question(db: AsyncSession, stem: str, admin_id: int) -> Question:
    q = Question(stem=stem, status="draft", created_by=admin_id)
    db.add(q)
    await db.flush()  # 获取 ID，不提交
    await audit_log(db, admin_id, "CREATE_QUESTION", "questions", str(q.id))
    return q
    # 路由层负责 await db.commit()
```

---

## 认证机制

### 登录流程

```
POST /api/v1/admin/auth/login  { username, password }
    ↓
验证密码（bcrypt）
    ↓
检查账号状态：
  is_active = 0 → AUTH-003（已停用）
  is_active = 2 → LOGIN-003（首次登录需改密）
  is_active = 1 → 继续
    ↓
失败 ≥ 5 次 → locked_until 设置 30 分钟 → LOGIN-002
    ↓
成功 → 签发 JWT → 返回 TokenResp
```

### 受保护路由

所有受保护路由通过 `get_current_admin` 依赖注入验证：

```python
from app.dependencies import get_current_admin

@router.get("/protected")
async def protected_route(admin: AdminUser = Depends(get_current_admin)):
    ...
```

验证链路：
1. 解析 `Authorization: Bearer {token}` Header
2. 验证 JWT 签名和过期时间
3. 查询 Redis 黑名单 `blacklist:{jti}`
4. 检查 `role == SUPER_ADMIN`
5. 查询 AdminUser 是否存在且未停用

### 退出登录

```
POST /api/v1/admin/auth/logout
```

将当前 Token 的 `jti` 写入 Redis 黑名单，TTL = Token 剩余有效期，自动过期无需手动清理。

---

## 统一规范

### 响应格式

所有接口返回统一结构：

```json
{
  "status": "success",   // "success" | "fail" | "error"
  "code": 0,             // 0=成功；字符串=业务错误码
  "msg": "操作成功",
  "data": {}             // 成功时为数据，失败时为 null
}
```

### 错误码体系

| 前缀 | 说明 | 常见示例 |
|------|------|---------|
| `AUTH-*` | 认证/Token | `AUTH-001`=Token 无效, `AUTH-003`=权限不足 |
| `LOGIN-*` | 登录流程 | `LOGIN-001`=密码错误, `LOGIN-002`=账号锁定, `LOGIN-003`=需改初始密码 |
| `BIND-*` | 家长绑定 | `BIND-002`=绑定数超限 |
| `COGQ-*` | 五力测试题 | `COGQ-001`=题目数超上限 |
| `SYS-*` | 系统错误 | `SYS-000`=未知异常 |

HTTP 状态码映射：
- `200` 成功 | `400` 参数/业务错误 | `401` 未认证 | `403` 权限不足/锁定 | `404` 不存在 | `409` 冲突 | `429` 限流 | `500` 服务器错误

### 分页规范

**请求参数（Query Params）：**

```
?limit=20&before_id=5000
```

- `limit`：每页数量，默认 20，最大 100
- `before_id`：上一页最后一条记录的 ID（第一页不传）
- **禁止 OFFSET 分页**（大数据量性能差）

**响应结构：**

```json
{
  "status": "success",
  "data": {
    "list": [...],
    "total": 1280,
    "has_more": true,
    "next_cursor": 5000
  }
}
```

---

## 环境变量

`.env.example` 中所有字段：

```ini
# 数据库（必须）
DATABASE_URL=postgresql+asyncpg://suliang@localhost:5432/mesh_edu

# Redis（必须，用于 JWT 黑名单）
REDIS_URL=redis://localhost:6379/0

# JWT（生产环境必须修改 SECRET_KEY）
JWT_SECRET_KEY=your-64-char-random-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8

# 应用
APP_ENV=development          # development | production
APP_DEBUG=true               # false 时隐藏错误详情

# 前端 CORS 白名单（JSON 数组格式）
CORS_ORIGINS=["http://localhost:5174"]

# 数据看板 Redis 缓存 TTL（秒）
DASHBOARD_CACHE_TTL=300
```

---

## 数据库

- **数据库名：** `mesh_edu`
- **用户：** `suliang`
- **连接：** `localhost:5432`
- **状态：** 已建好（34 张表，含种子数据）

后端通过 SQLAlchemy 2.0 async 连接，不使用 Alembic 管理现有表结构。`migrations/versions/` 目录供未来新增表时使用。

```bash
# 连接数据库
psql -U suliang -d mesh_edu

# 查看所有表
\dt

# 检查现有迁移状态
uv run alembic current
```

---

## 测试

```bash
# 运行全部测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_auth.py -v

# 查看覆盖率
uv run pytest tests/ --tb=short
```

**测试约定：**
- 使用 `fakeredis` mock Redis（`conftest.py` 中自动注入，无需真实 Redis）
- 需要真实 PostgreSQL（`mesh_edu`）连接
- 所有测试共享 session 级 event loop（避免 asyncpg 连接池问题）
- 测试文件以 `test_` 开头，测试函数以 `async def test_` 开头

---

## 代码规范

```bash
# 检查（lint + import 排序）
uv run ruff check app/ tests/

# 自动修复
uv run ruff check app/ tests/ --fix

# 格式化
uv run ruff format app/ tests/

# 类型检查
uv run mypy app/
```

**规范要点：**
- 行宽 100 字符
- Python 3.13+ 类型注解（`str | None` 而非 `Optional[str]`）
- import 按 stdlib → third-party → local 分组排序
- 禁止裸 `except:` 和未使用的 import

---

## 已实现接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/health` | 服务健康检查 | 无 |
| `POST` | `/api/v1/admin/auth/login` | 管理员登录，返回 JWT | 无 |
| `POST` | `/api/v1/admin/auth/logout` | 退出登录，撤销 Token | 需要 |

---

## 待实现模块

以下模块路由骨架已注册，Service 层待填充：

| 模块 | 路由前缀 | 接口文档章节 |
|------|---------|------------|
| 题库管理 | `/api/v1/admin/questions` | §9.1 |
| 五力测试题维护 | `/api/v1/admin/cognitive-questions` | §9.3 |
| 训练参数配置 | `/api/v1/admin/training` | §9.4 |
| 系统参数 + 启发策略 | `/api/v1/admin/system-configs` | §9.5、§9.6 |
| 数据看板 | `/api/v1/admin/dashboard` | §9.7 |
| 用户管理 | `/api/v1/admin/students`、`/parents`、`/admin-users` | §9.8 |
| 审计日志 | `/api/v1/admin/audit-logs` | §9.9 |

**添加新模块步骤：**
1. 在 `app/schemas/{module}.py` 填充 Pydantic Schema
2. 在 `app/services/{module}_service.py` 实现业务逻辑
3. 在 `app/api/v1/admin/{module}.py` 填充路由处理函数
4. 在 `app/api/v1/admin/__init__.py` 取消注释对应路由注册

---

## 接口文档

| 文档 | 地址 |
|------|------|
| Swagger UI（交互式） | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |
| OpenAPI JSON | http://localhost:8000/api/openapi.json |

接口设计说明书：`docs/4.架构设计/06_接口设计说明书.md`

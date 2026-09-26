# MESH Backend

MESH AI 助教平台 · 后端服务（后台管理 + 小程序端）

---

## 目录

- [项目简介](#项目简介)
- [技术栈](#技术栈)
- [快速启动](#快速启动)
- [目录结构](#目录结构)
- [架构设计](#架构设计)
- [认证机制](#认证机制)
- [统一规范](#统一规范)
- [环境变量](#环境变量)
- [数据库](#数据库)
- [测试](#测试)
- [代码规范](#代码规范)
- [已实现接口](#已实现接口)
- [AI 大模型集成](#ai-大模型集成)
- [接口文档](#接口文档)

---

## 项目简介

本服务同时提供两端 API：

| 端 | Base URL | 认证方式 | 说明 |
|----|----------|---------|------|
| **后台管理** | `/api/v1/admin/` | JWT（管理员，8小时） | SUPER_ADMIN / ADMIN 角色，题库、五力测试题、训练配置、用户管理、看板 |
| **微信小程序** | `/api/v1/` | JWT（学生/家长，7天 Access + 30天 Refresh） | 登录注册、五力测试、个性化训练、错题集、AI 助教 |

---

## 技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web 框架 | FastAPI | ≥ 0.115 | 原生 async，自动 OpenAPI 文档 |
| ASGI 服务器 | uvicorn | ≥ 0.30 | 开发 `--reload`，生产 gunicorn 管理 |
| ORM | SQLAlchemy 2.0 | ≥ 2.0.36 | async 模式，`Mapped`/`mapped_column` 语法 |
| DB 驱动 | asyncpg | ≥ 0.30 | PostgreSQL 高性能异步驱动 |
| 数据校验 | Pydantic v2 | ≥ 2.10 | Request/Response schema |
| 配置管理 | pydantic-settings | ≥ 2.6 | 从 `.env` 读取强类型配置 |
| 数据库迁移 | Alembic | ≥ 1.14 | async engine，支持未来迁移 |
| 认证 | PyJWT | ≥ 2.10 | HS256 签名 |
| 密码哈希 | bcrypt | ≥ 4.0 | 直接调用（不经 passlib）|
| 缓存/黑名单 | redis-py async | ≥ 5.2 | JWT 黑名单、看板缓存 |
| 日志 | loguru | ≥ 0.7.3 | 结构化日志，自动轮转 |
| 依赖管理 | uv | — | 快速安装，锁定版本 |
| 代码规范 | ruff | ≥ 0.8 | lint + format 一体 |
| 测试 | pytest + httpx | — | async 支持，fakeredis mock |

---

## 快速启动

### 前置要求

- Python 3.13+
- PostgreSQL 16+（数据库 `mesh_edu` 已存在）
- Redis 7+（或使用 fakeredis 开发环境自动 mock）

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
# 编辑 .env，修改 JWT_SECRET_KEY（必须）和 WX_APPID/WX_SECRET（小程序登录必须）
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 启动服务

```bash
uv run uvicorn app.main:app --reload --port 8000
```

### 4. 验证运行

```
GET  http://localhost:8000/health           → {"code":200,"data":{"status":"healthy"}}
GET  http://localhost:8000/api/docs         → Swagger UI（所有接口可交互调试）
GET  http://localhost:8000/api/openapi.json → OpenAPI JSON
```

### 默认管理员账号

```
用户名：admin
密  码：qwer123#
```

### 小程序开发模式

微信登录需配置 `WX_APPID` 和 `WX_SECRET`。短信验证码开发阶段固定为 `123456`，无需真实短信平台。

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
│   ├── dependencies.py         # 公共依赖注入：get_db()、get_current_admin()、get_current_student()
│   │
│   ├── core/                   # ── 基础设施层（无业务逻辑）──────────────────
│   │   ├── config.py           # Settings（pydantic-settings 读 .env）含 WX_APPID/WX_SECRET
│   │   ├── database.py         # async engine + AsyncSession 工厂 + get_db()
│   │   ├── redis.py            # Redis 连接池单例
│   │   ├── security.py         # JWT 签发/解码（管理员 8h / 学生 7d+30d Refresh）
│   │   ├── response.py         # 统一响应：ok_response() / fail_response()
│   │   ├── exceptions.py       # AppException + 全局异常处理器
│   │   ├── middleware.py       # RequestLogMiddleware（请求日志 + 耗时）
│   │   └── logger.py           # loguru 配置
│   │
│   ├── models/                 # ── ORM 模型层（映射现有数据库全部表）──────────
│   │   ├── base.py             # Base（DeclarativeBase）+ TimestampMixin
│   │   ├── admin.py            # AdminUser
│   │   ├── question.py         # Question、QuestionAnalysis
│   │   ├── cognitive.py        # CognitiveTestQuestion
│   │   ├── knowledge.py        # Subject / Grade / Semester / Chapter / KnowledgePoint
│   │   ├── training.py         # TrainingDimensionConfig、TrainingConfigVersion
│   │   │                       # TrainingSession、TrainingAnswerRecord
│   │   ├── student.py          # Student（含 semester 字段）、ParentStudentBinding
│   │   │                       # FivePowerProfile、FivePowerTrainingProfile
│   │   │                       # TestSession、TestAnswerRecord、WrongAnswerRecord
│   │   │                       # StudentKpStat、InviteCode、SmsCode
│   │   ├── ai.py               # AiChatSession、AiChatMessage、AiStrategyEvent
│   │   │                       # AiHeuristicStrategy、SystemConfig
│   │   │                       # StudentAiPromptSummary、StudentPromptInsight
│   │   └── audit.py            # AdminAuditLog
│   │
│   ├── schemas/                # ── Pydantic 校验层 ────────────────────────────
│   │   ├── common.py           # PageResp[T]、PageParams
│   │   ├── auth.py             # LoginReq、TokenResp、AdminInfo
│   │   └── users.py            # 用户管理相关 Schema
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── admin/          # ── 后台管理路由（prefix: /api/v1/admin）──────
│   │       │   ├── __init__.py # 汇总注册
│   │       │   ├── auth.py     # ✅ 管理员登录 / 2FA / 退出
│   │       │   ├── users.py    # ✅ 学生/家长/管理员账号管理
│   │       │   ├── cognitive.py# ✅ 五力测试题 CRUD + 发布/下架/软删除
│   │       │   ├── questions.py# ✅ 题库管理（录入/模型分析/发布/驳回）
│   │       │   ├── training.py # ✅ 五维度训练参数配置
│   │       │   ├── system.py   # ✅ 系统参数 + 启发策略
│   │       │   ├── dashboard.py# ✅ 数据看板
│   │       │   └── audit.py    # ✅ 审计日志（含权限分级）
│   │       │
│   │       └── miniapp/        # ── 小程序端路由（prefix: /api/v1）──────────
│   │           ├── __init__.py # 汇总注册
│   │           ├── auth.py     # ✅ 微信登录 / 短信验证 / 绑手机 / 刷新Token / 退出 / 邀请码
│   │           ├── profile.py  # ✅ 个人信息 / 五力画像 / 知识点练习统计
│   │           ├── test.py     # ✅ 五力认知测试（获取题卷/提交/完成/结果轮询/历史）
│   │           ├── training.py # ✅ 个性化训练（五维度会话/答题/错题统计/完成）
│   │           ├── wrong_answers.py # ✅ 错题集（列表/发起AI复盘）
│   │           ├── assistant.py     # ✅ AI助教（会话管理/发消息/历史/评分）[Mock]
│   │           └── knowledge.py     # ✅ 知识点导航（学科/年级/知识点，自动学期过滤）
│   │
│   └── services/               # ── 业务逻辑层 ────────────────────────────────
│       ├── auth_service.py     # ✅ 管理员登录验证、锁定、JWT
│       ├── audit_service.py    # ✅ 写 admin_audit_logs
│       ├── users_service.py    # ✅ 用户/家长/绑定管理、AI摘要
│       ├── cognitive_service.py# ✅ 五力测试题业务逻辑
│       └── questions_service.py# ✅ 题库管理（含模型分析 Mock）
│
├── migrations/                 # Alembic 迁移（供未来新增表使用）
│   ├── env.py
│   └── versions/
│
└── tests/
    ├── conftest.py             # pytest fixture：fakeredis + async HTTP client
    ├── test_auth.py            # 认证接口测试
    ├── test_core.py            # 核心工具测试
    ├── test_health.py          # 健康检查
    ├── test_integration.py     # 端到端集成测试
    └── test_models.py          # ORM 模型测试
```

> **图例：** ✅ 已完整实现 | [Mock] 占位实现，待接入大模型

---

## 架构设计

### 分层说明

```
┌─────────────────────────────────────────────────────┐
│  api 层（路由控制器）                                  │
│  解析请求、校验 Token、调用 service、返回响应           │
├─────────────────────────────────────────────────────┤
│  service 层（业务逻辑）                                │
│  所有业务规则、DB 操作编排、审计日志                   │
├─────────────────────────────────────────────────────┤
│  model 层（ORM）                                      │
│  映射 PostgreSQL 数据库表结构                          │
├─────────────────────────────────────────────────────┤
│  core 层（基础设施）                                   │
│  JWT、DB、Redis、配置、日志、异常处理                   │
└─────────────────────────────────────────────────────┘
```

### 请求链路示例

```
# 后台管理：POST /api/v1/admin/auth/login
HTTP Request → Middleware → api/auth.py → services/auth_service.py
    → models/admin.py → PostgreSQL → schemas/auth.py → ok_response()

# 小程序：POST /api/v1/auth/wx-login
HTTP Request → api/miniapp/auth.py
    → 调用微信 jscode2session API（获取 openid）
    → 查询/创建 Student → 签发 7天 JWT → ok_response()
```

---

## 认证机制

### 管理员认证（后台）

```
POST /api/v1/admin/auth/login  { username, password }
    ↓ bcrypt 验证密码
    ↓ 检查账号状态（is_active: 0=停用, 1=正常）
    ↓ 失败 ≥ 5 次 → 锁定 30 分钟
    ↓ 成功 → 签发 HS256 JWT（8小时）
```

**权限分级：**
- `SUPER_ADMIN`：全部功能 + 管理员账号管理
- `ADMIN`：除「管理员账号」Tab 外的全部功能

### 小程序学生认证

```
POST /api/v1/auth/wx-login  { code, nickname? }
    ↓ 调用微信 jscode2session（code → openid）
    ├─ 已注册 → 更新登录时间 → 签发 JWT（7天 Access + 30天 Refresh）
    └─ 新用户 → 返回 temp_token → 引导绑定手机号

POST /api/v1/auth/bind-phone-with-token
    ↓ 验证 temp_token + 短信验证码（开发固定 123456）
    ↓ 创建 Student 记录 → 签发正式 JWT
```

### 受保护路由依赖

```python
# 后台路由
from app.dependencies import get_current_admin, require_super_admin

@router.get("/admin-only")
async def admin_route(admin: AdminUser = Depends(require_super_admin)):
    ...

# 小程序路由
from app.dependencies import get_current_student

@router.get("/profile")
async def profile(student: Student = Depends(get_current_student)):
    ...
```

---

## 统一规范

### 响应格式

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {}
}
```

失败时 `code` 为 HTTP 状态码，`data` 为 `null`。

### 错误码

| 前缀 | 说明 |
|------|------|
| `TRAIN-001` | 未完成五力测试 |
| `TRAIN-002` | 范围内题目不足 |
| `TRAIN-003` | 错题集为空 |
| `COGQ-001` | 五力测试题已达上限 |
| `BIND-002` | 绑定家长数超限 |

### 分页规范（后台管理端）

```
请求：?page=1&limit=20
响应：{ list, total, page, limit, total_pages }
```

---

## 环境变量

```ini
# 数据库（必须）
DATABASE_URL=postgresql+asyncpg://suliang@localhost:5432/mesh_edu

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT（生产环境必须修改）
JWT_SECRET_KEY=your-64-char-random-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8          # 管理员 Token 有效期（小程序固定 7天/30天）

# 微信小程序（小程序登录必须配置）
WX_APPID=                   # 微信小程序 AppID
WX_SECRET=                  # 微信小程序 AppSecret

# 应用
APP_ENV=development
APP_DEBUG=true
CORS_ORIGINS=["http://localhost:5174"]

# 看板缓存
DASHBOARD_CACHE_TTL=300
```

---

## 数据库

- **数据库名：** `mesh_edu`
- **用户：** `suliang` / **端口：** `5432`
- **状态：** 已建好（含全部表结构和种子数据）

```bash
# 连接数据库
psql -U suliang -d mesh_edu

# 查看所有表
\dt
```

> 后端通过 SQLAlchemy 2.0 async 连接。`migrations/versions/` 供未来新增表时使用，现有表不通过 Alembic 管理。

---

## 测试

```bash
# 运行全部测试
uv run pytest tests/ -v

# 运行特定模块
uv run pytest tests/test_auth.py -v
```

**约定：**
- 使用 `fakeredis` mock Redis（`conftest.py` 自动注入，无需真实 Redis）
- 需要真实 PostgreSQL 连接（`mesh_edu`）
- 所有测试函数以 `async def test_` 开头

---

## 代码规范

```bash
uv run ruff check app/ tests/ --fix   # lint + 自动修复
uv run ruff format app/ tests/        # 格式化
uv run mypy app/                      # 类型检查
```

---

## 已实现接口

### 后台管理（`/api/v1/admin/`）

| 模块 | 接口数 | 说明 |
|------|--------|------|
| 认证 | 3 | 登录 / 2FA / 退出 |
| 用户管理 | 11 | 学生/家长/管理员 CRUD + 绑定解绑 + 知识点统计 + AI摘要 |
| 题库管理 | 8 | 录入/模型分析/发布/驳回（Mock AI）|
| 五力测试题 | 5 | 列表/新增/编辑/状态变更/软删除 |
| 训练配置 | 5 | 五维度参数版本化管理 |
| 系统参数 | 4 | 参数热更新 + 启发策略管理 |
| 数据看板 | 3 | 统计指标（Mock 数据）|
| 审计日志 | 1 | 权限分级查询 |

### 小程序端（`/api/v1/`）

| 模块 | 接口数 | 说明 |
|------|--------|------|
| 认证 | 6 | 微信登录 / 短信 / 绑手机 / 刷新Token / 退出 / 邀请码 |
| 个人信息 | 3 | 获取/更新信息 / 五力画像 / 知识点统计 |
| 知识导航 | 3 | 学科/年级/知识点（自动学期过滤）|
| 五力测试 | 5 | 题卷/答题/评分/结果轮询/历史 |
| 训练 | 6 | 五维度选题 / 答题 / RAG（Mock）/ 完成 / 错题统计 |
| 错题集 | 2 | 列表 / 发起AI复盘 |
| AI助教 | 6 | 会话管理 / 发消息（Mock）/ 历史 / 评分 / 结束 |

---

## AI 大模型集成

### 当前状态（Mock 占位）

以下功能已搭建接口框架，返回占位数据，待接入大模型后替换：

| 功能 | 文件 | 替换位置 |
|------|------|---------|
| 题干模型分析 | `services/questions_service.py` | `analyze()` 函数 |
| 训练 RAG 解题引导 | `api/v1/miniapp/training.py` | `get_rag_status()` |
| AI助教对话回复 | `api/v1/miniapp/assistant.py` | `send_message()` |
| 五力测试评分 | `api/v1/miniapp/test.py` | `complete_test()` |

### 接入 Anthropic API

**第一步：获取 API Key**

前往 [console.anthropic.com](https://console.anthropic.com) 注册并创建 API Key。

**第二步：配置**

```bash
# .env 中添加
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-opus-4-6

# 安装 SDK
uv add anthropic
```

**第三步：替换 Mock 实现**

以题库分析为例：

```python
# app/services/questions_service.py
import anthropic, json

async def analyze(db: AsyncSession, question_id: int, operator_id: int):
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    question = await db.get(Question, question_id)

    message = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"分析题目：{question.stem}\n返回JSON含：subject、grade、difficulty、five_power_weights（整数合计10）..."
        }]
    )
    result = json.loads(message.content[0].text)
    # 写入 question_analyses 表...
```

### 切换其他大模型

| 模型 | 替换方式 |
|------|---------|
| OpenAI GPT | `client = openai.AsyncOpenAI(api_key=...)` |
| 阿里通义千问 | OpenAI 兼容接口，`base_url="https://dashscope.aliyuncs.com/..."` |
| 字节豆包 | OpenAI 兼容接口，`base_url="https://ark.cn-beijing.volces.com/..."` |

---

## 接口文档

| 文档 | 地址 |
|------|------|
| Swagger UI（交互式） | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |
| OpenAPI JSON | http://localhost:8000/api/openapi.json |

接口设计说明书：`docs/4.架构设计/06_接口设计说明书.md`

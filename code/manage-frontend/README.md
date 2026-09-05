# MESH Admin Frontend

MESH AI 助教平台 - 后台管理系统前端。面向平台超级管理员，提供题库管理、AI 标注审核、训练配置、学生运营、数据看板等完整管理能力。

---

## 目录

- [技术栈](#技术栈)
- [快速启动](#快速启动)
- [项目结构](#项目结构)
- [架构设计](#架构设计)
  - [分层说明](#分层说明)
  - [请求链路](#请求链路)
  - [认证机制](#认证机制)
  - [Mock 数据](#mock-数据)
  - [设计系统](#设计系统)
- [路由表](#路由表)
- [模块详解](#模块详解)
  - [登录认证](#1-登录认证-loginview)
  - [数据看板](#2-数据看板-dashboardview)
  - [题库管理](#3-题库管理-questionlistview--questionformview)
  - [AI 标注审核](#4-ai-标注审核-annotationview)
  - [五力测试题维护](#5-五力测试题维护-cognitivetestview)
  - [训练配置管理](#6-训练配置管理-trainingconfigview)
  - [系统参数配置](#7-系统参数配置-systemconfigview)
  - [学生管理](#8-学生管理-studentlistview--studentdetailview)
  - [审计日志](#9-审计日志-auditlogview)
- [API 层](#api-层)
- [类型系统](#类型系统)
- [状态管理](#状态管理)
- [工具函数](#工具函数)
- [对接后端指南](#对接后端指南)

---

## 技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | Vue 3 | ^3.4 | Composition API + `<script setup>` |
| 构建 | Vite | ^5.3 | 开发服务器 / 打包 |
| 类型 | TypeScript | ^5.4 | 全量类型覆盖 |
| UI 组件 | Element Plus | ^2.7 | 表单、表格、弹窗等基础组件 |
| 图表 | ECharts | ^5.5 | 趋势折线图、五力雷达图 |
| HTTP | Axios | ^1.7 | 请求封装、拦截器 |
| 路由 | Vue Router | ^4.3 | Hash-less History 模式 |
| 状态 | Pinia | ^2.1 | 登录态持久化 |
| 日期 | Day.js | ^1.11 | 时间格式化、相对时间 |
| Mock | vite-plugin-mock | ^3.0 | 开发环境接口模拟 |

---

## 快速启动

```bash
# 安装依赖
npm install

# 启动开发服务器（含 Mock）
npm run dev
# 访问 http://localhost:5174

# 类型检查
npx vue-tsc --noEmit

# 生产构建
npm run build
```

**默认测试账号**

| 字段 | 值 |
|------|----|
| 账号 | `admin001` |
| 密码 | `password123` |
| 短信验证码 | `123456` |

---

## 项目结构

```
manage-frontend/
├── index.html
├── vite.config.ts          # Vite 配置（含 Mock 插件）
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── package.json
└── src/
    ├── main.ts             # 应用入口（注册插件、开启暗色模式）
    ├── App.vue             # 根组件
    ├── style.css           # 全局设计系统（CSS 变量 + Element Plus 暗色覆盖）
    │
    ├── api/
    │   ├── request.ts      # Axios 实例（拦截器、401 处理）
    │   └── index.ts        # 所有业务 API 函数
    │
    ├── mock/
    │   └── index.ts        # Mock 数据（覆盖全部接口）
    │
    ├── router/
    │   └── index.ts        # 路由配置（含路由守卫）
    │
    ├── stores/
    │   └── auth.ts         # 登录态 Pinia Store
    │
    ├── types/
    │   └── index.ts        # 所有 TypeScript 接口和枚举
    │
    ├── utils/
    │   ├── constants.ts    # Token 键名、颜色映射等常量
    │   └── format.ts       # 日期格式化、相对时间、百分比等工具
    │
    ├── layouts/
    │   └── AdminLayout.vue # 主框架布局（侧边栏 + Topbar + 内容区）
    │
    └── views/
        ├── login/
        │   └── LoginView.vue            # 登录页（视频背景 + 药丸导航 + 两步验证）
        ├── dashboard/
        │   └── DashboardView.vue        # 数据看板
        ├── questions/
        │   ├── QuestionListView.vue     # 题库列表
        │   └── QuestionFormView.vue     # 新增 / 编辑题目
        ├── annotations/
        │   └── AnnotationView.vue       # AI 标注审核
        ├── cognitive-test/
        │   └── CognitiveTestView.vue    # 五力测试题维护
        ├── training-config/
        │   └── TrainingConfigView.vue   # 训练配置管理
        ├── system-config/
        │   └── SystemConfigView.vue     # 系统参数 + 启发策略
        ├── students/
        │   ├── StudentListView.vue      # 学生列表
        │   └── StudentDetailView.vue    # 学生详情
        └── audit-logs/
            └── AuditLogView.vue         # 审计日志
```

---

## 架构设计

### 分层说明

```
┌─────────────────────────────────────────────────────┐
│  Views（页面）                                        │
│  各业务模块 .vue 文件，负责 UI 渲染和用户交互         │
├─────────────────────────────────────────────────────┤
│  Layouts（布局）                                      │
│  AdminLayout.vue 提供侧边栏 + Topbar 外壳             │
├─────────────────────────────────────────────────────┤
│  Stores（状态）                                       │
│  Pinia auth store，管理登录态，持久化到 localStorage  │
├─────────────────────────────────────────────────────┤
│  API 层                                              │
│  api/index.ts 封装业务接口，api/request.ts 处理鉴权  │
├─────────────────────────────────────────────────────┤
│  Mock 层（开发环境）                                  │
│  mock/index.ts 拦截全部接口，返回模拟数据             │
├─────────────────────────────────────────────────────┤
│  Types（类型）                                        │
│  types/index.ts 所有接口、枚举、Label 映射            │
└─────────────────────────────────────────────────────┘
```

### 请求链路

```
View 调用 api/index.ts 函数
  → api/request.ts（Axios 实例）
    → 请求拦截器：注入 Authorization: Bearer <token>
    → 开发环境：vite-plugin-mock 拦截并返回 mock 数据
    → 生产环境：转发至后端 /api/v1/admin/*
    → 响应拦截器：
        ├─ status === 'success' → 返回 data.data
        ├─ status === 'fail'    → ElMessage.error(msg)
        └─ HTTP 401             → 清除 token，跳转登录页
```

**统一响应格式**（后端约定）

```json
{
  "status": "success",
  "code": 0,
  "msg": "操作成功",
  "data": { ... }
}
```

分页列表接口的 `data` 结构：

```json
{
  "list": [],
  "total": 100,
  "has_more": true,
  "next_cursor": 20
}
```

> 所有列表使用 **Keyset Pagination（游标分页）**，参数为 `cursor` + `limit`，禁止 OFFSET 分页。

### 认证机制

采用两步登录（账号密码 + 短信 2FA）：

```
Step 1：POST /auth/login（账号 + 密码）
  → 返回 session_token（5 分钟有效，仅用于 2FA）

Step 2：POST /auth/verify-2fa（session_token + 短信验证码）
  → 返回 access_token（8 小时有效，无 refresh_token）

后续请求：Header Authorization: Bearer <access_token>
  → 8 小时到期后须重新走完整 2FA 流程
```

Token 存储在 `localStorage`，键名为 `mesh_admin_token`。路由守卫在每次导航时校验 token 是否存在，不存在则强制跳转 `/login`。

### Mock 数据

开发环境通过 `vite-plugin-mock` 拦截全部 `/api/v1/admin/*` 请求，无需启动后端即可完整运行。

覆盖接口清单（`src/mock/index.ts`）：

| 模块 | 覆盖接口数 |
|------|-----------|
| 认证 | 3（login / verify-2fa / logout） |
| 题库 | 8（CRUD + publish / archive / batch-import） |
| 标注 | 3（list / confirm / batch-confirm） |
| 五力测试题 | 2（list / update） |
| 训练配置 | 3（list / active / create） |
| 系统参数 | 2（list / update） |
| 启发策略 | 3（list / update / reorder） |
| 学生管理 | 3（list / detail / bind-parent） |
| 审计日志 | 2（list / detail） |
| 数据看板 | 2（stats / token-trend） |

切换为真实后端：修改 `vite.config.ts` 中 `viteMockServe` 的 `enable: false` 即可。

### 设计系统

视觉风格参考 Linear / Vercel Dashboard，全局暗色主题。核心设计变量定义在 `src/style.css`：

**背景层级**

```css
--bg-0: #09090b   /* 最深，代码块背景 */
--bg-1: #0f1013   /* 页面基底 */
--bg-2: #141518   /* 卡片 / 侧边栏 */
--bg-3: #1c1d22   /* 弹窗 / 次级卡片 */
--bg-4: #24252c   /* 悬浮 / 标签背景 */
```

**语义色**

```css
--blue:   #3b82f6   /* 主色调，CTA / 链接 / 主要标注 */
--green:  #22c55e   /* 成功 / 已发布 / 已确认 */
--amber:  #f59e0b   /* 警告 / 待处理 / 草稿 */
--red:    #ef4444   /* 错误 / 危险操作 / 已驳回 */
--purple: #a855f7   /* 迁移力维度 */
```

**五力维度颜色**

```css
--power-insight:   #22c55e   /* 洞察力 */
--power-construct: #ef4444   /* 建构力 */
--power-deduce:    #3b82f6   /* 推演力 */
--power-adapt:     #f59e0b   /* 调适力 */
--power-migrate:   #a855f7   /* 迁移力 */
```

**复用 CSS 类**

| 类名 | 用途 |
|------|------|
| `.surface` | 标准卡片容器（`bg-2` + 边框 + 圆角） |
| `.page-root` | 页面根容器（flex column + gap） |
| `.page-header` | 页面顶部标题行 |
| `.filter-bar` | 筛选条（flex + wrap + gap） |
| `.paginator` | 分页行（共 N 条 + 上一页/下一页） |
| `.power-badge--{POWER}` | 五力标签（INSIGHT/CONSTRUCT/DEDUCE/ADAPT/MIGRATE） |
| `.conf-badge--{high/mid/low}` | 置信度标签（绿/黄/红） |
| `.review-card` | 标注审核卡片 |
| `.id-chip` | ID 标签（等宽字体，深色背景） |
| `.num` | 等宽数字（tabular-nums） |
| `.mono` | 等宽字体 |
| `.json-viewer` | JSON 差异查看器 |

---

## 路由表

| 路径 | 组件 | 说明 |
|------|------|------|
| `/login` | `LoginView` | 公开页，已登录自动跳转首页 |
| `/dashboard` | `DashboardView` | 默认首页，需登录 |
| `/questions` | `QuestionListView` | 题目列表 |
| `/questions/create` | `QuestionFormView` | 新增题目 |
| `/questions/:id/edit` | `QuestionFormView` | 编辑题目（同一组件，`isEdit` 区分） |
| `/annotations` | `AnnotationView` | AI 标注审核 |
| `/cognitive-test` | `CognitiveTestView` | 五力测试题维护 |
| `/training-config` | `TrainingConfigView` | 训练配置管理 |
| `/system-config` | `SystemConfigView` | 系统参数 + 启发策略 |
| `/students` | `StudentListView` | 学生列表 |
| `/students/:id` | `StudentDetailView` | 学生详情 |
| `/audit-logs` | `AuditLogView` | 审计日志 |

路由守卫逻辑：未持有 token 的请求一律重定向至 `/login`；已登录访问 `/login` 自动跳转 `/`。

---

## 模块详解

### 1. 登录认证（`LoginView`）

**文件：** `src/views/login/LoginView.vue`

**设计特点：**
- 全屏视频背景（`autoplay muted loop playsinline`）
- 居中双药丸导航：左侧圆形 Logo 容器 + 右侧链接药丸
- 左下对齐英雄区域：状态徽章 + 主标题 + 副标题 + CTA 按钮
- 右侧 Glassmorphism 登录卡（`backdrop-filter: blur(28px)`）

**两步登录流程：**

```
用户填写账号密码 → handleLogin()
  → POST /auth/login
  → 返回 session_token → 切换到 step 2（带过渡动画）

用户填写短信验证码 → handleVerify()
  → POST /auth/verify-2fa
  → 返回 access_token + 管理员信息
  → authStore.setAuth() 持久化
  → 路由跳转 /dashboard
```

**关键状态：**

| 变量 | 类型 | 说明 |
|------|------|------|
| `step` | `ref<1|2>` | 当前登录步骤 |
| `sessionToken` | `ref<string>` | Step 1 返回，用于 Step 2 请求 |
| `loading` | `ref<boolean>` | 按钮 loading 状态 |

---

### 2. 数据看板（`DashboardView`）

**文件：** `src/views/dashboard/DashboardView.vue`

**功能点：**

| 区块 | 说明 |
|------|------|
| 4 个指标卡 | 总学生数 / 今日训练会话 / RAG 调用 / Token 成本，含今日增量和趋势 |
| 题库状态 | 已发布题目数 / 待审核标注数（可点击跳转） / 待向量化数 |
| 五力覆盖分布 | 水平条形图展示各维度题目占比 |
| Token 消耗趋势 | ECharts 面积折线图，支持 7/14/30 天切换 |
| 模块成本分布 | 训练模块 / AI 助教 / 测试模块的成本占比和金额 |

**API 调用：**

```ts
dashboardApi.getStats(date?)         // 当日统计数据
dashboardApi.getTokenTrend(days)     // Token 趋势（数组，按天）
```

**ECharts 配置要点：**
- 初始化时使用 `echarts.init(el, 'dark')` 不直接生效，通过手动设置各轴颜色保证暗色主题
- `backgroundColor: 'transparent'` 防止遮挡页面背景
- 面积渐变使用 `echarts.graphic.LinearGradient`
- 窗口 resize 时调用 `lineChart.resize()`

---

### 3. 题库管理（`QuestionListView` + `QuestionFormView`）

#### 题目列表（`QuestionListView`）

**文件：** `src/views/questions/QuestionListView.vue`

**功能点：**

| 功能 | 实现方式 |
|------|---------|
| 多维度筛选 | 关键词 / 知识点 / 五力 / 难度 / 状态 / 标注状态，`filter-bar` 布局 |
| 游标分页 | `cursor` + `limit=20`，上一页 / 下一页按钮 |
| 题干摘要 | 截取前 65 字符，超出显示 `…` |
| 标注状态展示 | 置信度百分比 + 置信度 badge（高/中/低） |
| 向量化状态展示 | `embed-badge`（completed/pending/failed 三态） |
| 发布题目 | 确认弹窗 → `questionApi.publish(id)` |
| 下架题目 | 确认弹窗 → `questionApi.archive(id)` |
| 删除草稿 | 确认弹窗 → `questionApi.delete(id)` |
| 批量导入 | JSON 文件上传弹窗（`el-upload` drag 模式） |

**题目状态流转：**

```
draft（草稿）
  ├─ 发布 → published（已发布）→ 触发 Celery 向量化
  │            └─ 下架 → archived（已归档）
  └─ 删除 → 软删除（deleted_at 标记）
```

#### 题目表单（`QuestionFormView`）

**文件：** `src/views/questions/QuestionFormView.vue`

通过 `route.params.id` 判断新增 / 编辑模式（`isEdit` computed）。

**三个表单区块：**

| 区块 | 字段 |
|------|------|
| 基础信息 | 知识点、题型、难度 |
| 题目内容 | 题干（textarea）、配图（可选上传）、参考解析（textarea） |
| 五力标注 | 主训练力、辅助训练力、典型错误、主力训练点、迁移方向（Tag 可增删） |

**迁移方向 Tag 交互：**
- 已有 tag 点击 × 删除
- 点击"+ 添加方向"显示 `el-input`，`Enter` 或 `blur` 确认新增

---

### 4. AI 标注审核（`AnnotationView`）

**文件：** `src/views/annotations/AnnotationView.vue`

**功能点：**

| 功能 | 说明 |
|------|------|
| 统计栏 | 待审核总数 / 高置信度可批量数 / 置信度范围滑块（实时过滤） |
| 批量确认 | 一键确认置信度 ≥ 85% 的所有标注（附确认弹窗） |
| 逐题审核卡 | 展示题干摘要 / AI 标注主力 + 置信度 + 标注理由 |
| 人工确认 | 下拉选择确认主训练力 → `annotationApi.confirm()` |
| 驳回标注 | `annotationApi.reject()` |
| 跳过 | 不更改状态，提示已跳过 |
| 已处理展示 | 已确认 / 已驳回的卡片半透明，显示最终结果 |

**置信度分级规则：**

| 置信度 | Badge 样式 | 处理建议 |
|--------|------------|---------|
| ≥ 85% | `conf-badge--high`（绿色） | 可批量确认 |
| 60% - 85% | `conf-badge--mid`（黄色） | 人工逐题确认 |
| < 60% | `conf-badge--low`（红色） | 强制人工填写 |

**本地状态设计：**
- `confirmData`（`reactive Record<id, {primary_power}>`）：存储每条记录的人工确认选择，不污染原始 `annotations` 数组

---

### 5. 五力测试题维护（`CognitiveTestView`）

**文件：** `src/views/cognitive-test/CognitiveTestView.vue`

**功能点：**

| 功能 | 说明 |
|------|------|
| 20 题列表 | 展示题号 / 类型 / 题干摘要 / 目标维度 / 参考时间 |
| 展开行查看 | 展示各选项得分（最高分绿色高亮） |
| 展开行编辑 | 行内表单，修改各选项得分 + 参考时间 |
| OPEN 题权重矩阵 | 5 列（五力维度）× 4 行（选项 A/B/C/D）的数字表格 |
| 保存修改 | `cognitiveApi.update(id, data)` |

**注意事项：**
- 题目数量固定 20 道，不可增删
- `editingId` 控制同一时间只有一道题进入编辑态
- `expandedRows` 同步控制 `el-table` 展开行
- STANDARD 题：`option_scores` 记录各选项绝对得分
- OPEN 题：额外有 `option_force_weights`，各选项权重向量之和建议为 1.0

---

### 6. 训练配置管理（`TrainingConfigView`）

**文件：** `src/views/training-config/TrainingConfigView.vue`

**功能点：**

| 功能 | 说明 |
|------|------|
| 当前生效版本 | `el-descriptions` 展示全部参数，难度分布用彩色进度条 |
| 历史版本记录 | 只读表格，展示版本号 / 状态 / 关键参数 / 创建时间 |
| 创建新版本 | 弹窗表单，含难度比例总和 = 100% 的校验 |

**核心配置项：**

| 参数 | 说明 | 约束 |
|------|------|------|
| `questions_per_session` | 每次训练题数 | 3 - 10 |
| `dedup_window` | 近期去重窗口（题数） | 10 - 100 |
| `weak_threshold` | 弱力判定阈值（分） | 50 - 80 |
| `severe_weak_bonus` | 严重弱力选题加权 | 0 - 1 |
| `general_weak_bonus` | 一般弱力选题加权 | 0 - 1 |
| `difficulty_basic/advanced/challenge_pct` | 难度分布百分比 | 三者之和 = 100 |
| `rag_mode` | RAG 触发模式 | `all` / `wrong_only` / `disabled` |
| `rag_timeout_sec` | RAG 超时秒数 | 5 - 30 |
| `rag_similarity_threshold` | 向量相似度阈值 | 0.5 - 0.99 |
| `ewma_decay` | 训练画像 EWMA 衰减系数 | 0.1 - 0.5 |

**版本机制：**
- 任意时刻只有一个 `is_active=true` 的版本生效
- 创建新版本后，旧版本自动置为停用
- 历史版本只读，不可回滚（创建新版本覆盖即可）
- 已开始的训练会话继续使用旧版本参数（后端保证）

---

### 7. 系统参数配置（`SystemConfigView`）

**文件：** `src/views/system-config/SystemConfigView.vue`

**布局：** 左列（系统参数）+ 右列（启发策略），比例 15:9。

#### 系统参数（左列）

| 参数 key | 说明 | 默认值 |
|----------|------|--------|
| `active_llm_provider` | AI 模型供应商（tongyi / openai / claude） | tongyi |
| `max_chat_rounds` | 单会话最大对话轮数 | 30 |
| `rag_timeout_sec` | RAG 超时时间（秒） | 8 |
| `max_token_per_session` | Token 会话上限 | 15000 |
| `review_session_max_min` | 错题复盘时限（分钟） | 20 |
| `strategy_switch_threshold` | 策略切换阈值（无效次数） | 2 |
| `max_proactive_per_session` | AI 主动介入次数上限 | 3 |
| `sms_daily_limit` | 每日短信发送上限 | 10 |

所有修改热更新（无需重启服务），点击行末"修改"按钮弹出修改弹窗。

#### 启发策略库（右列）

9 种苏格拉底式启发策略，可通过 `el-switch` 启用 / 禁用。优先级数字越小越优先被 AI 选用。

| 策略 | 代码 | 适用维度 |
|------|------|---------|
| 苏格拉底提问 | S-SOCRATIC | 全维度 |
| 化简特例 | S-SIMPLIFY | 调适力 |
| 生活场景类比 | S-ANALOGY | 洞察力 / 建构力 |
| 空间想象 | S-SPATIAL | 洞察力 / 推演力 |
| 图示引导 | S-DIAGRAM | 洞察力 |
| 故事叙述 | S-STORY | 建构力 / 迁移力 |
| 反例证伪 | S-COUNTER | 推演力 / 调适力 |
| 节奏/模式感 | S-PATTERN | 建构力 / 推演力 |
| 已知知识类比 | S-KNOWN | 迁移力 |

---

### 8. 学生管理（`StudentListView` + `StudentDetailView`）

#### 学生列表（`StudentListView`）

**文件：** `src/views/students/StudentListView.vue`

**筛选条件：** 关键词（昵称/手机号）/ 年级 / 是否有五力画像

**表格列：** ID / 昵称 / 年级 / 科目（蓝色标签组） / 最弱力（五力 badge，未测试显示灰色标签）/ 训练次数 / 手机号（脱敏）/ 最后登录（相对时间）/ 操作（查看详情）

#### 学生详情（`StudentDetailView`）

**文件：** `src/views/students/StudentDetailView.vue`

**布局：** 左宽列（16/24）+ 右窄列（8/24）

**左列区块：**

| 区块 | 内容 |
|------|------|
| 基本信息 | `el-descriptions`：昵称、年级、科目、手机号、注册时间、最后登录 |
| 五力画像 | ECharts 雷达图（左）+ 五力分数进度条列表（右）+ AI 分析文字 |
| 训练统计 | 三格并排：累计训练次数 / 累计答题数 / 平均正确率（颜色区分优劣） |

**右列区块：**

| 区块 | 内容 |
|------|------|
| 已绑定家长 | 家长头像 + 昵称 + 绑定方式 + 绑定时间，最多 2 位 |
| 手动绑定 | 弹窗填写家长手机号，记录为 `bind_method=ADMIN` |

**雷达图配置要点：**

```ts
// 五力颜色对应各顶点
const POWER_COLORS = {
  INSIGHT: '#22c55e', CONSTRUCT: '#ef4444',
  DEDUCE: '#3b82f6', ADAPT: '#f59e0b', MIGRATE: '#a855f7'
}
// axisLine / splitLine / splitArea 设为低透明度白色适配暗色背景
// backgroundColor: 'transparent' 避免遮挡
```

**正确率颜色区分：**

| 正确率 | 颜色 | class |
|--------|------|-------|
| ≥ 70% | 绿色 | `.train-stat-val--good` |
| 50% - 70% | 默认 | - |
| < 50% | 红色 | `.train-stat-val--poor` |

---

### 9. 审计日志（`AuditLogView`）

**文件：** `src/views/audit-logs/AuditLogView.vue`

**功能点：**

| 功能 | 说明 |
|------|------|
| 多维度筛选 | 操作人账号 / 操作类型（下拉，8 种） / 时间范围（日期区间选择器） |
| 日志列表 | 时间 / 操作人（含"管理员"标签）/ 操作类型（语义色 badge）/ 操作对象（表名 + ID）/ IP 地址 |
| 操作详情弹窗 | `el-descriptions` 基础信息 + 修改前后 JSON diff（两列 `.json-viewer`） |

**操作类型配色规则：**

| 类型前缀 | 颜色 | 示例 |
|----------|------|------|
| DELETE / ARCHIVE | 红色 danger | DELETE_QUESTION |
| UPDATE / MODIFY | 黄色 warning | UPDATE_SYSTEM_CONFIG |
| CREATE / PUBLISH / CONFIRM | 绿色 success | CONFIRM_ANNOTATION |
| 其他 | 灰色 info | - |

**JSON diff 展示：**
- 左列（修改前）：`.json-viewer--before`，红色文字
- 右列（修改后）：`.json-viewer--after`，绿色文字

---

## API 层

所有接口函数集中在 `src/api/index.ts`，按业务模块分组导出。

**Base URL：** `/api/v1/admin`（开发环境由 Mock 拦截）

| 导出名 | 对应模块 | 主要方法 |
|--------|---------|---------|
| `authApi` | 认证 | `login` / `verify2fa` / `logout` |
| `questionApi` | 题库 | `getList` / `getOne` / `create` / `update` / `publish` / `archive` / `delete` / `batchImport` |
| `annotationApi` | 标注审核 | `getList` / `confirm` / `batchConfirm` / `reject` |
| `cognitiveApi` | 五力测试题 | `getList` / `update` |
| `trainingConfigApi` | 训练配置 | `getList` / `getActive` / `create` |
| `systemConfigApi` | 系统参数 | `getList` / `update` |
| `strategyApi` | 启发策略 | `getList` / `update` / `reorder` |
| `studentApi` | 学生管理 | `getList` / `getOne` / `bindParent` |
| `auditLogApi` | 审计日志 | `getList` / `getOne` |
| `dashboardApi` | 数据看板 | `getStats` / `getTokenTrend` |

---

## 类型系统

所有 TypeScript 类型定义集中在 `src/types/index.ts`。

**核心类型：**

```ts
// 五力枚举
type FivePower = 'INSIGHT' | 'CONSTRUCT' | 'DEDUCE' | 'ADAPT' | 'MIGRATE'

// 题目状态
type QuestionStatus = 'draft' | 'published' | 'archived'

// 标注状态
type AnnotationStatus = 'pending' | 'confirmed' | 'rejected'

// 难度
type Difficulty = 'basic' | 'advanced' | 'challenge'

// 通用分页响应
interface PaginatedResponse<T> {
  list: T[]
  total: number
  has_more: boolean
  next_cursor: number | null
}
```

**Label 映射对象（直接用于模板渲染）：**

```ts
FivePowerLabels       // { INSIGHT: '洞察力', ... }
QuestionStatusLabels  // { draft: '草稿', ... }
AnnotationStatusLabels
DifficultyLabels
```

---

## 状态管理

**`src/stores/auth.ts`** - Pinia Store，管理登录态。

```ts
// 读取
authStore.token        // JWT access_token
authStore.user         // { id, username, role }
authStore.isLoggedIn() // 是否已登录

// 写入
authStore.setAuth(token, user)  // 登录成功后调用，同步 localStorage
authStore.clearAuth()           // 退出登录后调用，清除 localStorage
```

持久化键名：`mesh_admin_token`（token）和 `mesh_admin_user`（用户信息 JSON）。

---

## 工具函数

**`src/utils/format.ts`**

```ts
formatDate(date, fmt?)  // ISO 字符串 → 'YYYY-MM-DD HH:mm:ss'（可自定义格式）
fromNow(date)           // ISO 字符串 → '3天前' / '昨天' 等相对时间
formatPercent(val)      // 0.65 → '65.0%'
formatCost(val)         // 1.23 → '$1.23'
```

**`src/utils/constants.ts`**

```ts
TOKEN_KEY           // localStorage key: 'mesh_admin_token'
USER_KEY            // localStorage key: 'mesh_admin_user'
FIVE_POWER_COLORS   // 五力 → 十六进制颜色映射
```

---

## 对接后端指南

### 1. 禁用 Mock，启用真实请求

修改 `vite.config.ts`：

```ts
viteMockServe({
  mockPath: 'src/mock',
  enable: false,   // 改为 false
})
```

### 2. 配置代理（跨域）

若后端与前端不同域，在 `vite.config.ts` 添加代理：

```ts
server: {
  port: 5174,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',   // 后端地址
      changeOrigin: true,
    }
  }
}
```

### 3. 接口约定核查清单

对接前确认以下后端约定与本项目一致：

- [ ] 响应格式：`{ status, code, msg, data }` 三态（`success` / `fail` / `error`）
- [ ] 分页参数：`cursor`（游标 ID）+ `limit`（条数），响应包含 `has_more` + `next_cursor`
- [ ] 认证 Header：`Authorization: Bearer <token>`
- [ ] 401 响应：token 失效时返回 HTTP 401，前端自动跳转登录页
- [ ] 时间格式：ISO 8601（`2026-08-30T10:00:00Z`，UTC）
- [ ] Base URL：`/api/v1/admin`（所有管理后台接口统一前缀）

### 4. 扩展新模块步骤

1. 在 `src/types/index.ts` 添加数据接口类型
2. 在 `src/api/index.ts` 新增 API 函数组
3. 在 `src/mock/index.ts` 添加对应 Mock 路由
4. 在 `src/views/` 下新建模块目录和 `.vue` 文件
5. 在 `src/router/index.ts` 注册路由
6. 在 `src/layouts/AdminLayout.vue` 侧边栏添加导航项

---

*文档基于代码版本 v1.0.0，2026-09-05*

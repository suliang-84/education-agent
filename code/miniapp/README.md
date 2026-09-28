# MESH AI助教微信小程序

MESH 数理化认知训练平台 · 微信小程序客户端

> 面向初中至高中生的 AI 认知训练工具，以「五力认知测试」为核心，通过个性化选题与 AI 全程陪伴，培养学生底层认知能力。

---

## 目录

- [技术架构](#技术架构)
- [目录结构](#目录结构)
- [功能模块](#功能模块)
- [页面清单](#页面清单)
- [数据流与状态管理](#数据流与状态管理)
- [API 层设计](#api-层设计)
- [样式规范](#样式规范)
- [快速启动](#快速启动)
- [环境变量](#环境变量)
- [代码规范](#代码规范)
- [对接后端](#对接后端)

---

## 技术架构

```
微信小程序运行时
        ↑
  uni-app 编译层（Vite + @dcloudio/vite-plugin-uni）
        ↑
  Vue 3 Composition API（<script setup>）
        ↑
  Pinia 状态管理  ←→  SCSS 设计系统
        ↑
  API 层（utils/request.ts 封装，自动注入 Token + 401 刷新）
        ↑
  后端服务（FastAPI，Base URL: /api/v1）
```

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 跨端框架 | uni-app | 3.x alpha | 编译目标：微信小程序（`mp-weixin`）|
| UI 框架 | Vue 3 | ^3.4.0 | Composition API，`<script setup>` 语法 |
| UI 组件库 | TDesign Miniprogram | ^1.7.0 | 腾讯出品，符合微信设计规范 |
| 状态管理 | Pinia | ^2.1.7 | Vue 3 官方推荐，支持持久化 |
| 样式 | SCSS | sass ^1.75.0 | 变量全局注入，`rpx` 单位 |
| 构建工具 | Vite | 5.x | uni-app 官方集成 |
| 类型系统 | TypeScript | ^5.4.0 | 全量类型覆盖 |
| 代码规范 | ESLint + Prettier | 8.x / 3.x | Vue3 + TS 规则集 |

---

## 目录结构

```
miniapp/
├── .env                        # 开发环境变量（API地址、AppID）
├── .env.production             # 生产环境变量
├── .eslintrc.cjs               # ESLint 规则配置
├── .prettierrc                 # Prettier 格式化规则
├── package.json                # 依赖声明与 npm scripts
├── tsconfig.json               # TypeScript 配置（alias @/* → src/*）
├── vite.config.ts              # Vite 配置（SCSS 全局变量注入）
│
└── src/
    ├── main.ts                 # 应用入口，创建 Vue + Pinia 实例
    ├── App.vue                 # 根组件，onShow 检查登录态，引入全局样式
    ├── manifest.json           # 小程序基本配置（AppID、权限声明）
    ├── pages.json              # 页面路由配置 + TabBar 定义
    │
    ├── pages/                  # ── 页面层 ─────────────────────────────────
    │   ├── auth/
    │   │   ├── login.vue           # 登录引导页（微信一键登录）
    │   │   └── bind-phone.vue      # 新用户手机号绑定页
    │   ├── training/
    │   │   ├── index.vue           # Tab1：训练首页（科目选择 + 五维度入口）
    │   │   └── session/
    │   │       └── index.vue       # 训练答题页（进度条 + RAG引导 + AI浮层）
    │   ├── test/
    │   │   ├── index.vue           # 五力测试引导页（含中断恢复）
    │   │   ├── questions.vue       # 测试答题页（20题 + 进度点 + 计时器）
    │   │   └── result.vue          # 测试结果页（雷达图 + AI分析轮询）
    │   ├── assistant/
    │   │   ├── index.vue           # Tab2：AI助教首页（会话列表 + 快捷入口）
    │   │   └── chat.vue            # 对话页（消息列表 + 评分 + 突破反馈）
    │   ├── profile/
    │   │   └── index.vue           # Tab3：我的五力（SVG雷达图 + 维度详情）
    │   └── wrong-answers/
    │       └── index.vue           # 错题集（科目概览 + 分状态列表 + AI复盘）
    │
    ├── api/                    # ── 接口层（按业务模块拆分）────────────────
    │   ├── auth.ts             # 认证：微信登录 / 短信 / 绑手机 / Token刷新 / 退出
    │   ├── test.ts             # 五力测试：题卷 / 提交 / 完成 / 结果轮询 / 历史
    │   ├── knowledge.ts        # 知识导航：学科 / 年级 / 知识点（自动学期过滤）
    │   ├── training.ts         # 训练：五维度会话 / 答题 / RAG状态 / 完成 / 错题统计
    │   ├── profile.ts          # 画像：个人信息 / 五力画像 / 错题集列表 / 发起复盘
    │   ├── assistant.ts        # AI助教：会话管理 / 发消息 / 历史 / 评分 / 结束
    │   └── index.ts            # 统一导出所有 API 模块
    │
    ├── store/                  # ── 状态管理（Pinia）────────────────────────
    │   ├── auth.ts             # 登录态：Token / 用户信息 / 登录状态（持久化到 Storage）
    │   ├── training.ts         # 训练会话：当前题目列表 / 答题进度 / 会话 ID / 答对数
    │   └── index.ts            # 统一导出
    │
    ├── utils/
    │   ├── request.ts          # 请求封装：Token注入 / 401自动刷新（并发队列） / 错误提示
    │   └── index.ts            # 工具函数：时间格式化 / 手机脱敏 / 防抖节流 / 五力等级
    │
    ├── constants/
    │   └── index.ts            # 全局常量：五力枚举/颜色/标签 / 训练维度 / 页面路径 / 科目
    │
    ├── hooks/
    │   └── useRagPoller.ts     # RAG轮询 Hook：3秒轮询 / 最多15次 / 超时自动降级
    │
    ├── styles/
    │   ├── variables.scss      # 设计变量（品牌色/五力色/间距/圆角/字号），全局自动注入
    │   └── global.scss         # 全局基础样式 + 工具类（.card / .btn-primary / flex等）
    │
    └── static/
        ├── images/             # 业务图片资源
        └── icons/              # TabBar 图标（训练/AI助教/我的五力 各两套）
```

---

## 功能模块

### 1. 账户认证（`pages/auth/`）

| 功能 | 说明 |
|------|------|
| 微信登录 | 调用 `wx.login()` 获取 code → 换取 openid → 判断新/老用户 |
| 手机绑定 | 新用户必须绑定手机号，同时选择年级、学期、科目偏好 |
| Token 管理 | access_token（7天）+ refresh_token（30天），401 时自动静默刷新 |
| 退出登录 | 清除本地 Token + Pinia Store + 跳转登录页 |

**登录流程：**
```
wx.login() → POST /auth/wx-login
  ├─ 新用户 → temp_token → 跳转绑手机 → POST /auth/bind-phone-with-token → 进入首页
  └─ 老用户 → access_token + refresh_token → 检查五力画像 → 进入首页
```

---

### 2. 五力认知测试（`pages/test/`）

| 功能 | 说明 |
|------|------|
| 测试引导 | 介绍测试规则，检测上次中断的会话（72小时内可恢复） |
| 20题答题 | 固定20道题打散展示，计时，支持修改答案，进度点可视化 |
| 中断恢复 | 答题进度存 Storage，重启后弹窗询问继续/重新开始 |
| 评分展示 | 同步评分（≤3秒）→ 显示五边形雷达图 + 分维度分数 |
| AI 分析 | 异步生成（5~30秒），前端每3秒轮询（最多10次），骨架屏占位 |

**五力维度：**

| 维度 | 标识 | 颜色 |
|------|------|------|
| 洞察力 | `INSIGHT` | `#0D9488` 青绿 |
| 建构力 | `CONSTRUCT` | `#E11D48` 热红 |
| 推演力 | `DEDUCE` | `#4F46E5` 靛蓝 |
| 调适力 | `ADAPT` | `#D97706` 琥珀 |
| 迁移力 | `MIGRATE` | `#7C3AED` 紫罗兰 |

---

### 3. 个性化训练（`pages/training/`）

**训练入口四步流程：**

```
选科目（数学/物理/化学）
    → 选维度（5种）
        → 选内容（按维度差异化）
            → 训练说明页 → 开始答题
```

**五种训练维度：**

| 维度 | 选题范围 | 特殊逻辑 |
|------|---------|---------|
| `KNOWLEDGE_POINT` 按知识点 | 指定知识点题目 | 显示错误率（≥5题才统计）|
| `UNIT` 按单元 | 指定单元下所有知识点 | 显示单元题目数 |
| `SEMESTER` 按学期 | 当前年级+学期+科目 | 自动匹配，可手动切换 |
| `ERROR_QUESTIONS` 错题集 | 该科目待攻克错题 | 调 `wrong-summary` 展示各科目数量 |
| `RANDOM` 随机练习 | 科目所有已发布题目 | 跨知识点随机 |

**答题页核心状态机：**

```
答题 → 提交 → is_correct?
  ├─ 正确 → 下一题 / 完成
  └─ 错误 → RAG 轮询（3s轮询，最多15次）
               ├─ completed → 展示 AI 解题引导
               └─ degraded → 展示静态解析（可重试，最多3次）
                 连续2+次答错 → 显示 AI 介入浮层
```

---

### 4. AI 智能助教（`pages/assistant/`）

| 功能 | 说明 |
|------|------|
| 会话管理 | 创建/恢复/结束对话，同时只有一个 active 会话 |
| 苏格拉底对话 | AI 用引导式提问帮助学生自主突破，不直接给答案 |
| 消息评分 | 👍👎 对 AI 回复评分，反馈到策略有效性档案 |
| 理解突破检测 | 双重机制（关键词 + 语义），检测到突破显示 ✨ 成就感反馈 |
| 沉默模式 | 学生拒绝介入后 AI 停止主动发言，10分钟超时解除 |
| 对话上限 | 30轮/会话，达上限提示结束或新建 |
| 训练介入 | 训练中连续2+次答错 → 右下角浮层 → 底部50% mini对话 |

**消息气泡样式：**
- AI 消息：左对齐，浅色背景，含策略标签
- 学生消息：右对齐，品牌色背景
- 突破消息：✨ 特殊样式，高亮容器

---

### 5. 我的五力（`pages/profile/`）

- **五边形雷达图**：纯 SVG `<polygon>` 实现，5个顶点对应5个维度，分数驱动顶点位置
- **综合分**：`训练分 × 0.6 + 测试分 × 0.4`
- **维度详情**：可展开，含维度定义 + 个性化分析 + 专项训练 CTA
- **成长趋势**：历次测试折线图（最多5次历史）

---

### 6. 错题集（`pages/wrong-answers/`）

**状态流转：**

```
训练/测试答错 → unreview（未复盘）
    ↓ 点击「AI复盘」
  reviewing（复盘中）
    ├─ AI 检测到理解突破 → aha_achieved（已突破，终态）
    └─ 对话结束未突破 → pending_consolidation（待巩固）
                              ↓ 再次复盘
                          reviewing...
```

**科目-状态双维度过滤：**
- 入口：展示各科目待攻克总数（调 `wrong-summary` 接口）
- 列表：Tab 过滤（全部 / 未复盘 / 复盘中 / 已突破）

---

## 页面清单

| 页面路径 | 文件 | Tab | 自定义导航 | 核心接口 |
|---------|------|-----|----------|---------|
| `pages/auth/login` | `login.vue` | — | — | `authApi.wxLogin` |
| `pages/auth/bind-phone` | `bind-phone.vue` | — | — | `authApi.sendSms` / `bindPhone` |
| `pages/training/index` | `index.vue` | Tab1 | — | `profileApi.getFivePower` / `trainingApi.getWrongSummary` |
| `pages/training/session/index` | `session/index.vue` | — | ✅ | `trainingApi.submitAnswer` / `getRagStatus` / `completeSession` |
| `pages/test/index` | `index.vue` | — | — | `testApi.getQuestions` |
| `pages/test/questions` | `questions.vue` | — | ✅ | `testApi.submitAnswer` / `completeTest` |
| `pages/test/result` | `result.vue` | — | — | `testApi.getResult`（轮询）|
| `pages/assistant/index` | `index.vue` | Tab2 | — | `assistantApi.getSessions` / `createSession` |
| `pages/assistant/chat` | `chat.vue` | — | ✅ | `assistantApi.sendMessage` / `rateMessage` / `endSession` |
| `pages/profile/index` | `index.vue` | Tab3 | — | `profileApi.getFivePower` |
| `pages/wrong-answers/index` | `index.vue` | — | — | `wrongAnswerApi.getList` / `startReview` |

---

## 数据流与状态管理

### Pinia Store

**`useAuthStore`（持久化到 Storage）**

```typescript
// 读取
authStore.isLoggedIn          // boolean 是否已登录
authStore.hasFivePowerProfile // boolean 是否有五力画像
authStore.userInfo            // { student_id, nickname, grade, semester, ... }

// 写入
authStore.setAuth({ access_token, refresh_token, user_info })
authStore.updateUserInfo({ grade, semester })
authStore.setProfileFlag(true)
authStore.clearAuth()         // 退出登录
```

**`useTrainingStore`（内存状态，会话级）**

```typescript
// 读取
trainingStore.sessionId       // 当前训练会话 UUID
trainingStore.questions       // 题目列表
trainingStore.currentIndex    // 当前第几题（0-based）
trainingStore.correctCount    // 本次答对数
trainingStore.focusPower      // 本次重点练习的五力维度

// 写入
trainingStore.initSession(resp)  // 初始化新会话
trainingStore.nextQuestion()     // 推进到下一题
trainingStore.markCorrect()      // 记录答对
trainingStore.reset()            // 会话结束后清空
```

### 页面级本地状态

测试答题进度持久化到 Storage（中断恢复）：

```typescript
// 存储键：'mesh_test_session'
{ session_id, current_index, answers: Record<number, string> }
```

---

## API 层设计

### 请求封装（`utils/request.ts`）

所有请求通过 `http.get/post/patch/delete` 发起，自动处理：

1. **Token 注入**：`Authorization: Bearer {access_token}`
2. **401 自动刷新**：检测到 401 → 调 `/auth/token/refresh` → 重放原请求（并发队列防竞争）
3. **统一错误提示**：`uni.showToast` 展示后端 `msg` 字段
4. **响应解包**：直接返回 `body.data`，调用方无需处理响应包装层

```typescript
import { trainingApi } from '@/api'

// 示例：自动注入 Token，失败自动提示
const session = await trainingApi.createSession({
  training_dimension: 'KNOWLEDGE_POINT',
  knowledge_point_id: 1001,
})
```

### RAG 轮询 Hook（`hooks/useRagPoller.ts`）

```typescript
const { ragContent, staticSolution, status, canRetry, startPolling, retry, stop } = useRagPoller()

// 答错后启动轮询
startPolling(answerRecordId)
// status: 'pending' | 'completed' | 'degraded'
// 自动3秒轮询，最多15次，超时降级
```

---

## 样式规范

### 设计变量（`styles/variables.scss`，全局自动注入）

```scss
// 品牌色
$primary: #4F46E5;   // 靛蓝（导航/强调）
$pink: #F43F7E;      // 热粉（主CTA按钮）

// 五力专属色
$power-insight:   #0D9488;
$power-construct: #E11D48;
$power-deduce:    #4F46E5;
$power-adapt:     #D97706;
$power-migrate:   #7C3AED;

// 文字色
$text-1: #1E293B;  $text-2: #64748B;  $text-3: #94A3B8;

// 圆角
$r-xl: 36rpx;  $r-pill: 9999rpx;

// 间距
$space-2: 16rpx;  $space-3: 24rpx;  $space-4: 32rpx;
```

### 规范要点

- 单位：**全部使用 `rpx`**（750rpx = 屏幕宽度）
- 颜色：**必须引用变量**，不允许在组件中写 hex 值
- 主 CTA 按钮：热粉色 `$pink` + 胶囊圆角 `$r-pill`
- 卡片：白色背景 `$bg-surface` + `$r-xl` + `$shadow-sm`
- 全局工具类：`.flex-center` / `.flex-between` / `.card` / `.btn-primary`（见 `global.scss`）

---

## 快速启动

### 前置要求

- Node.js 18+
- 微信开发者工具（最新版）
- HBuilderX（可选，推荐用 VS Code）

### 1. 安装依赖

```bash
cd code/miniapp
npm install
```

### 2. 配置环境变量

```bash
cp .env .env.local
# 编辑 .env.local，填入后端地址和小程序 AppID
```

### 3. 开发编译

```bash
# 编译并监听变更（输出到 dist/dev/mp-weixin）
npm run dev:mp-weixin
```

### 4. 微信开发者工具预览

1. 打开微信开发者工具
2. 导入项目，选择 `dist/dev/mp-weixin` 目录
3. 填入小程序 AppID（与 `.env` 中 `VITE_WX_APPID` 一致）
4. 点击「编译」即可预览

### 5. 生产构建

```bash
npm run build:mp-weixin
# 产物位于 dist/build/mp-weixin，上传至微信开发者工具发布
```

---

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `VITE_APP_ENV` | 运行环境 | `development` / `production` |
| `VITE_API_BASE_URL` | 后端 API 根地址 | `http://localhost:8000/api/v1` |
| `VITE_WX_APPID` | 微信小程序 AppID | `wx1234567890abcdef` |

---

## 代码规范

```bash
# ESLint 检查 + 自动修复
npm run lint

# Prettier 格式化
npm run format

# TypeScript 类型检查
npm run type-check
```

**约定：**
- 组件使用 `<script setup lang="ts">`，不使用 Options API
- `import` 按 vue → pinia → @/api → @/store → @/utils → @/constants 分组
- 页面组件名与路径一致，不需要 multi-word 限制（ESLint 规则已关闭）
- 所有异步请求统一用 `try/catch` 包裹，loading 状态用 `ref<boolean>` 管理

---

## 对接后端

后端服务（`code/manage-backend`）同时服务后台管理系统和小程序：

| 端 | Base URL | 认证方式 |
|----|---------|---------|
| 小程序 | `/api/v1/` | JWT Bearer（学生，7天 Access + 30天 Refresh）|
| 后台管理 | `/api/v1/admin/` | JWT Bearer（管理员，8小时）|

**本地联调：**

```bash
# 启动后端（另开终端）
cd code/manage-backend
uv run uvicorn app.main:app --reload --port 8000

# .env 中 VITE_API_BASE_URL 保持 http://localhost:8000/api/v1
```

**微信登录本地调试：**

由于本地环境无法直接调用微信 `jscode2session`，调试时可在后端 `.env` 中配置 `WX_APPID` 和 `WX_SECRET`，或临时修改后端登录接口为 mock 模式。

**接口文档：**
- Swagger UI：`http://localhost:8000/api/docs`
- 完整接口设计：`docs/4.架构设计/06_接口设计说明书.md`
- 产品设计说明书：`docs/4.架构设计/07_产品设计说明书.md`

---

## 关联项目

```
education-agent/
├── code/
│   ├── miniapp/          # 本项目：微信小程序前端
│   ├── manage-frontend/  # 后台管理系统前端（Vue3 + Vite）
│   └── manage-backend/   # 统一后端服务（FastAPI + PostgreSQL）
└── docs/                 # 产品/接口/数据库设计文档
```

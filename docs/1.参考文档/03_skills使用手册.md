# Claude Code Skills 使用手册

> 本文档整理了 `~/.claude/skills/` 目录下所有已安装的 Skills，按功能分类说明其作用与触发关键词。

---

## 目录

- [开发流程类](#开发流程类)
- [代码质量类](#代码质量类)
- [规划与需求类](#规划与需求类)
- [UI/UX 设计类](#uiux-设计类)
- [Agent 协作类](#agent-协作类)
- [Skill 管理类](#skill-管理类)

---

## 开发流程类

### `brainstorming`
**作用**：在任何创意工作开始前进行头脑风暴，探索用户意图、需求和设计方案，防止过早进入实现阶段。

**触发关键词**：创建功能、构建组件、添加功能、修改行为、做一个…、实现…、我想要…

---

### `test-driven-development`
**作用**：实现任何功能或修复 Bug 前，先编写测试用例，遵循 TDD 红-绿-重构循环，确保代码有测试保障。

**触发关键词**：实现功能、修复 bug、开发新特性、写测试、TDD

---

### `executing-plans`
**作用**：在独立 session 中执行已写好的实现计划，每个阶段设有检查点，确保按计划推进。

**触发关键词**：执行计划、按计划实施、开始开发、implement this plan

---

### `finishing-a-development-branch`
**作用**：实现完成、测试通过后，决定如何整合工作（合并策略、PR 创建等）。

**触发关键词**：完成了、测试通过了、准备合并、提交 PR、结束这个分支

---

### `verification-before-completion`
**作用**：在声称工作完成、提交或创建 PR 之前，必须运行验证命令并确认输出，杜绝"应该可以"式的断言。

**触发关键词**：完成了、应该没问题、可以合并了、done、finished

---

### `using-git-worktrees`
**作用**：开始需要隔离的功能开发时，通过 git worktree 创建独立工作区，避免污染当前分支。

**触发关键词**：新功能开发、需要隔离、worktree、独立工作区、开始执行计划

---

## 代码质量类

### `systematic-debugging`
**作用**：遇到 bug、测试失败或意外行为时，系统化地定位根因，而非盲目猜测修复。

**触发关键词**：报错了、bug、测试失败、不工作、异常、unexpected behavior、debug

---

### `code-review-and-quality`
**作用**：从正确性、可读性、架构、安全、性能五个维度对代码进行全面审查，任何变更合并前使用。

**触发关键词**：review 代码、代码审查、合并前检查、看看这段代码、质量检查

---

### `code-simplification`
**作用**：在不改变行为的前提下，简化代码结构，降低复杂度，提升可读性和可维护性。

**触发关键词**：简化代码、重构、代码太复杂、难以阅读、refactor、simplify

---

### `requesting-code-review`
**作用**：完成任务或重要功能实现后，规范化地请求代码审查，验证工作是否符合要求。

**触发关键词**：请求 review、让别人看看、提交审查、request review

---

### `receiving-code-review`
**作用**：收到代码审查反馈后，在实施建议之前进行技术严谨性验证，避免盲目照做或表演性同意。

**触发关键词**：收到 review 意见、审查反馈、别人说要改、review comments

---

## 规划与需求类

### `writing-plans`
**作用**：拿到规格或需求后、动代码之前，先写出清晰的多步骤实现计划。

**触发关键词**：先规划一下、写个计划、怎么实现、制定方案、before coding

---

### `planning-with-files`
**作用**：Manus 风格的持久化文件计划系统，将 `task_plan.md`、`findings.md`、`progress.md` 保存到磁盘，在 context 丢失或 `/clear` 后自动恢复。适合 5+ 工具调用的长任务。

**触发关键词**：长任务、多步骤项目、帮我规划、整理任务、plan out、context 会丢失

---

### `grill-me`
**作用**：对计划或设计进行连环追问，逐一解决决策树的每个分支，在写代码前建立完整的共识。每次只问一个问题，并附带推荐答案。

**触发关键词**：grill me、帮我审设计、压力测试这个方案、质疑我的计划、拷问需求

---

### `requirement-writer`
**作用**：通过交互式对话引导用户进行结构化需求收集，生成问题框架（Problem Framing）、SRD 和 PRD 文档。

**触发关键词**：写需求文档、PRD、SRD、需求说明、产品规格、功能规格书

---

### `ai-prd`
**作用**：为软件系统和 AI 功能生成高质量的产品需求文档，包含执行摘要、用户故事、技术规格和风险分析。

**触发关键词**：生成 PRD、产品需求文档、AI 功能需求、写规格书

---

## UI/UX 设计类

### `ui-ux-pro-max`
**作用**：全平台 UI/UX 设计智能，包含 79 种 UI 风格、192 种配色方案、74 种字体搭配、119 条 UX 指南、25 种图表类型。适用于设计、构建、审查和修复界面。

**触发关键词**：设计界面、UI 设计、UX 优化、配色方案、字体搭配、响应式布局、无障碍设计

---

### `frontend-design`
**作用**：为新 UI 或改版提供有辨识度的视觉设计指导，在调色板、字体和布局上做出刻意的、有主见的选择，避免模板感。

**触发关键词**：视觉设计、界面风格、让界面有特色、不要模板感、审美方向、typography

---

### `frontend-ui-engineering`
**作用**：构建生产级、无障碍、响应式前端界面，满足 WCAG 要求，处理组件、布局、状态管理，让输出看起来是专业产品而非 AI 生成。

**触发关键词**：构建 UI、实现组件、响应式布局、WCAG、无障碍、React 组件、生产级界面

---

### `ui-styling`
**作用**：使用 shadcn/ui（Radix UI + Tailwind）构建美观、无障碍的用户界面，支持深色模式、主题定制和视觉设计。

**触发关键词**：shadcn、Tailwind、组件样式、深色模式、主题、UI 组件库

---

### `design`
**作用**：综合设计技能，覆盖品牌标识、设计 Token、Logo 生成（55 种风格）、企业视觉识别（CIP）、HTML 演示文稿、Banner 设计（22 种风格）、图标设计、社交媒体图片。

**触发关键词**：设计 Logo、品牌设计、CIP、设计系统、生成图标、社交媒体图片

---

### `design-system`
**作用**：三层 Token 架构（primitive→semantic→component）、CSS 变量、间距/字体规范、组件规格、策略性幻灯片创建。

**触发关键词**：设计系统、design token、组件规范、CSS 变量、字体规范、间距系统

---

### `banner-design`
**作用**：为社交媒体、广告、网站 Hero 区、印刷品设计 Banner，支持多种艺术风格和平台尺寸规格。

**触发关键词**：设计 banner、广告图、封面图、Facebook/Twitter/LinkedIn 广告、网站 hero

---

### `brand`
**作用**：品牌声音、视觉标识、信息框架、资产管理、品牌一致性。适用于品牌内容、语气风格、营销资产、风格指南。

**触发关键词**：品牌设计、品牌声音、营销物料、风格指南、品牌一致性、tone of voice

---

### `slides`
**作用**：使用 Chart.js 和设计 Token 创建策略性 HTML 演示文稿，包含响应式布局和文案公式。

**触发关键词**：做 PPT、创建演示文稿、幻灯片、presentation、slides、Chart.js

---

### `taste-skill`
**作用**：反模板化前端设计 Skill，专注于落地页、作品集和改版场景。先读懂设计简报，推断正确的设计方向（风格、调性、受众），再输出不像 AI 默认风格的界面——主动避开 AI 紫渐变、暗色网格背景、三等分卡片等 LLM 默认模式。

**触发关键词**：落地页设计、Landing Page、作品集、portfolio、页面改版、不要模板感、设计有品位的界面、anti-slop、炫酷风格

---

## Agent 协作类

### `dispatching-parallel-agents`
**作用**：面对 2 个或更多相互独立、无共享状态依赖的任务时，并行分派多个 Agent 同时处理，提升效率。

**触发关键词**：并行处理、同时做几件事、独立任务、多个任务、并发执行

---

### `subagent-driven-development`
**作用**：在当前 session 中用子 Agent 驱动执行实现计划中的独立任务。

**触发关键词**：子 Agent、分派任务、当前 session 执行、subagent

---

### `using-superpowers`
**作用**：对话开始时建立 Skills 框架，规定在任何响应（包括澄清性问题）之前必须先检查并调用相关 Skill。

**触发关键词**：（每次对话开始时自动触发）

---

## Skill 管理类

### `skill-creator`
**作用**：从零创建新 Skill、修改优化现有 Skill、运行评测和性能基准测试，优化 Skill 的 description 以提升触发准确率。

**触发关键词**：创建 skill、写一个 skill、优化 skill、测试 skill 效果、skill 评测

---

### `skill-finder`
**作用**：当遇到小众领域、陌生 API 或专业知识需求时，自动搜索社区 registry 并安装匹配的 Skill；找不到时帮你创建新 Skill。

**触发关键词**：我想要能做 X 的能力、帮我找一个 skill、安装某个能力、I want to know…

---

### `update-skills-handbook`
**作用**：安装新 Skill 后，自动扫描 `~/.claude/skills/` 与手册的差异，将缺失的 Skill 条目（作用、触发关键词、分类）同步写入本手册，并更新 Skills 总数。

**触发关键词**：更新手册、同步 skill 文档、安装了新 skill、handbook 过期了、skill 没有记录

---

### `writing-skills`
**作用**：创建新 Skill、编辑现有 Skill、在部署前验证 Skill 是否正常工作。

**触发关键词**：写 skill、编辑 skill、验证 skill、部署前检查

---

## 快速参考

| 场景 | 推荐 Skill |
|------|-----------|
| 开始实现新功能前 | `brainstorming` → `writing-plans` → `test-driven-development` |
| 遇到 bug | `systematic-debugging` |
| 代码写完准备提交 | `code-review-and-quality` → `verification-before-completion` |
| 代码太复杂难维护 | `code-simplification` |
| 需要设计 UI 界面 | `ui-ux-pro-max` + `frontend-design` + `frontend-ui-engineering` |
| 多个独立任务并行 | `dispatching-parallel-agents` |
| 长任务防 context 丢失 | `planning-with-files` |
| 需求不清晰时 | `grill-me` → `requirement-writer` |
| 收到 review 反馈 | `receiving-code-review` |
| 准备合并分支 | `finishing-a-development-branch` |

---

| 安装新 skill 后更新手册 | `update-skills-handbook` |

---

*最后更新：2026-09-02 | Skills 总数：33*

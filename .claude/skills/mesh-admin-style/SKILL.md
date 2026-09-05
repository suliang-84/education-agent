---
name: mesh-admin-style
description: >
  Personal design style tracker and propagator for the MESH Admin frontend.
  Use when the user requests a style change, asks to refine a UI component,
  or wants to propagate a confirmed style decision across the entire system.
  Also use proactively when adding new pages or components to ensure visual
  consistency with the established personal design language.
---

# MESH Admin · Personal Design Style Skill

> 记录用户每次提出的样式修改意见，确认后分析系统中所有可能需要同步的位置，统一更新，并持续蒸馏出个人专属的设计风格体系。

---

## 0. 工作流程

```
用户提出样式修改 → 你理解并复述修改意图
  → 确认：「这个样式是否要作为全局规范？」
  → 是 → 更新 DESIGN_LOG（本文件末尾）
       → 分析系统受影响位置 → 批量传播修改
  → 否 → 仅修改指定位置，不写入规范
```

---

## 1. 技术栈与文件约定

| 文件 | 职责 |
|------|------|
| `src/style.css` | 全局 CSS 变量 + Element Plus 覆盖 + 全局工具类 |
| `src/layouts/AdminLayout.vue` | 侧边栏 / Topbar 布局框架 |
| `src/views/login/LoginView.vue` | 登录页（独立设计语言） |
| `src/views/*/` | 各业务模块视图 |

样式令牌全部定义在 `src/style.css` 的 `:root {}` 中。修改任何视觉参数，**优先改令牌，而不是硬编码值**。

---

## 2. 当前确认的设计规范

### 2.1 色彩

```
页面底色:   --bg-page    = #E8ECF8  （薰衣草紫，全站底色）
卡片背景:   --bg-surface = #FFFFFF
悬停/嵌套: --bg-muted   = #F0F2FA

品牌靛蓝:  --indigo        = #4F46E5  （导航激活/图标/次要按钮）
靛蓝淡背:  --indigo-light  = #EEF2FF
主CTA粉:   --pink          = #F43F7E  （唯一主行动色，胶囊形按钮）
CTA渐变:   linear-gradient(135deg, #F43F7E, #E11D63)

成功绿:    --green   = #10B981
警告琥珀:  --amber   = #D97706
错误红:    --red     = #EF4444
迁移紫:    --purple  = #7C3AED
青绿洞察:  --teal    = #0D9488
```

### 2.2 阴影（靛蓝色调，非灰色）

```css
--shadow-sm: 0 2px 8px rgba(79,70,229,0.06), 0 1px 3px rgba(0,0,0,0.04);
--shadow-md: 0 4px 20px rgba(79,70,229,0.10), 0 2px 8px rgba(0,0,0,0.05);
--shadow-lg: 0 12px 40px rgba(79,70,229,0.14), 0 4px 16px rgba(0,0,0,0.07);
--shadow-pink: 0 4px 14px rgba(244,63,126,0.35);
```

### 2.3 圆角

```
--r-xs:   4px   （最小，内嵌元素）
--r-sm:   8px   （小徽章/小标签）
--r-md:   10px  （输入框/小按钮）
--r-lg:   14px  （一般按钮）
--r-xl:   18px  （卡片/面板）
--r-2xl:  24px  （弹窗）
--r-pill: 9999px（主CTA/状态标签/胶囊）
```

### 2.4 字体

```css
--font-sans: 'Inter', 'PingFang SC', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
```

数字/ID/代码：必须使用 `--font-mono` + `font-variant-numeric: tabular-nums`

### 2.5 间距

```
主内容区 padding: 26px 28px
卡片内边距: 22px 24px
filter-bar padding: 14px 18px
行间距 gap: 12-16px
```

### 2.6 五力维度色

```
INSIGHT   洞察力 → --teal    #0D9488
CONSTRUCT 建构力 → --red     #E11D48（比 --red 略深）
DEDUCE    推演力 → --indigo  #4F46E5
ADAPT     调适力 → --amber   #D97706
MIGRATE   迁移力 → --purple  #7C3AED
```

---

## 3. 组件规范

### 3.1 主 CTA 按钮（`.btn-pink`）

```css
background: linear-gradient(135deg, #F43F7E, #E11D63);
border-radius: 9999px;
height: 46px;        /* 登录页 */
height: auto;        /* 管理页用 padding */
padding: 9px 22px;
font-weight: 700;
box-shadow: 0 4px 16px rgba(244,63,126,0.38);
```

使用场景：
- 新增题目、提交标注审核、创建训练版本、批量确认

**禁止**将靛蓝色按钮用于以上场景。

### 3.2 次要/默认按钮（`el-button--default`）

```css
background: #FFFFFF;
border: 1.5px solid rgba(79,70,229,0.15);
border-radius: --r-lg (14px);
color: --text-2;
```

### 3.3 卡片（`.surface`）

```css
background: var(--bg-surface);   /* #FFFFFF */
border-radius: var(--r-xl);      /* 18px */
box-shadow: var(--shadow-sm);
/* 无 border */
```

hover 时：`box-shadow: var(--shadow-md)` + `transform: translateY(-2px)`（仅数据卡片）

### 3.4 表格

```
表头 th: background #F8F9FD, uppercase, letter-spacing: 0.06em, color --text-3
行 hover: background #F5F7FF （淡薰衣草，带品牌感）
分隔线: rgba(79,70,229,0.05)
```

### 3.5 导航激活态（侧边栏）

```css
background: var(--indigo-light);   /* #EEF2FF */
color: var(--indigo);              /* #4F46E5 */
font-weight: 600;
border-radius: 12px;               /* 整块背景，无左侧色条 */
```

### 3.6 标签/徽章

所有状态标签使用 `border-radius: 9999px`（胶囊形），带 `1.5px solid` 边框。

五力标签 `.power-badge--{POWER}` 使用维度色（2.6）。

置信度标签 `.conf-badge--high/mid/low`：绿/琥珀/红。

### 3.7 毛玻璃（Glassmorphism）— 登录页独占

**核心原则：卡片背景完全透明，`backdrop-filter` 独立承担磨砂玻璃效果。**

```css
/* 卡片主体：完全透明，背景色彩穿透显现 */
background: transparent;
backdrop-filter: blur(28px) saturate(160%);
-webkit-backdrop-filter: blur(28px) saturate(160%);
/* 细白边定义玻璃轮廓 */
border: 1px solid rgba(255, 255, 255, 0.40);
box-shadow:
  /* 顶部折射高光——玻璃质感的关键 */
  inset 0 1.5px 0 rgba(255,255,255,0.75),
  inset 1px 0 0 rgba(255,255,255,0.18),
  /* 外层靛蓝阴影 */
  0 24px 64px rgba(79,70,229,0.18),
  0 8px 24px rgba(79,70,229,0.10);
```

卡片内输入框：保留白色背景确保可读性：
```css
background: rgba(255, 255, 255, 0.72);
border: 1.5px solid rgba(255, 255, 255, 0.65);
```

背景浮动装饰卡片使用轻版毛玻璃：
```css
background: rgba(255,255,255,0.55);
backdrop-filter: blur(12px);
border: 1px solid rgba(255,255,255,0.75);
```

### 3.8 3D 鼠标倾斜效果（登录卡片独占）

```javascript
// 计算卡片相对鼠标位置
const nx = (e.clientX - cx) / (rect.width / 2)   // -1 ~ 1
const ny = (e.clientY - cy) / (rect.height / 2)  // -1 ~ 1
const maxDeg = 10
tiltY = nx * maxDeg
tiltX = -ny * maxDeg

// 应用
transform: perspective(900px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale3d(1.015, 1.015, 1)

// 悬浮时 fast，离开时 slow spring
isHovering ? 'transition: transform 0.12s cubic-bezier(0.16,1,0.3,1)'
           : 'transition: transform 0.65s cubic-bezier(0.16,1,0.3,1)'
```

---

## 4. 传播影响矩阵

当某个样式决策确认后，用此矩阵确定需要同步的位置：

| 样式决策类型 | 需检查的文件 |
|-------------|-------------|
| 颜色令牌变更 | `src/style.css` → 所有 `.vue` 文件的 scoped 样式 |
| 卡片圆角/阴影 | `src/style.css (.surface)` → 各视图 surface 元素 |
| 按钮样式 | `src/style.css (.btn-pink, el-button overrides)` → 各视图 |
| 表格样式 | `src/style.css (el-table overrides)` → QuestionList / StudentList / AuditLog |
| 导航激活态 | `src/layouts/AdminLayout.vue (.nav-item.active)` |
| 标签/徽章圆角 | `src/style.css (.power-badge, .conf-badge, .status-pill)` → 各视图 |
| 毛玻璃样式 | 仅 `LoginView.vue`（其他页面不使用） |
| 弹窗样式 | `src/style.css (el-dialog overrides)` → 所有含 el-dialog 的视图 |
| 输入框样式 | `src/style.css (el-input overrides)` → 全局生效 |

---

## 5. 执行步骤（每次样式修改）

1. **理解意图** - 用一句话复述用户想要修改的样式效果
2. **确认范围** - 询问「这个改动是否要作为全局规范统一应用？」
3. **写入 DESIGN_LOG** - 在第 6 节记录（日期 + 修改内容 + 影响范围）
4. **更新令牌** - 先修改 `src/style.css` 中的令牌或全局样式
5. **传播修改** - 按传播矩阵找到受影响位置并更新
6. **验证** - 运行 `npx vue-tsc --noEmit` 确保类型正确

---

## 6. DESIGN_LOG（样式变更历史）

> 每次确认的设计决策记录在此，按时间倒序。

---

### 2026-09-05 · 初始规范建立

**来源：** 参考 `/iamge/UI风格参考图1.webp` + `/iamge/UI风格参考图2.webp` 分析

**核心决策：**
- 页面底色从灰白改为薰衣草紫 `#E8ECF8`，建立品牌辨识度
- 主 CTA 颜色从靛蓝改为热粉 `#F43F7E`（胶囊形），靛蓝降为品牌色/辅助按钮
- 所有阴影从纯灰改为靛蓝色调 `rgba(79,70,229, x)`
- 圆角系统全面提升（卡片 18px，主按钮 9999px 胶囊）

**影响范围：** 全系统

---

### 2026-09-05 · 登录卡片真正透明底（毛玻璃拟态定型）

**来源：** 用户要求「类似毛玻璃拟态，底部是透明的」

**核心决策：**
- `.glass-card` background 改为 `transparent`（完全透明）
- `backdrop-filter: blur(28px) saturate(160%)` 独立承担磨砂效果
- 玻璃边界由 `border: 1px solid rgba(255,255,255,0.40)` + 顶部 `inset` 高光定义
- 输入框保留 `rgba(255,255,255,0.72)` 白底确保可读性
- 光斑 opacity 从 0.35 提升至 0.38-0.45，让透明玻璃后有更丰富色彩可透视
- 移除文字 `text-shadow`，深色文字在浅薰衣草背景上对比已足够

**设计原则（新增到 DNA）：** 真正的毛玻璃 = 透明背景 + `backdrop-filter` 磨砂 + 细白边 + 顶部折射高光。白色填充破坏透视感，应只出现在交互元素（输入框）而非卡片主体。

**影响范围：** 仅 `LoginView.vue`

---

### 2026-09-05 · 登录页毛玻璃 + 鼠标倾斜

**来源：** 用户明确要求「毛玻璃拟态风格 + 鼠标跟随倾斜感」

**核心决策：**
- 登录页从左右分屏改为全屏背景 + 居中悬浮毛玻璃卡片
- 毛玻璃参数：`blur(32px) saturate(200%)` + 顶部高光折射边缘
- 鼠标倾斜：`perspective(900px) rotateX/Y` 最大 ±10°，离开时 Spring 回弹
- 背景光晕：三个漂浮渐变光斑（靛蓝/粉/青绿），drift 动画

**影响范围：** 仅 `LoginView.vue`（毛玻璃和 3D 倾斜不向管理面板传播）

---

## 7. 蒸馏后的个人设计 DNA

> 从所有修改决策中提炼出的、属于这个项目的核心审美原则。

**1. 薰衣草底色是品牌锚点**
`#E8ECF8` 不是中性背景，是这套系统的身份标志。它让白色卡片浮起来，让靛蓝阴影产生意义。

**2. 只有一个主行动色，且它是粉色**
热粉 `#F43F7E` 的胶囊按钮在薰衣草背景上产生强烈但不刺眼的对比。靛蓝做导航激活态，粉色做行动召唤，两者分工明确，永不混用。

**3. 阴影是品牌色的延伸**
所有阴影带有 `rgba(79,70,229, x)` 的靛蓝色调——这个细节把孤立的卡片连接成有统一温度的系统。

**4. 圆角传递亲切感**
教育产品后台不是银行，主按钮是胶囊，卡片圆角 18px，标签圆角更是直接 `pill`。这种圆润让管理员觉得系统是为人设计的。

**5. 登录页是特殊区域，毛玻璃要彻底**
管理面板用白底卡片，登录页用真正的毛玻璃：`background: transparent` + `backdrop-filter` 磨砂 + 细白边 + 顶部折射高光。白色填充破坏透视感，只允许出现在输入框等交互元素上。交互元素内的文字靠自身背景白度保持可读，卡片整体要让背景的光斑色彩穿透进来。

**6. 数字永远等宽**
无论是统计卡片里的学生数，还是表格里的 ID，`JetBrains Mono` + `tabular-nums` 让数字精准、对齐、有工程感。

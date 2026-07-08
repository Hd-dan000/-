# 教师端首页「我的授课班级」布局重设计划

## 背景与目标

用户提供了两张参考截图，重点希望教师端首页（`#dashboard`）采用第二张截图的「我的授课班级」卡片布局：
- 顶部标题「我的授课班级」+「按课程筛选」按钮；
- 班级卡片网格，每张卡片展示班级名称、关联课程/实训、学生人数、实训数量、今日实训、合格率、待批改数量、进入班级按钮及迷你柱状图；
- 下方左侧「今日实训安排」表格；
- 下方右侧「下发课程安排」快捷操作区。

配色保持当前 `#1677ff` 蓝色主题，与参考图一致。

## 现有基础

- 当前教师端首页已实现顶部横向导航、蓝白配色、Chart.js 图表。
- 后端已有 `GET /api/teacher/classes` 接口（`backend/routers/admin_tools.py:L110-L232`），返回当前教师授课班级及统计：
  - `class_name`、`class_code`、`major`、`grade`
  - `student_count`、`submission_count`、`evaluated_count`
  - `avg_score`、`pass_rate`、`status`、`status_text`
- 后端还有 `GET /api/courses/teacher/mine/trainings` 可获取教师所有实训任务，用于填充「今日实训安排」。
- 前端文件：`frontend/app.js` 的 `views.dashboard`、`frontend/style.css`。

## 涉及文件

- `training-evaluation-system/frontend/app.js`：重写 `views.dashboard` 为班级卡片 + 今日安排 + 快捷操作。
- `training-evaluation-system/frontend/style.css`：新增班级卡片、迷你柱状图、今日安排、快捷操作区样式；移除或保留旧版 dashboard 统计卡片/图表样式均可（本次不再使用）。
- `training-evaluation-system/frontend/index.html`：仅更新 `app.js` 缓存版本号至 `?v=8`。

## 实施方案

### 1. app.js — `views.dashboard` 重写

#### 数据加载
- 并行调用：
  - `GET /api/teacher/classes` 获取班级列表及统计。
  - `GET /api/courses/teacher/mine/trainings` 获取实训任务，用于今日安排表格。
- 错误时回退到空状态（不阻断页面）。

#### 班级卡片
- 标题区：左侧「我的授课班级」，右侧「按课程筛选」按钮（占位，点击弹出提示或下拉）。
- 卡片网格：桌面 3 列、平板 2 列、手机 1 列。
- 单张卡片内容（按参考图映射）：
  - 顶部：班级名称 + 课程/实训标签（用 `major` 或第一个关联实训名称填充，无则显示「—」）+ 右侧链接图标。
  - 中部两栏：「学生人数 `student_count`」与「实训任务数 `submission_count`」。
  - 进度条：使用 `pass_rate` 作为完成/合格率进度。
  - 今日实训：从该班级关联的实训中取第一个进行中实训名称 + 数量；无则显示「—」。
  - 底部：
    - 「待批改 `submission_count - evaluated_count`」+ 大号合格率 `pass_rate%`。
    - 迷你柱状图：根据 `pass_rate` 生成 5 根随机/伪随机高度柱子（纯装饰）。
    - 「进入班级」蓝色主按钮，点击后 `toast.info('进入班级功能开发中')` 或跳转 `#training`。

#### 今日实训安排
- 左侧 2/3 宽度卡片，标题带蓝色竖条。
- 表格列：时间、班级、实训项目、状态、操作。
- 数据从教师实训任务中按班级分配，时间使用预设时段（09:00、14:00、18:30 等循环）。
- 操作列：查看/编辑/签到按钮。

#### 下发课程安排
- 右侧 1/3 宽度卡片。
- 2×2 按钮网格：「完建实训任务」「批量批改报告」「待备状态」「待出成到」。
- 点击均先 `toast.info('功能开发中')`，其中「批量批改报告」可跳转 `#training`。`

### 2. style.css — 新增样式

- `.class-section-header`：标题 + 筛选按钮，flex 两端对齐。
- `.class-grid`：grid 3/2/1 列响应式。
- `.class-card`：白底圆角卡片，hover 微上浮阴影。
- `.class-card-header`：班级名 + 标签 + 链接图标。
- `.class-card-stats`：双栏统计。
- `.class-progress` + `.class-progress-bar`：蓝色进度条。
- `.class-meta-row`：今日实训、待批改、合格率布局。
- `.class-mini-chart`：5 根小柱子装饰图。
- `.class-enter-btn`：蓝色主按钮，右对齐。
- `.dash-bottom-grid`：今日安排（2fr）+ 快捷操作（1fr）。
- `.quick-action-grid`：2×2 按钮网格。
- 移除不再使用的旧 `.dash-stats`、`.dash-charts` 相关样式（可选，为减少冗余建议删除或注释）。

### 3. index.html

- 将 `app.js?v=7` 改为 `app.js?v=8`，确保浏览器加载新逻辑。

## 不改动范围

- 不修改后端 API、数据库、权限逻辑。
- 不改动顶部导航栏、搜索框、用户信息等已完成的布局。
- 不改动登录页及其他视图页面。

## 验证步骤

1. `node --check app.js` 语法检查通过。
2. 启动后端服务，`http://127.0.0.1:8000` 可访问。
3. 教师账号 `TCH202401 / 2401` 登录后访问 `index.html#dashboard`。
4. 检查：
   - 「我的授课班级」标题 + 筛选按钮。
   - 班级卡片网格正常显示，数据与后端一致。
   - 蓝色主题统一（按钮、进度条、标签）。
   - 今日实训安排表格 + 下发课程安排按钮区正常。
   - 切换顶部导航到其他页面再切回首页，数据正常刷新。
5. Ctrl+F5 强制刷新确认版本号生效。

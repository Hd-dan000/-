# 教师端界面布局与配色重设计划

## 背景与目标

用户提供了参考设计 `演示的文件.htmll`，希望将当前教师端界面从「左侧深色侧边栏 + 顶部浅灰栏」改为「顶部横向导航栏 + 内容区卡片/图表/表格」的样式，并将主色调改为参考设计中的 `#1677ff`（Ant Design 蓝）。核心功能保持不变，仅做界面与配色调整。

当前教师端入口为 `training-evaluation-system/frontend/index.html`，配合 `app.js`（原生 JS 路由与视图）和 `style.css`。后端由 `main.py` 直接服务该目录静态文件。

## 涉及文件

- `training-evaluation-system/frontend/index.html`：页面外壳，改为顶部导航布局。
- `training-evaluation-system/frontend/style.css`：配色变量与新增顶部导航、统计卡片、图表卡片、今日安排表格样式。
- `training-evaluation-system/frontend/app.js`：
  - 适配新的横向导航高亮与路由；
  - 重写 `views.dashboard`（系统概览）为参考设计样式；
  - 其他视图保持功能，仅页面标题与容器样式跟随新主题。

## 实施方案

### 1. 页面外壳（index.html）

- 移除 `<aside class="sidebar">` 左侧深色导航栏与 `header.topbar` 面包屑栏。
- 新增顶部全局导航栏（参考设计）：
  - 左侧：Logo 图标 + 「实训管理平台」标题 + 搜索框（占位，可搜索班级/实训/学生）。
  - 右侧：消息通知、评论/提醒图标（带红点）、用户头像 + 名称 + 退出按钮。
  - 下方：横向二级菜单（首页、实训管理、评价规则配置、AI评阅报告、学生成长分析、大模型配置、系统设置）。
- 保留 `<main>` 中的 `#page-content` 作为视图渲染容器。
- 引入 Chart.js CDN，用于概览页折线图与圆环图。
- 更新 `app.js` 引用版本号至 `?v=7`，避免浏览器缓存旧逻辑。

### 2. 样式（style.css）

- 修改 `:root` 配色变量：
  - `--primary` 从 `#0052D9` 改为 `#1677ff`。
  - `--primary-hover` 改为 `#4096ff`。
  - `--primary-light` 改为 `#e8f3ff`。
  - `--bg-body` 保持接近 `#f5f7fa`。
  - 所有渐变、按钮、标签、进度条等使用新主色重新计算。
- 新增/调整样式类：
  - `.top-header`：白色背景、阴影、固定顶部、Flex 布局。
  - `.top-nav`：横向菜单，激活项为蓝底白字圆角按钮。
  - `.global-search`：灰色背景搜索框。
  - `.notification-bell` / `.user-menu`：顶部右侧图标与头像。
  - `.dash-tabs`：内容区顶部 Tab（今日实训 / 完成率统计 / 设备状态 / 待办事项）。
  - `.dash-stats`：4 列统计卡片，左侧文字 + 右侧浅蓝图标。
  - `.dash-charts`：2/3 + 1/3 分栏，折线图 + 圆环图 + 快捷操作。
  - `.dash-schedule`：今日实训安排表格。
- 兼容响应式：小屏下横向导航可横向滚动，统计卡片变为 2 列/1 列。
- 保留现有 `.card`、`.btn`、`.modal`、`.form-control`、`.toast` 等结构，仅调整颜色。

### 3. 交互与视图（app.js）

#### 导航适配
- `router.navigate` 高亮逻辑从 `.nav-item`（侧边栏）改为 `.top-nav-item`（顶部横向菜单）。
- `syncNavActive` 同步更新。

#### 系统概览（views.dashboard）重写
参考 `演示的文件.htmll` 结构，同时复用后端真实数据：

- **顶部 Tab**：今日实训 / 完成率统计 / 设备状态 / 待办事项（默认「今日实训」）。
- **4 张统计卡片**：
  - 授课班级：来自 `GET /api/courses/teacher/mine` 的 `courses.length`。
  - 进行中实训任务：来自 `GET /api/courses/teacher/mine/trainings`，统计 `status === 'in_progress'` 数量。
  - 待批改实训报告：来自 `GET /api/report/stats`，计算 `total_submissions - evaluated_count`。
  - 设备报修提醒：当前无对应接口，展示为 `0` 或静态占位，保留 UI 位置。
- **图表区**：
  - 左侧「本月实训完成趋势」折线图：使用 Chart.js，横轴为日期，纵轴可复用 `report.stats.recent_submissions` 按日聚合数量；数据不足时使用平滑模拟趋势。
  - 右侧「本班实训合格率」圆环图：使用 `report.stats` 计算 `(evaluated_count / total_submissions)` 或基于分数分布统计及格率。
  - 快捷操作：新建实训任务、批量批改报告、提交设备报修（按钮占位，跳转或提示）。
- **今日实训安排表格**：
  - 从 `/api/courses/teacher/mine/trainings` 取进行中/未开始实训，展示班级、实训项目、实训机房（暂无字段则显示「—」）、时间段（暂无字段则按顺序生成模拟时段）、状态标签、操作按钮。
  - 若后端无 schedule/机房/时间字段，表格内容使用已有训练数据 + 占位文本，确保 UI 完整。

#### 其他视图
- `views.training`（实训管理）：保留现有卡片列表、筛选、新建/编辑弹窗等全部功能；页面标题区样式改用新主题，统计卡片颜色同步新主色。
- `views.evaluation / report / llm / system-config / ops-center`：保持现有占位内容，仅外层容器与按钮颜色跟随新 CSS。

### 4. 不改动范围

- 不修改后端 API、数据库、路由权限逻辑。
- 不改动登录页 `login.html`。
- 不改动 Vue 版本 `frontend/src/` 与 `frontend/dist/`（当前由 `main.py` 服务的是根目录原生 JS 版）。
- 不删除现有功能代码，仅做样式与布局迁移。

## 验证步骤

1. 使用 Node.js 对修改后的 `app.js` 做语法检查（`node --check app.js`）。
2. 启动后端服务（`python backend/main.py`），确认 8000 端口正常。
3. 教师账号登录后访问 `http://127.0.0.1:8000/index.html#dashboard`。
4. 检查：
   - 顶部横向导航栏、搜索框、通知图标、用户信息是否正确显示。
   - 系统概览页 Tab、统计卡片、折线图、圆环图、今日安排表格是否渲染正常。
   - 颜色是否统一为 `#1677ff` 主题。
   - 切换到「实训管理」等导航，确认功能与数据正常。
5. Ctrl+F5 强制刷新，确认版本号生效。

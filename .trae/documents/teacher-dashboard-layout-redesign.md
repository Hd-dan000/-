# 教师端首页布局重构计划

## 背景与目标
用户希望将教师端首页（`#dashboard`）按照提供的参考图重新布局。参考图中顶部有一个蓝紫渐变 Hero 横幅，使用图片 `frontend/src/background.JPG`；横幅下方为授课班级卡片；底部左侧为实训安排表格，右侧为快捷操作区。本次仅做样式和布局调整，不改动业务逻辑与后端接口。

## 关键现状
- 入口页面：`frontend/index.html`，顶部全局导航 + `#page-content` 主内容区。
- 前端逻辑：`frontend/app.js`，`views.dashboard.render` 负责渲染教师首页，当前已实现：
  - 调用 `/api/teacher/classes` 获取授课班级统计。
  - 调用 `/api/courses/teacher/mine/trainings` 获取实训任务。
  - 渲染班级卡片网格 + 今日实训安排表格 + 下发课程安排快捷操作。
- 样式：`frontend/style.css`，已有大量组件样式，但缺少 Hero 横幅和参考图中简洁的两列统计卡片样式。
- 背景图片已存在：`frontend/src/background.JPG`。

## 待修改文件
1. `frontend/app.js` — 重写 `views.dashboard.render` 内的 HTML 结构，加入 Hero 横幅、两个统计卡片、底部表格与快捷操作。
2. `frontend/style.css` — 新增 Hero 横幅、统计卡片、响应式适配样式。
3. `frontend/index.html` — 更新 `app.js` 引用版本号（如 `?v=9`），避免缓存。

## 实现方案

### 1. Hero 横幅
- 在 dashboard 内容顶部插入 `.dash-hero` 区域。
- 背景使用 `src/background.JPG`，覆盖整个横幅；左侧叠加蓝紫渐变（`linear-gradient(90deg, #1677ff 0%, rgba(64,150,255,0.85) 60%, transparent 100%)`），确保白色文字可读。
- 文字内容：主标题“实训管理平台”，副标题“探索学习资源，管理实训项目”。
- 高度约 220px，圆角 16px，与下方内容保持 24px 间距。

### 2. 两个统计卡片
- 使用 `.dash-summary-grid` 两列网格（`grid-template-columns: 1fr 1fr`，小屏 1fr）。
- 每张卡片 `.dash-summary-card`：
  - 白底圆角卡片，左侧文字区，右侧迷你柱状图装饰。
  - 标题“我的授课班级”/“今日实训安排”。
  - 指标行：待批改、合格率。
  - 右下角蓝色主按钮“进入班级”/“进入安排”。
- 数据来源：
  - 我的授课班级：汇总所有班级 `submission_count - evaluated_count` 为待批改，按学生提交/班级人数或已有 `pass_rate` 计算合格率。
  - 今日实训安排：统计今日进行中的实训数量，待批改为今日实训中未评价数，合格率取自相关提交。

### 3. 底部区域
- 使用 `.dash-bottom-grid`（已存在），左侧表格，右侧快捷操作。
- 左侧表格保持“今日实训安排”，右侧保持“下发课程安排”4 个按钮。
- 表格增加表头全选复选框交互（已有实现，保持不变）。

### 4. 响应式
- 小屏（< 768px）时统计卡片单列、Hero 高度自动、表格横向滚动。

## 数据接口复用
- `/api/teacher/classes`：返回 `classes`（含 `student_count`、`submission_count`、`evaluated_count`、`pass_rate` 等）。
- `/api/courses/teacher/mine/trainings`：返回 `trainings`（含 `title`、`assignedClasses`、`status`、`submissionCount`、`evaluatedCount` 等）。

## 验证步骤
1. 启动后端 Python 服务（`python backend/main.py`）。
2. 使用教师账号登录后访问 `http://127.0.0.1:8000/index.html#dashboard`。
3. 检查：
   - Hero 横幅正常显示背景图且文字清晰。
   - 两个统计卡片与参考图一致。
   - 表格和快捷操作正常展示。
   - 控制台无 JS 错误。
4. Ctrl+F5 强制刷新确认缓存生效。

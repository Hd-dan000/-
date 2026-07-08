# 教师端 AI 评阅报告模块收尾与验证计划

## 1. 概要

本计划用于完成教师端 **AI 评阅报告** 模块的剩余工作。前端筛选/班级联动/搜索、分类查看弹窗、报告详情页、分类评分与总体成绩计算、班级共性问题、异常学生清单、报告导出、人工复核等核心代码已实现。当前主要剩余任务为：

- 确认/重启后端服务，使最新代码与表结构生效；
- 运行历史数据迁移，回填 `class_id` / `class_name`；
- 准备可覆盖“文档 / UI 截图 / 源代码”三类文件的测试数据；
- 端到端验证页面交互与评分计算；
- 处理搜索框焦点丢失等细节问题（如复现）。

## 2. 当前状态分析

已确认以下关键文件已按需求实现：

- [database.py](file:///f:/xiangmu/training-evaluation-system/backend/database.py)：`submissions` 表已增加 `class_id`、`class_name`、`category_teacher_scores`、`category_teacher_comments`；`trainings` 表已增加 `category_weights`；并提供了 `ALTER TABLE` 兼容迁移。
- [report_service.py](file:///f:/xiangmu/training-evaluation-system/backend/services/report_service.py)：已实现 `get_training_classes`、`list_submissions`、`get_category_detail`、`save_category_review`、`calculate_final_score`（缺失类别自动归一化权重）等核心逻辑。
- [report.py](file:///f:/xiangmu/training-evaluation-system/backend/routers/report.py)：已增加 `/api/report/classes`、`/api/report/submissions`、`/api/report/submission/{id}/detail`、`/api/report/submission/{id}/category-review` 等接口。
- [main.py](file:///f:/xiangmu/training-evaluation-system/backend/main.py)：新接口已注册到路由表。
- [app.js](file:///f:/xiangmu/training-evaluation-system/frontend/app.js)：
  - `views.report` 已实现实训/班级选择、学生搜索（回车触发）、提交状态列、分类标签、分类选择弹窗；
  - 新增 `views['report-detail']` 视图，支持三类文件预览、分类评分输入、实时总体成绩计算、保存复核。
- [index.html](file:///f:/xiangmu/training-evaluation-system/frontend/index.html)：静态资源版本已升级到 `v=38`。
- [migrate_submission_classes.py](file:///f:/xiangmu/training-evaluation-system/backend/migrate_submission_classes.py)：用于为已有提交回填班级信息。
- [seed_test_submission.py](file:///f:/xiangmu/training-evaluation-system/backend/seed_test_submission.py)：现有脚本只能生成一条仅含文档的测试数据，需要扩展以覆盖三类文件。

当前环境还有若干后台任务在运行（`job-2dbc...` 等），需要先确认是否为旧版后端进程，避免端口或资源冲突。

## 3. 拟执行步骤

### 步骤 1：清理并重启后端服务

1. 检查当前后台任务/进程，识别是否为旧版 `python backend/main.py`；
2. 终止冲突/陈旧进程，避免端口占用；
3. 在 `f:\xiangmu\training-evaluation-system\backend` 下重新启动后端：
   ```bash
   python main.py
   ```
4. 访问 `/api/health` 确认服务正常。

### 步骤 2：运行数据迁移

1. 执行班级信息回填脚本：
   ```bash
   python migrate_submission_classes.py
   ```
2. 校验 SQLite 中 `submissions.class_id` / `class_name` 已被填充。

### 步骤 3：准备覆盖三类的测试数据

目标：让 AI 评阅报告页不再为空，且能验证“文档 / UI 设计截图 / 源代码”的查看与评分。

1. 在 `backend/seed_test_submission.py` 基础上扩展（或新建 `seed_test_categories.py`），要求：
   - 指定一条可用的 `training_id`，并确保该实训的 `category_weights` 存在（默认 `document/ui/code 各 1/3`）；
   - 在 `uploads/training_{id}/` 下生成：
     - 一个 `.txt` / `.md` 文档；
     - 一个 `.png` / `.jpg` 图片（可直接复制项目已有 logo 或生成小图）；
     - 一个 `.py` / `.html` 源代码文件；
   - 向 `submissions` 插入或更新记录，将上述文件写入 `files` JSON 字段；
   - 可选：直接写入 `evaluation_detail` 中 `category_evaluation` 的 AI 分数，使列表页能显示 AI 评分；
   - 插入多条记录，覆盖不同班级、不同评分状态。
2. 运行脚本后，通过 `/api/report/submissions?training_id=...` 确认返回数据非空且 `categories` 包含 `document/ui/code`。

### 步骤 4：前端端到端验证

使用浏览器访问前端页面，按以下清单验证：

1. 教师登录后进入“AI 评阅报告”页；
2. 实训项目下拉可选，选择后班级下拉自动加载对应班级；
3. 搜索框输入学生姓名/学号，按回车后列表刷新，不丢失焦点；
4. 列表展示：提交状态（未提交/已提交未评阅/已评阅）、总分、维度分、文件分类标签；
5. 点击“查看报告”弹出复选框，可勾选“文档 / UI 设计截图 / 源代码”中的多项，确认后在新页面打开；
6. 报告详情页：
   - 三类文件预览正常（文档可下载、图片可放大、代码可高亮/显示内容）；
   - 教师评分输入后，总体成绩按 `category_weights` 实时重新计算；
   - 保存复核后返回成功提示，列表页总分/status 更新为 `evaluated`；
7. 班级共性问题面板、异常学生清单、导出 PDF/Excel、人工复核入口可正常打开且无报错。

### 步骤 5：搜索框焦点问题兜底修复

如果在步骤 4 中复现“输入时焦点丢失”：

- 在 [app.js](file:///f:/xiangmu/training-evaluation-system/frontend/app.js) `views.report.render` 中，当前已使用 `document.activeElement` 与 `setSelectionRange` 恢复焦点；
- 若仍有问题，将恢复逻辑改为在 `requestAnimationFrame` 或短 `setTimeout` 中执行，并把 `selectionStart/selectionEnd` 存入 `this.data` 状态，避免 DOM 重建瞬间 `activeElement` 被清空。

### 步骤 6：回归检查

1. 检查浏览器控制台无 500/404/JS 报错；
2. 返回首页/实训管理/学生提交等其他模块，确认无回归；
3. 如项目存在测试脚本，运行一次 smoke test。

## 4. 假设与决策

- 不再新增数据库表结构，仅使用已完成的 `ALTER TABLE` 迁移；
- 测试数据为一次性合成数据，不会污染真实学生/班级信息；
- 总体成绩计算遵循“教师评分优先于 AI 评分、缺失类别自动归一化剩余权重”的现有逻辑；
- 若真实数据中已有学生提交，可直接使用真实数据验证，跳过或简化步骤 3。

## 5. 验证标准

完成后需满足：

- [ ] 后端服务启动无报错，`/api/health` 返回 `ok`；
- [ ] `migrate_submission_classes.py` 执行成功，且 `submissions` 中 `class_id` / `class_name` 非空率符合预期；
- [ ] `/api/report/classes?training_id=...` 返回班级列表；
- [ ] `/api/report/submissions?...` 返回包含 `submission_status_label`、`categories`、`category_scores` 的学生列表；
- [ ] `/api/report/submission/{id}/detail?categories=document,ui,code` 返回三类文件及评分数据；
- [ ] 在报告详情页输入教师分类评分后，总体成绩实时变化，保存后 `final_score` 更新；
- [ ] 浏览器中搜索、筛选、查看报告、导出等关键交互无焦点丢失或报错。

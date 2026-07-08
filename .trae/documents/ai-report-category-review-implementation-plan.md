# 教师端 AI 评阅报告分类查看与分类评分实现计划

## 1. 摘要

本计划针对教师端“AI 评阅报告”模块中“按实训项目/班级/学生姓名筛选 → 列表展示提交状态 → 查看报告（可复选文档/UI 截图/源代码）→ 分类评分 → 自动计算总成绩 → 补充评阅”的完整流程，完成剩余缺口开发、数据补齐和功能验证。

当前前后端主干逻辑（筛选、列表、分类详情、分类评分、总分计算、报告导出、异常清单等）已基本实现，但存在以下关键缺口：
- 新提交未写入 SQLite `submissions.class_id/class_name`，导致按班级筛选/展示班级信息失效；
- 历史提交缺少班级信息，需要一次性迁移；
- 报告详情页源代码/文档仅展示占位文案，未真正读取文件内容；
- 搜索回车后整页重绘导致搜索框焦点丢失；
- 静态资源缓存版本未更新。

## 2. 现状分析

| 文件 | 关键现状 |
|------|----------|
| [backend/main.py](file:///f:/xiangmu/training-evaluation-system/backend/main.py) | `/api/report/classes`、`/api/report/submissions`、`/api/report/submission/{id}/detail`、`/api/report/submission/{id}/category-review` 等路由已注册；`/uploads/` 静态文件服务已启用。 |
| [backend/routers/report.py](file:///f:/xiangmu/training-evaluation-system/backend/routers/report.py) | 新增筛选、分类详情、分类评分接口已完整；使用 `ReportService` 处理业务逻辑。 |
| [backend/services/report_service.py](file:///f:/xiangmu/training-evaluation-system/backend/services/report_service.py) | `list_submissions`、`get_category_detail`、`save_category_review`、`calculate_final_score` 已实现；最终分按权重自动归一化缺失类别。 |
| [backend/database.py](file:///f:/xiangmu/training-evaluation-system/backend/database.py) | `submissions` 表已存在 `class_id`、`class_name`、`category_teacher_scores`、`category_teacher_comments` 列，并包含 `ALTER TABLE` 兼容迁移。 |
| [backend/routers/training.py](file:///f:/xiangmu/training-evaluation-system/backend/routers/training.py) | `handle_create_training` 已绑定 `training_classes`；`handle_submit_work` **未** 在写入 SQLite `submissions` 时带上 `class_id/class_name`（仅在 `_sync_to_submit_work` 写入 MySQL）。 |
| [frontend/app.js](file:///f:/xiangmu/training-evaluation-system/frontend/app.js) | `views.report` 已完成筛选/列表/分类弹窗；`views['report-detail']` 已完成 Tab 切换、评分输入、自动计算、保存；但 `renderFilePreview` 中 `code`/`document` 为占位展示。 |
| [frontend/style.css](file:///f:/xiangmu/training-evaluation-system/frontend/style.css) | 分类选择弹窗、报告详情页样式已补充。 |
| [frontend/index.html](file:///f:/xiangmu/training-evaluation-system/frontend/index.html) | `style.css?v=37`、`app.js?v=37`，需要 bump 版本号。 |

## 3. 拟修改内容

### 3.1 新提交写入班级信息
**文件：** [backend/routers/training.py](file:///f:/xiangmu/training-evaluation-system/backend/routers/training.py) `handle_submit_work`

在保存文件后、插入 `submissions` 前，按现有 `_sync_to_submit_work` 同样方式从 MySQL `students` 表查 `class_id`/`class_name`（按 `student_no` 匹配），并把字段加入 `INSERT` 语句。保证后续班级筛选、班级名称展示不再为空。

### 3.2 历史提交班级信息迁移
**文件：** 新建 `backend/migrate_submission_classes.py`

编写一次性迁移脚本：
1. 连接 SQLite `submissions` 表，筛选 `class_id IS NULL OR class_name IS NULL` 的记录；
2. 用 `student_id`（即学号 `student_no`）去 MySQL `students` 表匹配 `class_id`/`class_name`；
3. 若 `student_id` 为空，则按 `student_name` 二次匹配（同名取第一个，兜底）；
4. 更新 SQLite 对应记录，并打印迁移条数。

完成后在本地运行一次：
```bash
python backend/migrate_submission_classes.py
```

### 3.3 报告详情页真正预览文件内容
**文件：** [frontend/app.js](file:///f:/xiangmu/training-evaluation-system/frontend/app.js) `views['report-detail'].renderFilePreview`

- **源代码（code）：** 渲染每个文件占位后，通过 `fetch(f.url).then(r => r.text())` 异步拉取内容，替换 `<pre><code>` 中的占位文案；对获取失败展示“无法读取文件内容”。
- **文档（document）：** PDF 文件使用 `<iframe src="..."/>` 内嵌预览，其他文档保留“下载/查看”链接；Word/PPT 等仍通过链接打开。
- **UI 截图（ui）：** 已使用 `<img>` 预览，保持不变。

### 3.4 修复搜索框焦点丢失
**文件：** [frontend/app.js](file:///f:/xiangmu/training-evaluation-system/frontend/app.js) `views.report.render` / `onSearchSubmit`

`render` 每次都会重绘整个页面，回车触发 `loadSubmissions().then(() => this.render())` 后输入框被重建导致焦点丢失。修复方式：在 `render` 的 `content.innerHTML = ...` 之后、事件绑定区增加一段逻辑：若渲染前 `document.activeElement` 是搜索框（`class="report-search"`），则渲染完成后重新 `focus()` 并将光标移到末尾。

### 3.5 静态资源缓存版本更新
**文件：** [frontend/index.html](file:///f:/xiangmu/training-evaluation-system/frontend/index.html)

将 `style.css?v=37` 与 `app.js?v=37` 同时改为 `?v=38`。

## 4. 假设与决策

1. **学号匹配优先：** SQLite `submissions.student_id` 存储的是 `student_no`；迁移脚本以 `student_no` 为主键匹配，仅当学号缺失时使用姓名兜底。
2. **班级来源：** 班级下拉框使用 `training_classes` 表；只要实训创建/编辑时正常保存 `class_ids` 即生效。本次不再改动 `report_service.get_training_classes`。
3. **代码文件直接读取：** 代码文件统一按文本 `fetch`，失败时降级为提示；不新增后端文本接口，以减少改动量。
4. **分类选择弹窗保持三选项：** 不根据该学生实际文件禁用选项；选择后若某分类无文件，详情页显示“该分类下暂无文件”。
5. **不改动评分权重编辑：** 继续使用 `trainings.category_weights` 默认值 `{"document":0.333,"ui":0.333,"code":0.333}`，如需调整权重在数据库/实训创建处扩展。

## 5. 验证步骤

1. 后端服务重启成功，无 schema 报错；运行 `python backend/migrate_submission_classes.py` 成功，打印迁移条数 ≥ 0。
2. 以教师身份进入“AI 评阅报告”页：
   - 切换实训项目 → 班级下拉自动出现对应班级；
   - 选择班级 / 输入学生姓名按回车 → 列表刷新，搜索框保持焦点；
   - 列表显示“提交状态”“文件分类”列；
3. 点击“查看报告” → 弹出复选框，勾选文档/UI/源代码 → 新标签页打开 `#report-detail`。
4. 报告详情页：
   - Tab 可切换分类；
   - UI 图片正常显示；源代码区异步加载文本内容；PDF 文档内嵌预览；
   - 输入教师评分 → 总体成绩卡片实时更新；
   - 填写分类/整体评语 → 点击“保存复核” → 提示成功，返回报告列表后总分/状态已更新。
5. 学生端重新提交一份作业 → 教师端按该学生班级可筛选到，且班级列正确显示。

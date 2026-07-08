# AI 评阅报告模块增强计划

## 背景与目标

当前教师端 AI 评阅报告页已实现：训练选择、学生列表、单学生 AI 报告面板、班级共性问题汇总、异常学生清单、人工复核入口。用户参考图片后，要求增加“按实训项目 + 班级 + 学生姓名”筛选的学生报告列表，并支持分内容类型（文档 / UI 设计截图 / 源代码）查看、分类评分、自动计算总分、教师补充评阅。

本次改造将沿用当前生效的 **vanilla JS 前端（frontend/app.js + style.css）**，新增一个 SPA 视图 `#report-detail/{submissionId}` 用于分类查看与评分。

## 关键假设

1. **总分计算**：采用训练级权重加权平均。默认三类权重均为 `1/3`；若某类无文件/无评分，则自动归一化剩余类别的权重。权重存储在 `trainings.category_weights`。
2. **文件分类**：按扩展名分类：
   - 文档：`.pdf .doc .docx .txt .xlsx .xls .ppt .pptx .csv .md`
   - UI 截图：`.png .jpg .jpeg .gif .bmp .svg .webp`
   - 源代码：`.py .js .java .cpp .c .h .html .css .vue .jsx .ts .tsx .json .xml .sql .php .go .rb .rs .cs .swift .kt .m .mm .sh .bat .ps1 .yaml .yml .toml .ini .properties`
3. **新页面**：在现有单页应用内新增 hash 路由 `#report-detail/{id}?categories=document,ui,code`，用新浏览器页签打开（`window.open`）。
4. **不保留旧面板**：

## 数据库 Schema 变更

### SQLite `submissions` 表新增列

| 字段 | 类型 | 说明 |
|---|---|---|
| `class_id` | INTEGER | 班级 ID，用于筛选 |
| `class_name` | TEXT | 班级名称展示 |
| `category_teacher_scores` | TEXT | JSON，教师分类评分，如 `{"document":85,"ui":90,"code":75}` |
| `category_teacher_comments` | TEXT | JSON，教师分类评语 |

### SQLite `trainings` 表新增列

| 字段 | 类型 | 说明 |
|---|---|---|
| `category_weights` | TEXT DEFAULT '{"document":0.333,"ui":0.333,"code":0.333}' | 各类别权重 |

### `evaluation_detail` JSON 扩展

AI 评价结果中增加分类维度（兼容旧数据）：

```json
{
  "indicator_summary": [...],
  "ai_scores": [...],
  "overall_comment": "...",
  "category_evaluation": {
    "document": {"score": 85, "max_score": 100, "reason": "..."},
    "ui": {"score": 90, "max_score": 100, "reason": "..."},
    "code": {"score": 75, "max_score": 100, "reason": "..."}
  }
}
```

### 兼容已有数据

在 `backend/database.py` 的 `init_db()` 中：
1. `CREATE TABLE IF NOT EXISTS submissions` 新增四列。
2. 通过 `PRAGMA table_info` + `ALTER TABLE ADD COLUMN` 兼容已存在的数据库。
3. `trainings` 表同样处理。
4. 新增迁移脚本 `backend/migrate_submission_classes.py`，遍历已有 `submissions`，按 `student_id` 到 MySQL `students` 表查询 `class_id/class_name` 并回填。

### 持续写入

修改 `backend/routers/training.py` 的 `handle_training_submit`：学生提交时即从 MySQL 查出 `class_id`、`class_name`，一并写入 SQLite `submissions`。

## 文件分类逻辑

在 `backend/services/file_parser.py` 新增：

```python
CATEGORY_EXTENSIONS = {
    'document': {...},
    'ui': {...},
    'code': {...},
}

def categorize_files(files):
    # files: [{filename, path, size}, ...]
    # return: {'document': [...], 'ui': [...], 'code': [...], 'unknown': [...]}
```

同步扩展 `backend/config.py` 的 `ALLOWED_EXTENSIONS`，加入源码扩展名。

## 总分计算逻辑

在 `backend/services/report_service.py` 新增 `calculate_final_score(category_scores, category_weights)`：

1. 每个类别的“可用分”优先级：教师分类评分 > AI 分类评分 > null。
2. 过滤掉 null 的类别，按训练权重加权平均；若总权重为 0 返回 null。
3. 保留一位小数。

触发时机：
- AI 自动评价后写入 `ai_total_score` 与 `final_score`。
- 教师提交分类评分后重新计算 `final_score` 并更新。

## 后端 API 变更

### 新增接口（统一放在 `backend/routers/report.py`）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/report/classes?training_id={id}` | 返回某实训已绑定的班级列表 |
| GET | `/api/report/submissions?training_id={id}&class_id={cid}&student_name={name}` | 筛选提交列表 |
| GET | `/api/report/submission/{id}/categories` | 返回提交文件按分类分组及现有分类评分 |
| GET | `/api/report/submission/{id}/detail?categories=document,ui,code` | 按选定分类返回报告详情 |
| POST | `/api/report/submission/{id}/category-review` | 提交教师分类评分/评语 |

### 修改接口

- `backend/routers/report.py`
  - `handle_training_report_data`：返回的 `submissions` 增加 `class_id`、`class_name`、`category_scores`、`submission_status_label`。
- `backend/routers/evaluation.py`
  - `handle_teacher_review`：兼容旧整体评分；若请求体含 `category_scores`/`category_comments`，走分类评分分支。
  - AI 评价流程：调用 LLM 时要求输出 `category_evaluation`，解析后写入 `evaluation_detail`。

## 前端变更（基于 frontend/app.js + style.css）

### 1. 改造 AI 评阅报告首页 `views.report`

顶部筛选栏改为三列布局：
- **实训项目下拉**：调用 `/api/courses/teacher/mine/trainings`，选中后自动加载班级列表。
- **班级下拉**：调用 `/api/report/classes?training_id={id}`；未选实训时禁用；选择“全部班级”时不传 `class_id`。
- **学生姓名搜索框**：placeholder “搜索学生姓名/学号”，按 `Enter` 触发搜索。
- **查询按钮**：蓝色主按钮，重新加载列表。

学生列表列调整为：
- 序号、学号、姓名、班级、提交状态、AI 评分、最终评分、文件分类、操作。
- “提交状态”显示：未提交 / 已提交未评阅 / 已评阅。
- “查看报告”按钮点击后弹出复选框弹窗，选项：文档 / UI 设计截图 / 源代码。

### 2. 新增内容类型选择弹窗

```html
<div class="report-modal">
  <h3>选择要查看的评价内容</h3>
  <label><input type="checkbox" value="document"> 文档</label>
  <label><input type="checkbox" value="ui"> UI 设计截图</label>
  <label><input type="checkbox" value="code"> 源代码</label>
  <button onclick="openReportDetail()">查看报告</button>
</div>
```

`openReportDetail(submissionId)`：
- 收集选中的分类。
- 至少选一项，否则提示。
- `window.open(`#report-detail/${submissionId}?categories=...`, '_blank')`。

### 3. 新增 `views.reportDetail`

路由：`#report-detail/{submissionId}?categories=document,ui,code`。

页面结构：
- **头部**：学生姓名 / 学号 / 班级 / 实训名称 / 返回按钮 / 保存复核按钮。
- **文件浏览区**：按分类 Tab 展示：
  - 文档：文件名 + 下载/预览链接。
  - UI 截图：`<img>` 直接预览。
  - 源代码：`<pre>` 展示文本内容。
- **分类评分区**：每个已选分类一个卡片：
  - AI 评分（只读）
  - 教师评分（输入框，0-100）
  - 教师评语（输入框）
  - AI 评语理由（只读）
- **底部**：实时显示“预计总分”，教师整体评语，保存按钮。

保存时调用 `POST /api/report/submission/{id}/category-review`，成功后提示并刷新页面数据。

### 4. 路由注册

在 `frontend/app.js` 路由初始化处增加：

```javascript
'report-detail': views.reportDetail
```

并确保 `router.navigate` 能正确解析 `#report-detail/123?categories=document,ui,code`。

## 需要修改/新建的文件

- `backend/database.py`：新增列与兼容迁移。
- `backend/config.py`：扩展 `ALLOWED_EXTENSIONS`。
- `backend/services/file_parser.py`：新增文件分类函数。
- `backend/services/report_service.py`：分类详情、保存分类评分、总分计算、班级筛选。
- `backend/routers/report.py`：新增 5 个 API。
- `backend/routers/evaluation.py`：分类评分兼容、AI 输出分类结果。
- `backend/routers/training.py`：提交时写入 `class_id/class_name`。
- `backend/migrate_submission_classes.py`：回填已有提交班级信息。
- `frontend/app.js`：改造 `views.report`，新增 `views.reportDetail`，注册路由。
- `frontend/style.css`：新增筛选栏、分类弹窗、报告详情页样式。
- `frontend/index.html`：更新 CSS/JS 缓存版本号。

## 验证方案

1. **数据库迁移**：运行迁移脚本，检查 `submissions` 新列存在且 `class_id` 已回填。
2. **后端 API**：
   - 上传含 `.py`、`.png`、`.docx` 的作业，调用 `/api/report/submission/{id}/categories`，验证返回三类。
   - 提交分类评分，验证 `final_score` 按权重正确计算。
   - 测试 `/api/report/submissions?training_id=1&class_id=2&student_name=张` 筛选。
3. **前端验证**：
   - 切换实训，班级下拉自动更新。
   - 按姓名 Enter 搜索，列表正确过滤。
   - 点击“查看报告”弹出分类选择，未选提示，选中后打开新页面。
   - 新页面可预览文件，修改教师评分时总分实时变化，保存成功。
4. **回归测试**：旧 `/api/report/training/{id}/data` 和学生提交流程不受影响。

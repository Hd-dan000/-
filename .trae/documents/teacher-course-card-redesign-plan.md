# 教师端授课班级卡片三级递进改造计划

## 背景与目标

根据 `新要求2.md` 的赛题解读，教师端需要体现“高校-企业协同实训”的业务场景：实训项目来自企业真实需求，教师按“实训项目 → 授课班级 → 学生成果”三级结构进行教学管理。

当前首页把“课程×班级”平铺成多张卡片，不符合赛题推荐的“按实训项目聚合班级”的导航结构。本次改造目标：

1. 将 `course` 表的课程名称替换为 5 个企业级实训项目名称。
2. 教师端首页改为“实训项目卡片”聚合展示。
3. 点击卡片进入该项目下的班级列表。
4. 点击班级进入学生提交/评价详情页。

## 数据更新策略

用户明确：“相当于把之前 course 中的 `course_name` 属性替换，其余保存不变”。因此：

- 仅更新 `course.course_name` 字段。
- 不删除、不重建 `course`、`teach`、`student_course` 等关联表。
- 由于现有课程记录多于 5 条，按 `id` 顺序循环写入 5 个实训项目名，保证 5 个项目均匀分布。

5 个实训项目名：

1. “智聘”企业级人力资源管理系统（HRMS）
2. “鲜速达”生鲜电商小程序
3. 智慧校园统一数据可视化大屏
4. 云物业收费与服务 SaaS 系统
5. 智能家居设备管控平台

## 后端改造

### 1. 新增数据库更新脚本

文件：`training-evaluation-system/backend/update_course_names.py`

- 按 `course.id` 顺序循环更新 `course_name`。
- 仅修改 `course_name`，保留 `course_code`、`semester`、`teacher_id`、`teacher_name` 及所有关联关系。

### 2. 增强现有课程接口

文件：`training-evaluation-system/backend/routers/courses.py`

- `handle_teacher_courses`：在返回的课程对象中补充
  - `class_count`（已有）
  - `pending_count`：该课程下当前教师所有班级中 `submit_work.status != 'evaluated'` 的作业数
  - `cover_index`：用于前端封面配色 `(id - 1) % 5`
- `handle_teacher_course_classes`：在返回的班级对象中补充
  - `pending_count`：该班级中 `submit_work.status != 'evaluated'` 的作业数

### 3. 新增班级学生详情接口

文件：`training-evaluation-system/backend/routers/courses.py`

新增 `handle_teacher_class_students(handler, class_id)`：

- 校验当前教师是否通过 `teacherclasses` 关联到该班级。
- 查询班级信息（`classes` 表）。
- 查询该班级所有学生（`students` 表）。
- 查询该班级下所有 `submit_work` 提交记录，统计每位学生的提交数、待批数、教师评分。
- 通过 `teach` 表找到班级关联的课程，再查到 SQLite `trainings` 中对应实训，进而从 `submissions` 表读取大模型评分、最终得分。
- 返回结构：`{ class: {...}, students: [...], total: N }`

### 4. 注册新路由

文件：`training-evaluation-system/backend/main.py`

在课程路由区域新增：

```
GET /api/courses/teacher/classes/{class_id}/students
```

## 前端改造

### 1. 首页：实训项目卡片

文件：`training-evaluation-system/frontend/app.js`

- 保留对 `/api/courses/teacher/mine`、`/api/courses/teacher/mine/trainings` 的调用。
- 移除旧的“我的授课班级”平铺逻辑，改为“我的实训项目”卡片网格。
- 新增 `renderCourseCard(course, index)`：
  - 顶部渐变封面（使用 5 套固定渐变，避免依赖图片资源）。
  - 实训项目名称。
  - 学期、主讲教师。
  - 班级数、`pending_count` 待批改数。
- 点击卡片跳转：`course-detail?course_id={id}`。

### 2. 二级页面：班级列表

文件：`training-evaluation-system/frontend/app.js`

新增视图 `views['course-detail']`：

- 从 URL 读取 `course_id`。
- 调用 `/api/courses/teacher/{course_id}/classes`。
- 渲染班级列表项：
  - 班级名称、专业、年级。
  - 学生人数、待批改数。
- 点击班级跳转：`class-students?class_id={id}`。

### 3. 三级页面：学生提交与评价

文件：`training-evaluation-system/frontend/app.js`

新增视图 `views['class-students']`：

- 从 URL 读取 `class_id`。
- 调用 `/api/courses/teacher/classes/{class_id}/students`。
- 以表格展示：
  - 学号、姓名
  - 实训提交状态（未提交 / N份·待评 / N份·已评）
  - LLM评分（`ai_total_score` 均值）
  - 最终得分（`final_score` 均值）
  - 教师评分（`teacher_score`）
  - 操作：查看报告（占位按钮，后续接入智能核查报告）

### 4. 样式补充

文件：`training-evaluation-system/frontend/style.css`

追加三类样式：

- `.course-grid` / `.course-card` / `.course-card-cover` / `.course-card-stats`
- `.class-list-page` / `.class-list-item` / `.class-list-stats`
- `.student-table` / `.status-badge`

采用响应式网格：4 列 → 3 列 → 2 列 → 1 列。

### 5. 缓存版本号

文件：`training-evaluation-system/frontend/index.html`

- `style.css?v=18` → `style.css?v=20`
- `app.js?v=19` → `app.js?v=21`

## 不修改的范围

- 不改动 Vue 前端（`frontend/src/`），本次改造针对当前纯 HTML/JS 教师端。
- 不改动登录、权限、大模型配置等无关页面。
- 不删除 `training` 视图原有的班级开课状态管理功能，仅新增 `course-detail` 和 `class-students` 两个视图。

## 验证步骤

1. **数据库验证**
   - 运行 `python training-evaluation-system/backend/update_course_names.py`。
   - 在 MySQL 中执行 `SELECT id, course_name FROM course`，确认出现 5 个实训项目名且按顺序循环。

2. **后端验证**
   - 重启后端服务。
   - 调用 `GET /api/courses/teacher/mine`，确认返回 `class_count`、`pending_count`、`cover_index`。
   - 调用 `GET /api/courses/teacher/{course_id}/classes`，确认班级对象含 `pending_count`。
   - 调用 `GET /api/courses/teacher/classes/{class_id}/students`，确认返回班级与学生提交/评分数据。

3. **前端验证**
   - 以教师身份登录，进入首页，确认展示“我的实训项目”卡片，含封面、班级数、待批改数。
   - 点击卡片进入班级列表，确认显示该课程下的班级、学生数、待批改数。
   - 点击班级进入学生表，确认展示学号、姓名、提交状态、LLM评分、最终得分、教师评分。
   - 检查 DevTools，确认加载 `style.css?v=20` 和 `app.js?v=21`。

4. **回归验证**
   - 确认顶部导航其他页面（实训管理、评价规则配置、AI评阅报告等）仍可正常访问。

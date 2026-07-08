# 教师实训项目管理功能实现计划

## 背景与目标

实现教师端实训项目的全生命周期管理：教师可新建实训项目并同步持久化到数据库、与班级绑定；支持编辑、归档；设置截止时间、考核维度、上传任务文档、代码提交规范；并在首页提供快捷入口一键进入新建流程。

## 当前状态

- **数据库（`backend/database.py`）**：已完成。
  - `trainings` 表已通过兼容式迁移新增 `deadline`、`dimensions`、`document_url`、`code_standard` 列。
  - 已创建 `training_classes` 关联表，支持实训与班级精确绑定。
- **后端 API**：
  - `backend/routers/training.py`：`handle_create_training`、`handle_update_training`、`handle_list_trainings`、`handle_get_training`、班级绑定与富化逻辑已完成。
  - `backend/routers/courses.py`：`handle_teacher_all_trainings` 已完成，优先读取 `training_classes` 回退课程-班级映射。
  - `backend/main.py`：已注册 `POST /api/training/{id}/document` 路由。
  - `backend/schemas.py`：校验规则已扩展。
- **前端（`frontend/app.js`）**：
  - 实训管理页列表、筛选、新建/编辑弹窗、归档逻辑已完成。
  - 弹窗已包含标题、截止时间、所属课程、考核维度、文档链接/上传、代码规范、分配班级。
  - 首页“创建实训任务”快捷按钮已跳转至 `#training?action=create`。
  - `views.training.render` 已检测 `action=create` 自动打开弹窗。
- **已知缺陷**：文档上传接口 `POST /api/training/{id}/document` 返回 500，`IndexError('list index out of range')`。

## 待完成工作

### 1. 修复文档上传 `IndexError`

**位置**：`backend/main.py` → `RequestHandler.parse_form_body`

**根因**：multipart 每个 part 在 boundary 后紧跟 `\r\n`，`part.split(b'\r\n')` 后首行是空字节串 `b''`。`while i < len(lines) and lines[i]:` 在 `i=0` 时即因 `lines[0]` 为空而退出，导致 `headers` 为空；后续解析 `Content-Disposition` 时 `split('name=')[1]` 越界。

**修复方案**：进入 part 解析前先 `part = part.strip(b'\r\n')`，或在首个 `while` 前跳过前导空行。

```python
for part in parts[1:-1]:
    lines = part.strip(b'\r\n').split(b'\r\n')
    # 后续逻辑保持不变
```

### 2. 前端文件上传校验

**位置**：`frontend/app.js` → `views.training.renderModal` 中 `doc-upload` 的 `onchange`

**需补充**：
- 文件大小校验：读取 `MAX_UPLOAD_SIZE`（默认 50MB），超限提示。
- 文件类型校验：限制为 `.pdf`、`.doc`、`.docx`、`.txt`、`.md` 等，与后端 `ALLOWED_EXTENSIONS` 对齐。
- 不符合条件时清空 `pendingFile` 并恢复上传区域文案。

### 3. 文档链接/上传状态展示优化

**位置**：`frontend/app.js` → `renderTrainingCard`

**需补充**：
- 若 `documentUrl` 为 `/uploads/...` 本地路径，点击应正确打开。
- 编辑弹窗中已上传文档应提供“删除/替换”视觉反馈。

### 4. 端到端验证

- 启动服务，教师登录后点击首页“创建实训任务”。
- 填写表单、选择班级、上传本地文档，确认 `POST /api/training/create` 与 `POST /api/training/{id}/document` 均 200。
- 确认 SQLite `trainings` 记录、`training_classes` 绑定、`uploads/training_{id}/` 文件均正确。
- 编辑实训：修改字段、替换文档、调整班级，确认 `PUT /api/training/{id}` 成功且绑定全量替换。
- 归档实训：确认 `status` 变为 `archived`，并在“已归档”标签可见。
- 不选择文件直接保存：确认不调用上传接口，仅保存其他字段。

## 涉及文件

- `backend/main.py`（修复 multipart 解析）
- `frontend/app.js`（前端上传校验与状态展示）
- `frontend/style.css`（如需补充已归档/文档状态样式）

## 范围说明

- 本次改动聚焦教师端 plain JS 界面与后端 multipart 解析 bug，Vue 前端（`frontend/src/views/TrainingList.vue` 等）暂不改。
- 不新增数据库表结构，仅修复现有逻辑并补齐前端校验。

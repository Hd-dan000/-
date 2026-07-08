# 实训项目与课程整合实施计划

## 一、任务概述

明确 `course 表 = 实训项目`：教师新建实训项目时，系统自动在 MySQL `course` 表中生成同名课程记录；教师在首页「我的实训项目」卡片中查看自己管理的项目，状态按「未开始 / 进行中 / 已截止」分类展示；首页最多展示 8 张卡片（2 行 × 4 列），超出时显示「更多」入口跳转实训管理页。

## 二、当前状态分析

### 2.1 后端（已完成）
- `backend/routers/training.py`：
  - `handle_create_training` 在 `course_id` 为空时自动调用 `_create_course_for_training` 创建 `course` 记录。
  - 项目标题变更时同步更新 `course.course_name`。
  - SQLite 写入失败时回滚已创建的 `course` 记录。
- `backend/routers/auth.py`：`get_teacher_course_ids` 合并 `teach` 表与 `course.teacher_id` 查询，确保教师可见自己创建的项目课程。
- `backend/routers/courses.py`：`handle_teacher_courses` 使用 `UNION` 合并两类课程来源。

### 2.2 前端（待完成）
- `frontend/app.js`：
  - 首页 `renderTrainingCard` 将 `ended` 映射为「已结束」，需统一为「已截止」。
  - 首页实训卡片未做数量限制，需限制最多 8 张并追加「更多」卡片。
  - 实训管理页统计标签与筛选标签仍为「已结束」，需改为「已截止」。
  - `views.training.statusTextMap` 中 `ended` 文案为「已结束」，需改为「已截止」。
  - `saveTraining` 仍强制依赖 `self.data.courses[0].id`，新模式下创建项目不应再要求课程 ID，应允许后端自动创建 `course`。
- `frontend/style.css`：缺少「更多」卡片样式。
- `frontend/index.html`：静态资源缓存版本仍为 `?v=30`，需升级以刷新浏览器缓存。

## 三、待修改文件及具体变更

### 3.1 `frontend/app.js`

#### 1) 首页实训卡片状态映射（约 L357-L363）
将 `ended` 的展示文案从「已结束」改为「已截止」：

```javascript
const statusMap = {
    not_started: { cls: 'tag-info', text: '未开始' },
    in_progress: { cls: 'tag-success', text: '进行中' },
    active: { cls: 'tag-success', text: '进行中' },
    ended: { cls: 'tag-warning', text: '已截止' },
    archived: { cls: 'tag-danger', text: '已归档' }
};
```

#### 2) 首页卡片数量限制与「更多」入口（约 L455-L465）
限制首页最多渲染 8 张卡片；超出时追加「更多」卡片，点击跳转 `#training`：

```javascript
const showMore = trainings.length > 8;
const displayTrainings = trainings.slice(0, 8);
const trainingCards = displayTrainings.map((t, i) => this.renderTrainingCard(t, i)).join('') +
  (showMore ? `
    <div class="course-card more-card" onclick="router.navigate('training')">
      <div class="more-card-inner">
        <div class="more-card-icon">›</div>
        <div class="more-card-text">更多</div>
        <div class="more-card-sub">查看全部 ${trainings.length} 个项目</div>
      </div>
    </div>
  ` : '');
```

#### 3) 实训管理页状态文案统一
- `statusTextMap`（约 L902-L908）：`ended: '已截止'`。
- 统计卡片标签（约 L1537）：`已结束` → `已截止`。
- 筛选标签（约 L1549）：`已结束` → `已截止`。

#### 4) 创建项目时解除对 `courses` 数组的强依赖（约 L1087-L1136）
- 移除 `courseId = self.data.courses && self.data.courses[0] ? self.data.courses[0].id : ''` 的强制取值。
- 移除 `if (!courseId)` 的拦截提示。
- 新建时 `course_id` 传 `null`（或不传），让后端自动创建 `course` 记录；编辑时保持原 `course_id`。

```javascript
const courseId = self.data.editingId ? (self.data.formData.courseId || '') : '';
// ... 移除 !courseId 校验 ...
course_id: courseId ? parseInt(courseId, 10) : null,
```

### 3.2 `frontend/style.css`

在 `.course-grid` 样式附近新增「更多」卡片样式：

```css
.more-card {
    cursor: pointer;
    border: 2px dashed var(--border-color);
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 180px;
    transition: var(--transition);
}

.more-card:hover {
    border-color: var(--primary-color);
    background: var(--bg-hover);
}

.more-card-inner {
    text-align: center;
    color: var(--text-secondary);
}

.more-card-icon {
    font-size: 32px;
    line-height: 1;
    margin-bottom: 8px;
    color: var(--text-muted);
}

.more-card-text {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 4px;
}

.more-card-sub {
    font-size: 13px;
    color: var(--text-muted);
}
```

### 3.3 `frontend/index.html`

将 `style.css` 与 `app.js` 的版本号从 `?v=30` 升级为 `?v=31`：

```html
<link rel="stylesheet" href="style.css?v=31">
<script src="app.js?v=31"></script>
```

## 四、验证步骤

1. 启动后端服务，以教师身份登录。
2. 在首页点击快捷入口「新建实训项目」，填写标题、截止时间、选择班级后创建。
3. 确认：
   - 请求体中 `course_id` 为 `null` 或不传。
   - MySQL `course` 表中新增一条 `course_name` 与项目标题一致的记录。
   - 页面返回 200，toast 提示创建成功。
4. 返回首页：
   - 「我的实训项目」区域按「未开始 / 进行中 / 已截止」展示卡片。
   - 当项目 ≤8 个时全部展示；>8 个时展示 8 张卡片 + 1 张「更多」卡片。
   - 点击「更多」跳转实训管理页。
5. 进入实训管理页：
   - 统计卡片与筛选标签中 `ended` 显示为「已截止」。
   - 列表中项目状态标签显示为「已截止」。
6. 刷新浏览器（确保加载 `?v=31` 新版本），重复步骤 4-5。

## 五、假设与决策

- 假设后端 `handle_create_training` 已能正确处理 `course_id` 为空/为 `null` 的情况并自动创建 `course`（当前代码符合）。
- 决策：首页采用固定 8 张上限（2 行 × 4 列），与现有 `.course-grid { grid-template-columns: repeat(4, 1fr) }` 保持一致。
- 决策：状态文案统一为「已截止」，同时保留 `ended` 作为内部状态码不变。
- 决策：创建时不传有效 `course_id`，编辑时保留原 `course_id`，避免误将已有项目重新关联到新课程。

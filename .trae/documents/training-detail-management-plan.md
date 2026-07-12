# 实训项目详情管理页实现方案

## 背景与目标

当前教师点击首页/实训管理页的实训卡片后，仅跳转到 `training` 列表或没有任何详情页。用户参考设计图，要求实现一个**实训项目详情管理页**，作为点击卡片后的落地页，包含：

1. **实训基础信息栏目**：展示实训名称、周期、归属班级、实训类型（个人/小组标签）、截止时间、当前状态，并提供“修改实训配置”“导出全部实训数据”“一键重置提交记录”等操作。
2. **提交状态以及查看栏目**：严格参考图片风格与配色，包含筛选栏、批量操作、小组/个人卡片列表、分页。
3. **个人/小组适配**：创建实训时若选择“小组”，筛选栏显示“分组筛选”；若选择“个人”，显示“个人筛选”。

目标文件：`frontend/app.js`、`frontend/style.css`。

## 现有基础

- `index.html` 通过 `<script src="app.js?v=45">` 加载单页应用，路由采用 `window.location.hash`，视图注册在 `views` 对象中。
- `views.training` 已包含：
  - `normalizeTraining()`：标准化实训数据。
  - `renderTrainingCard()`：渲染实训卡片（当前点击无详情跳转）。
  - `formData.trainingType` / `groupSize`：创建实训时区分个人/小组。
  - `saveCreateTraining()`：提交 `training_type`、`group_size` 到后端。
- 现有 CSS 变量与组件：`.tag-*`、`.btn-*`、`.filter-select`、`.search-box`、`.training-toolbar` 等可直接复用。
- 现有 API 工具：`api.get/post/put/delete`，失败时提供 mock 数据兜底。
- 后端目前无独立 `groups` 表，小组需前端按 `groupSize` 取模构建；静态预览以 mock 数据为主。

## 实现方案

### 1. 新增视图 `views['training-detail']`

在 `app.js` 的 `views` 对象中新增 `training-detail` 视图，数据结构：

```js
data: {
    trainingId: null,
    training: null,
    submissions: [],
    groups: [],           // 小组模式下的分组列表
    students: [],         // 个人模式下的学生列表
    filters: {
        status: 'all',    // 提交状态
        scoreRange: 'all',// 评分区间
        group: 'all',     // 分组/个人筛选
        search: ''        // 搜索学生姓名/学号/小组名
    },
    selectedIds: [],      // 批量选中项
    pagination: { page: 1, pageSize: 10, total: 0 },
    loading: false
}
```

关键方法：

- `parseParams()`：从 `hash` 读取 `id`。
- `loadTraining()`：调用 `/training/${id}`，失败使用 `mockTraining()`。
- `loadSubmissions()`：调用 `/training/${id}/submissions`，失败使用 `mockSubmissions()`。
- `buildGroups()`：小组模式下按 `groupSize` 将学生/提交聚合成小组；个人模式直接展示学生列表。
- `applyFilters()`：根据筛选条件过滤并分页。
- `render()`：整体渲染。
- `renderBasicInfo()`：顶部基础信息栏。
- `renderFilterBar()`：筛选与批量操作栏（动态“分组筛选/个人筛选”标签）。
- `renderSubmissionCards()`：小组/个人卡片列表（含文件预览、分数、状态、操作按钮）。
- `renderPagination()`：底部分页。
- 事件方法：`onFilterChange`、`onSearch`、`onBatchAction`、`onResetSubmissions`、`onExport`、`toggleSelect`、`onPageChange` 等。

### 2. 修改实训卡片跳转

在 `views.training.renderTrainingCard()` 中：

- 将卡片主体点击事件从 `router.navigate('training')` 改为 `router.navigate('training-detail?id=${training.id}')`。
- 保留编辑/归档按钮的 `stopPropagation`，避免与卡片跳转冲突。
- 同步修改 `dashboard.renderTrainingCard()` 中的卡片跳转（当前也指向 `training`）。

### 3. 样式扩展（`style.css`）

新增 `.td-*` 前缀的样式类，避免与现有类冲突：

- `.td-page`：页面容器，浅灰背景、内边距。
- `.td-basic-card` / `.td-basic-grid`：基础信息卡片与网格布局。
- `.td-type-tag` / `.td-status-tag`：类型标签（橙色=小组，蓝色=个人/状态）。
- `.td-filter-bar`：筛选栏弹性布局。
- `.td-batch-bar`：批量操作与右侧功能按钮区域。
- `.td-group-card` / `.td-person-card`：卡片主体，含左侧序号、名称、成员、分数、文件预览、操作按钮。
- `.td-file-preview`：文件图标预览区（zip/pdf/png/docx）。
- `.td-action-group`：卡片右侧纵向/横向操作按钮组。
- `.td-pagination`：分页组件。

颜色严格遵循设计图：
- 小组实训类型标签：背景 `#FFF7E6` / 文字 `#FA8C16`。
- 状态标签“待评审”：背景 `#E6F7FF` / 文字 `#1677FF`。
- 已提交待评审：背景 `#E6F7FF` / 文字 `#1677FF`。
- 逾期提交：背景 `#FFF2F0` / 文字 `#FF4D4F`。
- 未提交：背景 `#F2F3F5` / 文字 `#86909C`。
- 操作按钮：主色 `#1677FF`，危险 `#FF4D4F`。

### 4. Mock 数据

为无后端环境提供完整预览：

- `mockTraining(id)`：返回包含 `trainingType: 'group'`，`groupSize: 4`，`assignedClasses: ['2023级软件工程2班']` 等的实训对象。
- `mockSubmissions()`：返回 12~15 条学生提交记录，含文件列表、分数、状态、提交时间，覆盖“已提交待评审”“逾期提交”“未提交”等状态。
- `buildGroups()` 基于 mock 学生列表与 `groupSize` 生成 3~4 个小组。

### 5. 响应式

- 宽屏：基础信息 4 列网格，筛选栏一行排列，卡片主体左右布局。
- 中屏：基础信息 2 列，筛选栏换行，卡片主体上下布局。
- 窄屏：单列堆叠，操作按钮横向滚动或换行。

## 关键文件

- `F:\xiangmu\training-evaluation-system\frontend\app.js`：新增 `views['training-detail']`、修改卡片跳转、新增 mock 方法。
- `F:\xiangmu\training-evaluation-system\frontend\style.css`：追加 `.td-*` 样式块。

## 实施步骤

1. 在 `app.js` 中新增 `views['training-detail']` 的数据结构与方法骨架。
2. 实现 `loadTraining`、`loadSubmissions`、`buildGroups`、`applyFilters`。
3. 实现 `renderBasicInfo`、`renderFilterBar`、`renderSubmissionCards`、`renderPagination`。
4. 实现事件处理方法与 mock 数据。
5. 修改 `views.training.renderTrainingCard` 与 `views.dashboard.renderTrainingCard` 的跳转链接。
6. 在 `style.css` 末尾追加全部 `.td-*` 样式。
7. 启动本地静态服务器，访问 `http://localhost:8088/index.html#training-detail?id=1` 预览。
8. 验证：
   - 基础信息展示完整、类型/状态标签颜色正确。
   - 小组模式显示“分组筛选”，个人模式显示“个人筛选”。
   - 卡片列表、文件预览、分数、状态、操作按钮按图布局。
   - 分页、搜索、筛选交互正常。
   - 从首页/实训页点击卡片正确进入详情页。

## 待确认 / 风险

1. 后端暂无独立 `groups` 表，小组数据由前端按 `groupSize` 聚合；后续若需持久化分组，需后端新增表与接口。
2. “一键重置提交记录”属于高风险操作，本版本仅做确认弹窗 + toast 占位，不实际调用删除接口。
3. 文件预览中的图标使用静态 emoji/SVG，真实文件下载需后端文件接口支持。

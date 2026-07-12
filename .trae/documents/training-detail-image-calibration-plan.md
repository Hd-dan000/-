# 实训详情管理页 – 按图三校准计划

## 1. 摘要
现有 `training-detail` 视图已具备「实训基础信息」「提交状态及查看」「小组/个人动态筛选」等完整功能。本计划基于用户提供的图三，对 **提交状态及查看栏目** 的批量操作栏、状态标签、逾期提示、小组卡片圆角与文件预览等视觉细节进行精确校准，使颜色、布局与参考图保持一致。

## 2. 当前状态分析
- **入口文件**：`f:\xiangmu\training-evaluation-system\frontend\index.html`（CSS/JS 版本号需更新以清缓存）。
- **逻辑与渲染**：`f:\xiangmu\training-evaluation-system\frontend\app.js` 的 `views['training-detail']`（约 3803–4469 行）。已实现：
  - 动态小组/个人筛选（`分组筛选` / `个人筛选`）。
  - 提交状态、评分区间、搜索、重置。
  - 批量操作（AI 评审、批注、退回、导出）。
  - 小组/个人卡片渲染、文件预览、分页。
- **样式**：`f:\xiangmu\training-evaluation-system\frontend\style.css` 的 `.td-*` 区域（6060–6613 行）。已基本覆盖页面结构，但与图三相比存在以下偏差：
  - 批量操作栏按钮风格与图三不一致（缺少“主按钮 + 描边按钮 + 文字链接”的层次）。
  - 逾期状态标签为红色，图三为橙色标签 + 红色逾期天数提示。
  - 小组卡片 `小组 01` 标签圆角不足，未形成图三的圆角胶囊感。
  - 未提交卡片缺少图三的“暂无提交”占位文案。
  - 批量/卡片按钮缺少图三中对应的图标前缀。

## 3. 拟修改内容

### 3.1 `app.js` – `views['training-detail']`
| 位置 | 修改项 | 说明 |
|------|--------|------|
| `renderBatchBar()` | 按钮样式分层 | `批量触发AI评审` 保持主色按钮；`批量下发批注`、`批量退回重提交` 改为蓝色描边按钮；`导出选中数据` 改为带下载图标的文字链接。每个按钮增加对应图标。 |
| `renderGroupCard()` | 逾期提示 | 对 `late` 状态的小组/个人卡片，在提交时间下方增加红色 `（已逾期X天）` 提示。新增 `getOverdueDays(submitTime, deadline)` 辅助方法。 |
| `renderGroupCard()` / `renderPersonCard()` | 未提交占位 | 当状态为 `not_submitted` 时，状态区显示 `暂无提交` 灰色小字，替代空白。 |
| `renderFilterBar()` | 搜索占位 | 保持 `搜索学生姓名、学号或小组名称`，与图三一致。 |
| `mockTraining()` / `mockSubmissions()` | 演示数据 | 让部分模拟提交为 `late`，且提交时间超过 `deadline` 1 天，便于验证逾期提示。 |

### 3.2 `style.css` – `.td-*` 区域
| 选择器 | 修改项 | 目标效果 |
|--------|--------|----------|
| `.td-group-badge` | `border-radius` 从 `var(--radius-sm)` 改为 `12px` | 与图三小组标签的胶囊圆角一致。 |
| `.td-tag-late` | 背景 `#FFF7E6`、文字 `#FA8C16`、边框 `#FFD591` | 逾期标签改为橙色，与图三一致。 |
| 新增 `.td-overdue-note` | `color: #FF4D4F; font-size: 12px; margin-top: 4px;` | 红色逾期天数提示。 |
| 新增 `.td-batch-btn-outline` | 蓝边蓝字白底，hover 背景 `#E6F7FF` | 批量下发批注、批量退回重提交。 |
| 新增 `.td-batch-link` | 纯文字链接 `#1677ff`，带图标间距 | 导出选中数据。 |
| `.td-batch-bar` / `.td-batch-left` | 调整间距与按钮高度 32px | 与筛选栏视觉对齐。 |
| `.td-card-actions` / `.td-action-btn` | 略微缩小 padding 与字号，保持右对齐 | 减少卡片右侧拥挤感。 |
| `.filter-select`（若已有则覆盖） | 统一高度 32px、圆角 6px、边框 `#D7D8DA` | 与图三筛选下拉框一致。 |

### 3.3 `index.html`
- 将 `style.css?v=43` 与 `app.js?v=46` 的版本号各 +1（分别改为 `v=44`、`v=47`），确保浏览器加载最新样式与逻辑。

## 4. 实现步骤
1. 修改 `app.js`：
   - 重写 `renderBatchBar()`，使用新的按钮样式类与图标。
   - 在 `renderGroupCard()` / `renderPersonCard()` 中加入逾期天数与未提交占位文案。
   - 新增 `getOverdueDays()` 辅助函数。
   - 调整 mock 数据，使 late 记录产生逾期 1 天。
2. 修改 `style.css`：
   - 调整 `.td-group-badge`、`.td-tag-late`。
   - 新增 `.td-overdue-note`、`.td-batch-btn-outline`、`.td-batch-link`。
   - 微调批量栏与卡片操作按钮尺寸。
3. 修改 `index.html` 版本号。
4. 本地验证：
   - 启动 `npx serve -l 8088`。
   - 访问 `http://localhost:8088/index.html#training-detail?id=1`。
   - 截图对比图三，检查批量栏按钮、状态标签颜色、逾期提示、小组标签圆角、文件预览。

## 5. 假设与决定
- **动作按钮保留**：图三截图中未显示单条卡片的操作按钮，但前期需求明确要求“查看、AI 评审、人工打分、下发批注、退回重提交”等功能，因此保留卡片右侧操作区，仅做样式压缩，不删除。
- **逾期天数计算**：以实训 `deadline` 与 `submitTime` 日期差为准；若 `deadline` 缺失则取当前日期，确保演示数据能显示 `已逾期1天`。
- **图标来源**：沿用现有内联 SVG，批量操作按钮按图三语义补充对应 SVG（机器人/批注/退回/下载）。

## 6. 验证标准
- 页面能正常打开，`分组筛选` 下拉显示 `全部小组`。
- 批量操作栏从左到右依次为：主色「批量触发AI评审」、描边「批量下发批注」、描边「批量退回重提交」、文字链接「导出选中数据」。
- 逾期卡片状态标签为橙色，下方出现红色 `（已逾期1天）`。
- 未提交卡片状态标签为灰色，下方显示 `暂无提交`。
- 小组标签 `小组 01` 为蓝色圆角胶囊。
- 文件预览区显示图标 + 文件名，与图三一致。

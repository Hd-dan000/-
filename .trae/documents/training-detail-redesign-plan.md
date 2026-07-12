# 实训项目管理详情页改造方案

## 背景与目标

当前教师点击实训项目卡片后进入的 `training-detail` 页面是一个单页小组列表，包含基础信息、筛选栏、批量操作和分页。用户参考三张设计图，要求将该页面改造为**三标签页**的综合管理界面：

1. **评价评阅管理**：按维度/指标对小组进行 AI 评分与教师评分，展示 AI 评审报告、雷达图、结论与操作按钮。
2. **分组/人员管理**：展示实训分组统计、按小组/个人切换的列表、成员详情卡片。
3. **实训数据统计**：展示实训整体数据看板，包括统计卡片、分数分布柱状图、能力维度雷达图、提交时间折线图、小组平均分排名与导出按钮。

## 设计原则

- 参考图风格：浅灰背景、白色卡片、圆角、蓝色主色、清晰的分割线与标签。
- 沿用项目现有技术栈：原生 JS + 视图对象 `views['training-detail']`、样式统一写入 `style.css`、图表使用已加载的 Chart.js 4.4.8。
- 保持与现有代码的兼容性：保留 `normalizeTraining`/`normalizeSubmission`、`buildGroups` 等已有方法，新增功能以扩展方式实现。
- 在无后端环境下可正常预览：所有新接口失败时均有 mock 数据兜底。

## 关键文件

- `F:\xiangmu\training-evaluation-system\frontend\app.js`：重写 `views['training-detail']` 的渲染与交互逻辑。
- `F:\xiangmu\training-evaluation-system\frontend\style.css`：追加新标签页、评分表、统计卡片、图表等样式。
- `F:\xiangmu\training-evaluation-system\frontend\index.html`：Chart.js 已加载，无需改动（如版本号需更新则单独处理）。

## 数据模型扩展

在 `views['training-detail'].data` 中保留原有字段，并新增：

```js
{
    activeTab: 'review',          // 'review' | 'groups' | 'stats'
    selectedGroupId: null,        // 评价评阅管理当前选中的小组
    selectedMemberId: null,       // 分组/人员管理-按个人当前选中的成员
    groupSubTab: 'byGroup',       // 'byGroup' | 'byMember'
    indicators: [],               // 当前实训评价指标（来自 evaluation_indicators）
    reportData: null,             // 统计与报告数据缓存
    chartInstances: {},           // Chart.js 实例，切换 tab 时销毁
    reviewDraft: {},              // { indicatorId: { teacherScore, deductionReason } }
}
```

`reset()` 中同步清空新增字段。

## 主要方法规划

### 数据加载

- `loadIndicators(trainingId)`：调用 `/evaluation/indicators/${trainingId}`，失败使用 `mockIndicators()`。
- `loadReportData(trainingId)`：调用 `/report/training/${trainingId}/data`，失败使用 `mockReportData()`。
- `selectGroup(groupId)` / `selectMember(memberId)`：设置当前选中对象并局部重绘。
- `switchTab(tab)` / `switchGroupSubTab(subTab)`：切换标签页，触发 `render()` 并在 DOM 更新后初始化图表。

### 渲染方法

- `renderTabs()`：顶部三个主标签页按钮。
- `renderBasicInfoBar()`：顶部精简实训基础信息条（保留用户原要求的“实训基础信息”）。
- `renderTabContent()`：根据 `activeTab` 分发。
- `renderReviewTab()`：评价评阅管理两栏布局。
  - `renderScoringTable()`：左侧维度/指标评分表。
  - `renderAIReport()`：左侧 AI 评审报告（总分、雷达图、结论列表、按钮）。
  - `renderGroupInfoPanel()`：右侧当前小组/成员信息。
- `renderGroupManageTab()`：分组/人员管理。
  - `renderGroupStatsCards()`：顶部统计卡片。
  - `renderGroupSubTabs()`：按小组 / 按个人。
  - `renderGroupListTable()` / `renderMemberListTable()`：列表表格。
  - `renderMemberCards()`：成员详情卡片。
- `renderStatsTab()`：实训数据统计。
  - `renderStatsCards()`：统计卡片（总人数、已提交、未提交、平均分、最高分）。
  - `renderScoreDistributionChart()`：分数分布柱状图。
  - `renderStatsRadarChart()`：能力维度雷达图。
  - `renderSubmissionTimeChart()`：提交时间折线图。
  - `renderGroupRanking()`：小组平均分排名。

### 事件与图表

- `onTeacherScoreChange(indicatorId, value)` / `onDeductionReasonChange(...)`：更新 `reviewDraft`。
- `saveReviewDraft()` / `confirmReview()` / `returnForResubmit(group)` / `exportStats(format)`：操作按钮，暂以 toast 或占位实现。
- `destroyCharts()` / `initCharts()`：Chart.js 实例生命周期管理，复用 `growth` 视图模式。

## Mock 数据

新增以下 mock 方法，确保静态预览完整：

- `mockIndicators()`：4 个指标，分为“文档质量”“代码规范”“功能实现”等维度，带权重。
- `mockReportData(trainingId)`：包含 training、submissions、statistics、dimensions、score_distribution、submission_hours、group_ranking。
- 扩展现有 `mockSubmissions()` 的 `evaluation_detail`，增加 `indicator_summary`、`category_evaluation`、`overall_comment`、`conclusions`。

## CSS 新增（追加到 style.css 实训详情区块后）

- `.td-tabs` / `.td-tab` / `.td-tab.active`：顶部标签页。
- `.td-basic-bar`：精简基础信息条。
- `.td-review-layout`：两栏网格（左侧评分/报告，右侧小组信息）。
- `.td-score-table`、`.td-dimension-row`、`.td-score-input`：评分表。
- `.td-ai-report`、`.td-total-score`、`.td-conclusion-list`：AI 评审报告。
- `.td-stats-grid`、`.td-stat-card`、`.td-stat-value`：统计卡片。
- `.td-chart-row`、`.td-chart-card`、`.td-chart-wrap`：图表卡片。
- `.td-ranking-list`、`.td-ranking-item`：小组排名。
- `.td-group-table`、`.td-member-grid`、`.td-member-card`：分组/人员管理表格与卡片。
- 响应式：窄屏下 `.td-review-layout`、`.td-chart-row`、`.td-stats-grid` 变为单列或两列。

## 实施步骤

1. 扩展 `views['training-detail'].data` 与 `reset()`。
2. 在 `style.css` 追加全部新样式类。
3. 实现 mock 数据方法（indicators、report data、evaluation_detail）。
4. 实现数据加载方法（`loadIndicators`、`loadReportData`）并在 `render()` 中调用。
5. 改造 `render()`：渲染精简基础信息条 + 标签页 + 标签内容容器。
6. 实现 `renderReviewTab()` 及其子方法，包括评分输入、AI 报告、小组信息面板。
7. 实现 `renderGroupManageTab()` 及其子方法，包括统计卡片、子标签、表格、成员卡片。
8. 实现 `renderStatsTab()` 及其子方法，包括统计卡片与三种 Chart.js 图表。
9. 实现图表生命周期管理（`destroyCharts` / `initCharts`）和事件处理。
10. 本地静态服务器预览，验证三个标签页、mock 数据、图表、筛选与交互。

## 验证方式

- 启动 `npx serve -l 8088`（已在后台运行）。
- 浏览器访问 `http://localhost:8088/index.html#training-detail?id=1`。
- 验证：
  1. 顶部精简基础信息条显示正常。
  2. 三个标签页可切换，各自内容完整。
  3. 评价评阅管理：可选择小组，评分表、AI 报告、雷达图、结论列表、操作按钮正常。
  4. 分组/人员管理：统计卡片、子标签切换、小组表格、成员卡片正常。
  5. 实训数据统计：统计卡片、分数分布柱状图、雷达图、提交时间折线图、小组排名正常。
  6. 切换标签页时图表无残留/空白。

## 待确认 / 风险

1. 当前后端没有独立的 `groups` 表，小组由 `buildGroups()` 按 `groupSize` 取模生成；若需要固定分组，需后端新增表与接口。
2. 后端 `submissions.category_teacher_scores` 是按 `document/ui/code` 存储的，与参考图按指标维度打分不完全一致；本次前端按 indicators 展示，提交时以指标聚合回写或仅做本地草稿。
3. 统计页时间分布、小组排名等数据在后端暂无直接接口，由前端基于 submissions 聚合或 mock 数据提供。
4. 评分输入框使用 `onchange` 避免字符串模板重渲染导致失焦。

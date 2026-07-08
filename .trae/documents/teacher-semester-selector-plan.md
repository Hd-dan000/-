# 教师端顶部学年/学期下拉选择框设计方案

## 背景与目标

用户提供了下拉选择框截图，希望教师端增加一个风格一致的学年/学期选择器，并放在显眼位置。截图中：
- 触发按钮为蓝底白字，显示当前选中项，右侧有上下箭头；
- 下拉菜单为白底，选中项高亮为蓝色，其余为灰色；
- 选项格式为「2025-2026学年-第2、3学期」。

## 现有基础

- 当前教师端顶部为横向导航栏，左侧有 Logo/标题/搜索框，右侧有通知/用户区。
- 课程表 `course.semester` 存有学期数据，格式如 `2024-2025-1`。
- 教师课程接口 `/api/courses/teacher/mine` 会返回 `semester` 字段。
- 当前仅有真实数据 `2024-2025-1`，格式化为「2024-2025学年-第1学期」。

## 涉及文件

- `training-evaluation-system/frontend/index.html`：在顶部导航栏显眼位置插入学年学期选择器 DOM。
- `training-evaluation-system/frontend/style.css`：添加选择器按钮、下拉菜单、选项高亮等样式。
- `training-evaluation-system/frontend/app.js`：添加选择器初始化、展开/收起、选项渲染、选中状态与 localStorage 持久化逻辑。

## 实施方案

### 1. 位置选择

将学年学期选择器放在顶部导航栏左侧区域、搜索框旁边，具体在 `.global-search` 之前。这样：
- 与 Logo/标题同处左侧，一眼可见；
- 不影响右侧通知/用户操作区；
- 作为全局上下文选择器，符合常见 B 端系统布局。

### 2. index.html

在 `.top-header-left` 内、`.global-search` 前插入：

```html
<div class="semester-selector" id="semester-selector">
    <button class="semester-trigger" id="semester-trigger">
        <span id="semester-label">2024-2025学年-第1学期</span>
        <svg class="semester-arrow" id="semester-arrow" ...>...</svg>
    </button>
    <div class="semester-dropdown" id="semester-dropdown" style="display:none">
        <div class="semester-options" id="semester-options"></div>
    </div>
</div>
```

### 3. style.css

- `.semester-selector`：相对定位，作为下拉容器。
- `.semester-trigger`：蓝底（`var(--primary)`）白字圆角按钮，内边距与搜索框高度一致，hover 变深；右侧箭头图标，展开时旋转 180°。
- `.semester-dropdown`：绝对定位，白底，圆角，阴影，顶部与触发按钮对齐，带小三角箭头指向触发按钮。
- `.semester-option`：选项行，内边距 10px 16px，hover 浅蓝背景。
- `.semester-option.selected`：文字蓝色、背景浅蓝，左侧可不加图标，仅文字高亮。
- 小屏下隐藏搜索框时仍保留选择器；若空间不足可将选择器字号略微缩小。

### 4. app.js

新增 `semesterSelector` 模块：
- `init()`：
  - 从 `localStorage` 读取已保存的 `teacher_selected_semester`；
  - 调用 `/api/courses/teacher/mine`，提取 `semester` 去重列表；
  - 若接口无数据，使用默认选项 `['2024-2025-1']`；
  - 将学期值格式化为「YYYY-YYYY学年-第N学期」；
  - 相同学年的多个学期合并为「第1、2学期」样式（当前数据只有 1 个，逻辑保留即可）；
  - 渲染下拉选项，设置当前选中项。
- `toggle()`：点击触发按钮时显示/隐藏下拉菜单，同步箭头旋转。
- `select(value)`：点击选项后更新按钮文字、高亮选项、保存到 `localStorage`、关闭下拉。
- 点击页面其他区域时自动关闭下拉。
- 在 `DOMContentLoaded` 中调用 `semesterSelector.init()`。

**格式化规则**
- 输入：`2024-2025-1`
- 输出：`2024-2025学年-第1学期`
- 多学期合并：`['2024-2025-1', '2024-2025-2']` → `2024-2025学年-第1、2学期`

### 5. 与现有功能的关系

- 本次仅作为全局 UI 选择器实现，暂不对 dashboard 班级卡片、实训管理等内容做按学期过滤（可在后续迭代中接入）。
- 选择器状态保存在 `localStorage`，后续过滤功能可直接读取。

## 不改动范围

- 不修改后端 API、数据库。
- 不改动登录页、学生端及其他视图核心逻辑。
- 不在本次实现按学期过滤数据。

## 验证步骤

1. `node --check app.js` 语法检查通过。
2. 启动后端服务，教师账号 `TCH202401 / 2401` 登录。
3. 访问 `index.html#dashboard` 并 Ctrl+F5 刷新。
4. 检查顶部导航栏左侧是否出现蓝底白字的学年学期选择器。
5. 点击选择器：
   - 下拉菜单展开，显示学期选项；
   - 选中项为蓝色高亮；
   - 切换选项后触发按钮文字同步更新；
   - 点击页面空白处下拉关闭。
6. 刷新页面后确认选中项保持（localStorage 生效）。

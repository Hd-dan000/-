# 学生端 student.html 加载失败修复

## 问题
学生端 `student.html` 登录后显示"加载失败"，因为调用了**不存在的 API 路径**。

## 修复内容

### 3 个错误 API 端点修复

| Tab 页 | 原来的错误路径 | 修正为 |
|--------|---------------|--------|
| 实训任务 | `/api/training/student/list` (不存在) | `/api/training/my-projects` |
| 作业提交 | `/api/homework/student/my-submissions` (不存在) | `/api/submissions/student/mine` |
| 评价报告 | `/api/homework/student/reports` (不存在) | `/api/submissions/student/mine` + 过滤 `status === 'evaluated'` |

### 数据格式兼容
`handle_student_submissions` 直接返回 JSON 数组，所以添加了 `Array.isArray(data)` 判断来兼容两种格式。

### 正确的 API 路径
- 首页 & 我的项目：`GET /api/training/my-projects` → `handle_student_my_projects`
- 提交记录 & 评价报告：`GET /api/submissions/student/mine` → `handle_student_submissions`

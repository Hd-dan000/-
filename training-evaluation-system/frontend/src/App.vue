<template>
  <el-container class="app-container">
    <el-aside width="220px" class="app-sidebar">
      <div class="logo">
        <el-icon :size="28"><Monitor /></el-icon>
        <span>实训评价系统</span>
      </div>
      <el-menu
        class="app-menu"
        :default-active="activeMenu"
        router
        background-color="#2f4050"
        text-color="#a7b1c2"
        active-text-color="#ffffff"
      >
        <el-menu-item :class="{ active: isMenuActive('/dashboard') }" index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>系统概览</span>
        </el-menu-item>
        <el-menu-item v-if="isStudent" :class="{ active: isMenuActive('/student-home') }" index="/student-home">
          <el-icon><Collection /></el-icon>
          <span>我的项目</span>
        </el-menu-item>
        <el-menu-item v-if="isSuperAdmin || isTeacher" :class="{ active: isMenuActive('/training') }" index="/training">
          <el-icon><Notebook /></el-icon>
          <span>实训管理</span>
        </el-menu-item>
        <el-menu-item v-if="isSuperAdmin" :class="{ active: isMenuActive('/llm-config') }" index="/llm-config">
          <el-icon><Setting /></el-icon>
          <span>大模型配置</span>
        </el-menu-item>
        <el-menu-item v-if="isSuperAdmin || isTeacher" :class="{ active: isMenuActive('/evaluation-templates') }" index="/evaluation-templates">
          <el-icon><Collection /></el-icon>
          <span>评价规则配置</span>
        </el-menu-item>
        <el-menu-item v-if="isSuperAdmin" :class="{ active: isMenuActive('/admin/users') }" index="/admin/users">
          <el-icon><UserFilled /></el-icon>
          <span>账号权限管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="pageTitle">{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <span class="header-tip">{{ currentUser.display_name || '未登录用户' }} · {{ roleLabel }}</span>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentUser = ref(getCurrentUser())

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch (e) {
    return {}
  }
}

const isStudent = computed(() => currentUser.value.role === 'student')
const isSuperAdmin = computed(() => currentUser.value.role === 'super_admin')
const isTeacher = computed(() => currentUser.value.role === 'teacher')
const roleLabel = computed(() => {
  if (currentUser.value.role === 'super_admin') return '超级管理员'
  if (currentUser.value.role === 'admin') return '管理员'
  if (currentUser.value.role === 'teacher') return '教师'
  if (currentUser.value.role === 'student') return '学生'
  return '访客'
})
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/admin')) {
    return '/admin/users'
  }
  if (path.startsWith('/evaluation-templates')) {
    return '/evaluation-templates'
  }

  if (path.startsWith('/training') || path.startsWith('/submission') ||
      path.startsWith('/evaluation') || path.startsWith('/report')) {
    return '/training'
  }
  if (path.startsWith('/student-home')) {
    return '/student-home'
  }
  return path
})
const pageTitle = computed(() => route.meta?.title || '')
const isMenuActive = (index) => activeMenu.value === index
</script>

<style>
:root {
  --primary: #0052D9;
  --primary-hover: #1890FF;
  --primary-light: #E6F7FF;
  --success: #52C41A;
  --warning: #FAAD14;
  --danger: #FF4D4F;
  --bg-page: #F2F4F7;
  --bg-card: #FFFFFF;
  --border-light: #E5E6EB;
  --text-title: #1D2129;
  --text-body: #4E5969;
  --text-muted: #86909C;
  --shadow-soft: 0 2px 12px rgba(0, 0, 0, 0.06);
  --shadow-hover: 0 4px 20px rgba(0, 0, 0, 0.08);
  --radius: 8px;
  --topbar-height: 64px;
  --sidebar-width: 240px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { min-height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg-page);
  color: var(--text-body);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.app-container { min-height: 100vh; background: var(--bg-page); }
.app-sidebar {
  background: #2f4050;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  overflow-y: auto;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.12);
}
.app-sidebar .logo {
  height: var(--topbar-height); display: flex; align-items: center; justify-content: center;
  color: #ffffff; font-size: 18px; font-weight: 600; gap: 10px;
  background: #293846;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.app-sidebar .logo .el-icon { color: #1c84c6; }
.app-header {
  background: #a7b1c2; display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border-light); padding: 0 24px; height: var(--topbar-height);
}
.header-left .el-breadcrumb__inner,
.header-left .el-breadcrumb__separator { color: var(--text-muted); }
.header-left .el-breadcrumb__inner.is-link:hover { color: var(--primary-hover); }
.header-right .header-tip { color: var(--text-muted); font-size: 13px; }
.app-main {
  background: linear-gradient(180deg, #F7F9FC 0%, var(--bg-page) 100%);
  min-height: calc(100vh - var(--topbar-height));
  padding: 24px;
}
.app-menu {
  border-right: none !important;
  padding: 8px 0 10px;
  background: #2f4050 !important;
}
.app-menu .el-menu-item {
  margin: 4px 8px;
  height: 44px;
  line-height: 44px;
  border-radius: 0 6px 6px 0;
  font-size: 14px;
  color: #a7b1c2;
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
  border-left: 4px solid transparent;
  background: transparent;
}
.app-menu .el-menu-item .el-icon { color: #a7b1c2; }
.app-menu .el-menu-item:hover {
  background: #293846 !important;
  color: #ffffff !important;
}
.app-menu .el-menu-item:hover .el-icon { color: #ffffff; }
.app-menu .el-menu-item.active,
.app-menu .el-menu-item.is-active {
  background: #1c84c6 !important;
  color: #ffffff !important;
  border-left-color: #1c84c6;
}
.app-menu .el-menu-item.active .el-icon,
.app-menu .el-menu-item.is-active .el-icon { color: #ffffff; }
.app-menu .el-menu-item.active:hover,
.app-menu .el-menu-item.is-active:hover {
  background: #1c84c6 !important;
}
.app-menu .el-menu-item.active::before,
.app-menu .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background: #1c84c6;
}
.app-menu .el-sub-menu__title {
  margin: 4px 8px;
  height: 44px;
  line-height: 44px;
  border-radius: 0 6px 6px 0;
  border-left: 4px solid transparent;
  color: #a7b1c2;
  background: transparent !important;
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}
.app-menu .el-sub-menu__title:hover {
  color: #ffffff;
  background: #293846 !important;
}
.app-menu .el-sub-menu.is-active > .el-sub-menu__title,
.app-menu .el-sub-menu.active > .el-sub-menu__title {
  color: #ffffff;
  background: #1c84c6 !important;
  border-left-color: #1c84c6;
}
.app-menu .el-sub-menu__icon-arrow {
  color: #a7b1c2;
  transition: transform 0.2s ease;
}
.app-menu .el-sub-menu.is-opened > .el-sub-menu__title .el-sub-menu__icon-arrow {
  transform: rotate(90deg);
}
.app-menu .el-sub-menu .el-menu {
  background: #293846 !important;
}
.app-menu .el-sub-menu .el-menu-item {
  margin: 2px 8px 2px 24px;
  padding-left: 32px !important;
  height: 40px;
  line-height: 40px;
  border-radius: 0 6px 6px 0;
  font-size: 13px;
  color: #a7b1c2;
  border-left: 4px solid transparent;
}
.app-menu .el-sub-menu .el-menu-item:hover,
.app-menu .el-sub-menu .el-menu-item.active,
.app-menu .el-sub-menu .el-menu-item.is-active {
  background: #1c84c6 !important;
  color: #ffffff !important;
  border-left-color: #1c84c6;
}
.app-menu .el-sub-menu .el-menu-item:hover .el-icon,
.app-menu .el-sub-menu .el-menu-item.active .el-icon,
.app-menu .el-sub-menu .el-menu-item.is-active .el-icon {
  color: #ffffff;
}
.app-menu .el-sub-menu .el-menu-item.active::before,
.app-menu .el-sub-menu .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background: #1c84c6;
}
.app-main .el-card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  box-shadow: var(--shadow-soft);
  transition: all 0.25s ease;
  overflow: hidden;
}
.app-main .el-card:hover { box-shadow: var(--shadow-hover); }
.app-main .el-card__header {
  padding: 16px 20px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-title);
  border-bottom: 1px solid var(--border-light);
}
.app-main .el-card__body { padding: 20px 24px; }
.app-main .el-button--primary {
  background: var(--primary);
  border-color: var(--primary);
  transition: all 0.25s ease;
  box-shadow: none;
}
.app-main .el-button--primary:hover,
.app-main .el-button--primary:focus {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
  box-shadow: 0 4px 12px rgba(0, 82, 217, 0.25);
}
.app-main .el-button.is-link { color: var(--primary); }
.app-main .el-button.is-link:hover { color: var(--primary-hover); }
.app-main .el-tag {
  border-radius: 12px;
  font-weight: 500;
}
.app-main .el-tag--success { background: #f6ffed; color: var(--success); border-color: #b7eb8f; }
.app-main .el-tag--warning { background: #fffbe6; color: var(--warning); border-color: #ffe58f; }
.app-main .el-tag--danger { background: #fff2f0; color: var(--danger); border-color: #ffccc7; }
.app-main .el-tag--info { background: #f5f7fa; color: var(--text-muted); border-color: var(--border-light); }
.app-main .el-tag--primary { background: var(--primary-light); color: var(--primary); border-color: #bae0ff; }
.app-main .el-input__wrapper,
.app-main .el-textarea__inner,
.app-main .el-select__wrapper,
.app-main .el-input-number__decrease,
.app-main .el-input-number__increase {
  border-radius: var(--radius);
  box-shadow: none;
}
.app-main .el-input__wrapper.is-focus,
.app-main .el-textarea__inner:focus,
.app-main .el-select__wrapper.is-focused {
  box-shadow: 0 0 0 3px rgba(0, 82, 217, 0.1);
}
.app-main .el-input__wrapper,
.app-main .el-textarea__inner,
.app-main .el-select__wrapper {
  border: 1px solid var(--border-light);
}
.app-main .el-table {
  --el-table-border-color: var(--border-light);
  --el-table-header-bg-color: var(--bg-page);
  --el-table-header-text-color: var(--text-muted);
  --el-table-text-color: var(--text-body);
  --el-table-row-hover-bg-color: var(--primary-light);
}
.app-main .el-table th.el-table__cell {
  background: var(--bg-page) !important;
  color: var(--text-muted);
  font-weight: 600;
}
.app-main .el-table .cell { padding-left: 16px; padding-right: 16px; }
.app-main .el-table tr:hover > td.el-table__cell { background: var(--primary-light) !important; }
.app-main .el-dialog {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(29, 33, 41, 0.18);
}
.app-main .el-dialog__header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-light);
}
.app-main .el-dialog__body { padding: 24px; }
.app-main .el-dialog__footer { padding: 0 24px 24px; }
.app-main .el-form-item__label {
  color: var(--text-body);
  font-weight: 500;
}
.app-main .el-divider__text { color: var(--text-muted); }
.app-main .page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.app-main .page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-title) !important;
  line-height: 1.3;
}
.app-main .page-header p {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-muted) !important;
}
.app-main .page-header > div:first-child {
  min-width: 0;
}
.app-main .stat-value,
.app-main .summary-value,
.app-main .overview-value,
.app-main .score-value {
  color: var(--text-title) !important;
  font-weight: 700;
  line-height: 1.2;
}
.app-main .stat-label,
.app-main .summary-label,
.app-main .overview-label,
.app-main .score-label,
.app-main .empty-hint,
.app-main .no-data,
.app-main .muted,
.app-main .hint,
.app-main .form-tip,
.app-main .test-response,
.app-main .deploy-tips,
.app-main .json-view {
  color: var(--text-muted);
}
.app-main .stat-card .stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}
.app-main .stat-card .stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 6px 14px rgba(0, 82, 217, 0.18);
}
.app-main .stat-label,
.app-main .summary-label,
.app-main .overview-label,
.app-main .score-label {
  margin-top: 4px;
  font-size: 13px;
  font-weight: 400;
}
.app-main .stat-value,
.app-main .summary-value,
.app-main .overview-value {
  font-size: 28px;
}
.app-main .score-value { font-size: 28px; }
.app-main .summary-card,
.app-main .overview-item,
.app-main .score-item,
.app-main .json-view,
.app-main .empty-hint,
.app-main .no-data {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
}
.app-main .overview-item,
.app-main .score-item {
  text-align: center;
  padding: 16px;
}
.app-main .score-item {
  background: linear-gradient(180deg, #F7F9FC 0%, #FFFFFF 100%);
}
.app-main .score-item.final {
  background: var(--primary-light);
}
.app-main .json-view {
  padding: 12px;
  font-size: 12px;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
}
.app-main .empty-hint,
.app-main .no-data {
  text-align: center;
  padding: 30px 20px;
}
.app-main .toolbar,
.app-main .card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.app-main .toolbar-left {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.app-main .summary-row,
.app-main .stats-row,
.app-main .chart-row,
.app-main .report-content,
.app-main .section-card,
.app-main .panel-card,
.app-main .info-card,
.app-main .submission-card,
.app-main .teacher-card,
.app-main .files-card {
  margin-bottom: 16px;
}
</style>

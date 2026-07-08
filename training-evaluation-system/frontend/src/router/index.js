import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', meta: { title: '系统概览' }, component: () => import('../views/Dashboard.vue') },
  { path: '/training', name: 'TrainingList', meta: { title: '实训管理' }, component: () => import('../views/TrainingList.vue') },
  { path: '/student-home', name: 'StudentHome', meta: { title: '我的项目' }, component: () => import('../views/StudentHome.vue') },
  { path: '/training/:id', name: 'TrainingDetail', meta: { title: '实训详情' }, component: () => import('../views/TrainingDetail.vue') },
  { path: '/evaluation/:trainingId', name: 'EvaluationConfig', meta: { title: '评价配置' }, component: () => import('../views/EvaluationConfig.vue') },
  { path: '/submission/:id', name: 'SubmissionDetail', meta: { title: '提交详情' }, component: () => import('../views/SubmissionDetail.vue') },
  { path: '/report/:trainingId', name: 'ReportView', meta: { title: '评价报告' }, component: () => import('../views/ReportView.vue') },
  { path: '/evaluation-templates', name: 'EvaluationTemplates', meta: { title: '评价模板管理' }, component: () => import('../views/EvaluationTemplates.vue') },
  { path: '/admin/users', name: 'UserManagement', meta: { title: '账号权限管理' }, component: () => import('../views/UserManagement.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

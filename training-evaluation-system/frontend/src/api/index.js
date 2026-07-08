import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

api.interceptors.request.use((config) => {
  try {
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
    config.headers = config.headers || {}
    if (currentUser.id) config.headers['X-User-Id'] = currentUser.id
    if (currentUser.role) config.headers['X-User-Role'] = currentUser.role
    if (currentUser.account_type) {
      config.headers['X-User-Type'] = currentUser.account_type
      config.headers['X-Account-Type'] = currentUser.account_type
    }
    if (currentUser.username) config.headers['X-User-Name'] = currentUser.username
    if (currentUser.display_name) config.headers['X-User-Display-Name'] = currentUser.display_name
  } catch (e) {
    // ignore malformed localStorage payloads
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export const trainingAPI = {
  list: () => api.get('/training/list'),
  myProjects: () => api.get('/training/my-projects'),
  mySubmissions: () => api.get('/training/my-submissions'),
  get: (id) => api.get(`/training/${id}`),
  create: (data) => api.post('/training/create', data),
  update: (id, data) => api.put(`/training/${id}`, data),
  delete: (id) => api.delete(`/training/${id}`),
  submissions: (id) => api.get(`/training/${id}/submissions`),
  submit: (id, formData) => api.post(`/training/${id}/submit`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getSubmission: (id) => api.get(`/training/submission/${id}`),
  deleteSubmission: (id) => api.delete(`/training/submission/${id}`),
}

export const evaluationAPI = {
  indicators: (trainingId) => api.get(`/evaluation/indicators/${trainingId}`),
  templates: () => api.get('/evaluation/templates'),
  createTemplate: (data) => api.post('/evaluation/templates', data),
  updateTemplate: (id, data) => api.put(`/evaluation/templates/${id}`, data),
  deleteTemplate: (id) => api.delete(`/evaluation/templates/${id}`),
  assignTemplate: (id, data) => api.post(`/evaluation/templates/${id}/assign`, data),
  templateAssignments: (id) => api.get(`/evaluation/templates/${id}/assignments`),
  createIndicator: (data) => api.post('/evaluation/indicators', data),
  updateIndicator: (id, data) => api.put(`/evaluation/indicators/${id}`, data),
  deleteIndicator: (id) => api.delete(`/evaluation/indicators/${id}`),
  evaluate: (submissionId) => api.post(`/evaluation/evaluate/${submissionId}`),
  batchEvaluate: (trainingId) => api.post(`/evaluation/batch-evaluate/${trainingId}`),
  teacherReview: (submissionId, data) => api.post(`/evaluation/teacher-review/${submissionId}`, data),
  reparse: (submissionId) => api.post(`/evaluation/reparse/${submissionId}`),
}

export const reportAPI = {
  stats: () => api.get('/report/stats'),
  getReportData: (trainingId) => api.get(`/report/training/${trainingId}/data`),
  generate: (trainingId) => api.post(`/report/generate/${trainingId}`),
  list: (trainingId) => api.get(`/report/list/${trainingId}`),
  downloadPdf: (reportId) => api.get(`/report/download/${reportId}/pdf`, { responseType: 'blob' }),
  downloadExcel: (reportId) => api.get(`/report/download/${reportId}/excel`, { responseType: 'blob' }),
  deleteReport: (reportId) => api.delete(`/report/${reportId}`),
  getStudentReport: (submissionId) => api.get(`/report/student/${submissionId}`),
  getCommonProblems: (trainingId) => api.get(`/report/training/${trainingId}/common-problems`),
  getAbnormalStudents: (trainingId, params) => api.post(`/report/training/${trainingId}/abnormal-students`, params),
  generateSingleStudent: (submissionId) => api.post(`/report/generate/student/${submissionId}`),
  batchGenerate: (trainingId) => api.post(`/report/batch-generate/${trainingId}`),
  exportProblems: (trainingId) => api.get(`/report/training/${trainingId}/export-problems`, { responseType: 'blob' }),
}

export const llmAPI = {
  getConfig: () => api.get('/llm/config'),
  updateConfig: (data) => api.put('/llm/config', data),
  test: (prompt) => api.post('/llm/test', { prompt }),
}

export const systemAPI = {
  getConfig: () => api.get('/system/config'),
  updateConfig: (data) => api.put('/system/config', data),
}

export const adminAPI = {
  classStats: () => api.get('/admin/class-stats'),
  logs: () => api.get('/admin/logs'),
  backup: () => api.get('/admin/backup', { responseType: 'blob' }),
}

export const modifyAPI = {
  modifySubmission: (data) => api.post('/modify/submission', data),
  getSpecs: () => api.get('/modify/specs'),
  getCategories: () => api.get('/modify/categories'),
  rebuildIndex: () => api.post('/modify/rebuild-index'),
}

export const knowledgeAPI = {
  getGraph: () => api.get('/knowledge/graph'),
  getPoints: (params) => api.get('/knowledge/points', { params }),
  getPrerequisites: (name) => api.get('/knowledge/prerequisites', { params: { name } }),
  analyzeWeakness: (content) => api.post('/knowledge/analyze', { content }),
}

export const recommendAPI = {
  recommendCourses: (weakPoints, topK) => api.post('/recommend/courses', {
    weak_points: weakPoints,
    top_k: topK || 5,
  }),
  analyzeAndRecommend: (content, topK) => api.post('/recommend/analyze-and-recommend', {
    content,
    top_k: topK || 5,
  }),
}

export const usersAPI = {
  list: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id, accountType) => api.delete(`/users/${id}`, {
    headers: accountType ? { 'X-Account-Type': accountType } : {},
  }),
}

export default api
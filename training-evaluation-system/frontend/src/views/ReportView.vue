<template>
  <div class="report-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2>AI评阅报告</h2>
        <p>AI自动完成全班级实训评阅，集中展示智能评价结果，减少重复批改工作</p>
      </div>
      <el-button type="primary" @click="openAbnormalDrawer">
        <el-icon><Warning /></el-icon> 异常学生清单
      </el-button>
    </div>

    <!-- 顶部统计卡 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="8" v-for="stat in topStats" :key="stat.label">
        <el-card class="stat-card" shadow="hover" :class="{ clickable: stat.clickable }" @click="handleStatClick(stat)">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选工具栏 -->
    <el-card class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索学生姓名/学号"
            clearable
            :prefix-icon="Search"
            style="width: 220px"
          />
          <el-select v-model="selectedTraining" placeholder="实训任务" style="width: 200px" disabled>
            <el-option :label="reportData?.training?.title" :value="reportData?.training?.id" />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" @click="handleBatchExport('pdf')" :loading="batchExporting.pdf">
            <el-icon><Document /></el-icon> 批量导出全部PDF
          </el-button>
          <el-button type="success" @click="handleBatchExport('excel')" :loading="batchExporting.excel">
            <el-icon><Download /></el-icon> 批量导出全部Excel
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 主内容区 -->
    <el-row :gutter="16" class="main-content">
      <!-- 左侧表格 -->
      <el-col :span="15">
        <el-card class="table-card" v-loading="loading">
          <el-table
            :data="filteredSubmissions"
            stripe
            highlight-current-row
            max-height="calc(100vh - 340px)"
            style="width: 100%"
            @row-click="handleRowClick"
          >
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="student_id" label="学号" width="110" />
            <el-table-column prop="student_name" label="姓名" width="90" />
            <el-table-column prop="final_score" label="总分" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="scoreType(row.final_score)" size="small">{{ row.final_score ?? '-' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="逻辑结构" width="90" align="center">
              <template #default="{ row }">{{ row.dimension_scores?.['逻辑结构'] ?? '-' }}</template>
            </el-table-column>
            <el-table-column label="代码规范" width="90" align="center">
              <template #default="{ row }">{{ row.dimension_scores?.['代码规范'] ?? '-' }}</template>
            </el-table-column>
            <el-table-column label="功能实现" width="90" align="center">
              <template #default="{ row }">{{ row.dimension_scores?.['功能实现'] ?? '-' }}</template>
            </el-table-column>
            <el-table-column label="批注" width="70" align="center">
              <template #default="{ row }">{{ row.annotation_count ?? '-' }}</template>
            </el-table-column>
            <el-table-column label="AI评阅状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'evaluated' ? 'success' : 'info'" size="small">{{ row.ai_review_status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="文档状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.document_status === '已提交' ? 'primary' : 'info'" size="small">{{ row.document_status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click.stop="viewStudentReport(row)">查看报告</el-button>
                <el-button link type="success" size="small" @click.stop="generateStudentReport(row)">导出PDF</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧面板 -->
      <el-col :span="9">
        <div class="right-panel" v-loading="studentLoading">
          <!-- 单学生报告 -->
          <el-card class="student-report-card">
            <div class="report-header">
              <div>
                <h3>单学生完整AI评价报告</h3>
                <p class="report-subtitle">
                  {{ selectedStudentReport?.submission?.student_name || '请选择学生' }}
                  <template v-if="selectedStudentReport?.submission?.student_id">
                    | {{ selectedStudentReport.submission.student_id }}
                  </template>
                  <template v-if="selectedStudentReport?.training?.title">
                    | {{ selectedStudentReport.training.title }}
                  </template>
                </p>
              </div>
              <el-button type="primary" size="small" :disabled="!selectedStudentReport" @click="openReviewModalForCurrent">
                <el-icon><EditPen /></el-icon> 人工复核
              </el-button>
            </div>

            <div v-if="selectedStudentReport" class="score-overview">
              <div class="score-ring">
                <svg viewBox="0 0 120 120" class="ring-svg">
                  <circle cx="60" cy="60" r="52" fill="none" stroke="#E5E6EB" stroke-width="10" />
                  <circle
                    cx="60" cy="60" r="52"
                    fill="none"
                    :stroke="scoreRingColor"
                    stroke-width="10"
                    stroke-linecap="round"
                    :stroke-dasharray="circumference"
                    :stroke-dashoffset="scoreOffset"
                    transform="rotate(-90 60 60)"
                  />
                </svg>
                <div class="score-text">
                  <div class="score-number">{{ selectedStudentReport.scores.final_score ?? '-' }}</div>
                  <div class="score-unit">分</div>
                </div>
              </div>

              <div class="dimension-bars">
                <div v-for="dim in studentDimensions" :key="dim.name" class="dimension-bar-item">
                  <div class="dimension-bar-header">
                    <span>{{ dim.name }}</span>
                    <span class="dimension-bar-score">{{ dim.score }}</span>
                  </div>
                  <el-progress :percentage="dim.percentage" :color="dim.color" :show-text="false" :stroke-width="8" />
                </div>
              </div>
            </div>

            <div v-if="selectedStudentReport" class="ai-comment-box">
              <h4>AI综合评语</h4>
              <p>{{ selectedStudentReport.scores.overall_comment || '暂无AI综合评语' }}</p>
            </div>

            <div v-if="selectedStudentReport" class="follow-up-box">
              <h4>班级添加跟进备注</h4>
              <el-input
                v-model="currentFollowUpNote"
                type="textarea"
                :rows="2"
                placeholder="输入跟进备注，修改记录将同步存入学生成长档案..."
              />
              <div class="follow-up-actions">
                <el-button type="primary" size="small" :loading="savingNote" @click="saveFollowUpNoteForCurrent">
                  保存复核记录
                </el-button>
              </div>
            </div>

            <div v-if="selectedStudentReport" class="code-annotations-box">
              <h4>代码逐段批注</h4>
              <div v-for="(annotation, index) in selectedStudentReport.code_annotations" :key="index" class="annotation-item" :class="annotation.type">
                <div class="annotation-title">
                  <el-icon v-if="annotation.type === 'error'" class="annotation-icon error-icon"><CircleClose /></el-icon>
                  <el-icon v-else-if="annotation.type === 'warning'" class="annotation-icon warning-icon"><Warning /></el-icon>
                  <el-icon v-else class="annotation-icon suggestion-icon"><InfoFilled /></el-icon>
                  错误点：第{{ annotation.line_number }}行{{ annotationTypeLabel(annotation.type) }}
                </div>
                <div class="annotation-content">{{ annotation.message }}</div>
                <div v-if="annotation.suggestion" class="annotation-suggestion">
                  <strong>修改建议：</strong>{{ annotation.suggestion }}
                </div>
              </div>
              <div v-if="!selectedStudentReport.code_annotations.length" class="empty-hint">暂无代码批注</div>
            </div>

            <el-empty v-if="!selectedStudentReport" description="请从左侧表格选择学生查看详细报告" />
          </el-card>

          <!-- 班级共性问题汇总 -->
          <el-card class="common-problems-card">
            <div class="card-title">班级共性问题汇总</div>
            <div v-if="commonProblems.length > 0" class="problem-list">
              <div v-for="problem in commonProblems.slice(0, 5)" :key="problem.keyword" class="problem-item">
                <div class="problem-info">
                  <span class="problem-name">{{ problem.keyword }}</span>
                  <span class="problem-count">{{ problem.student_count }}人</span>
                </div>
                <el-progress :percentage="Math.min(problem.student_count * 10, 100)" :show-text="false" :stroke-width="6" :color="problemColor(problem)" />
              </div>
            </div>
            <div v-else class="empty-hint">暂无共性问题数据</div>
            <div class="problem-actions">
              <el-button type="primary" size="small" @click="exportProblems">
                <el-icon><Download /></el-icon> 导出课堂讲解汇总
              </el-button>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>

    <!-- 人工复核弹窗 -->
    <el-dialog v-model="reviewDialogVisible" title="人工复核" width="600px">
      <el-form :model="reviewForm" label-width="90px" size="small">
        <el-form-item label="AI评分">
          <el-input :model-value="reviewForm.ai_score" disabled />
        </el-form-item>
        <el-form-item label="教师评分">
          <el-input-number v-model="reviewForm.teacher_score" :min="0" :max="100" :step="0.5" style="width: 180px" />
        </el-form-item>
        <el-form-item label="复核备注">
          <el-input v-model="reviewForm.teacher_comment" type="textarea" :rows="4" placeholder="输入教师评语，将同步存入学生成长档案..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReview" :loading="submittingReview">提交复核</el-button>
      </template>
    </el-dialog>

    <!-- 异常学生抽屉 -->
    <el-drawer v-model="abnormalDrawerVisible" title="异常学生重点关注清单" size="720px">
      <div class="abnormal-toolbar">
        <span class="threshold-label">预警阈值：</span>
        <el-input-number v-model="warningThreshold" :min="0" :max="100" :step="5" @change="loadAbnormalStudents" />
        <span class="threshold-unit">分以下</span>
      </div>
      <el-table :data="abnormalStudents" stripe max-height="calc(100vh - 240px)" style="width: 100%">
        <el-table-column prop="student_name" label="姓名" width="100" />
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="final_score" label="最终得分" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="danger">{{ row.final_score }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ai_total_score" label="AI评分" width="90" align="center" />
        <el-table-column prop="follow_note" label="跟进备注" min-width="160">
          <template #default="{ row }">
            <el-input v-model="row.follow_up_note" size="small" @blur="saveFollowUpNote(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewStudentReport({ id: row.id }); abnormalDrawerVisible = false">查看报告</el-button>
            <el-button size="small" type="warning" @click="openReviewModal({ id: row.id, ai_total_score: row.ai_total_score, teacher_score: row.teacher_score, teacher_comment: row.teacher_comment || row.follow_note })">复核</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { reportAPI, evaluationAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const route = useRoute()
const trainingId = computed(() => Number(route.params.trainingId))

const loading = ref(false)
const studentLoading = ref(false)
const reportData = ref(null)
const commonProblems = ref([])
const abnormalStudents = ref([])
const selectedStudentReport = ref(null)
const searchQuery = ref('')
const selectedTraining = ref(null)
const currentFollowUpNote = ref('')
const savingNote = ref(false)
const warningThreshold = ref(60)
const abnormalDrawerVisible = ref(false)

const batchExporting = ref({ pdf: false, excel: false })

const reviewDialogVisible = ref(false)
const reviewForm = ref({ submissionId: null, ai_score: null, teacher_score: null, teacher_comment: '' })
const submittingReview = ref(false)

const circumference = 2 * Math.PI * 52

const topStats = computed(() => {
  const stats = reportData.value?.statistics
  if (!stats) return []
  return [
    { label: '已评价', value: stats.evaluated_count || 0, color: '#52C41A', icon: 'CircleCheck', clickable: false },
    { label: '已自动评阅', value: stats.ai_evaluated_count || 0, color: '#1890FF', icon: 'Cpu', clickable: false },
    { label: '待人工复核', value: stats.pending_manual_review_count || 0, color: '#FAAD14', icon: 'User', clickable: true, onClick: openAbnormalDrawer }
  ]
})

const filteredSubmissions = computed(() => {
  const list = reportData.value?.submissions || []
  if (!searchQuery.value.trim()) return list
  const q = searchQuery.value.trim().toLowerCase()
  return list.filter(s =>
    (s.student_name && s.student_name.toLowerCase().includes(q)) ||
    (s.student_id && s.student_id.toLowerCase().includes(q))
  )
})

const scoreRingColor = computed(() => {
  const score = selectedStudentReport.value?.scores?.final_score
  if (!score && score !== 0) return '#909399'
  if (score >= 90) return '#52C41A'
  if (score >= 70) return '#1890FF'
  return '#FF4D4F'
})

const scoreOffset = computed(() => {
  const score = selectedStudentReport.value?.scores?.final_score || 0
  return circumference - (Math.min(score, 100) / 100) * circumference
})

const studentDimensions = computed(() => {
  const scores = selectedStudentReport.value?.scores?.indicator_scores || []
  const dims = []
  const names = ['逻辑结构', '代码规范', '功能实现']
  const colors = ['#1890FF', '#52C41A', '#FAAD14']
  for (let i = 0; i < names.length; i++) {
    const name = names[i]
    const item = scores.find(s => s.name && s.name.includes(name))
    const score = item ? item.score : null
    const max = item ? (item.max_score || 100) : 100
    dims.push({
      name,
      score: score ?? '-',
      percentage: score !== null ? Math.round((score / max) * 100) : 0,
      color: colors[i]
    })
  }
  return dims
})

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const scoreType = (score) => {
  if (!score && score !== 0) return 'info'
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}

const annotationTypeLabel = (type) => ({ error: '错误', warning: '警告', suggestion: '建议' }[type] || '')

const problemColor = (problem) => {
  if (problem.severity === 'high') return '#FF4D4F'
  if (problem.severity === 'medium') return '#FAAD14'
  return '#1890FF'
}

const loadData = async () => {
  loading.value = true
  try {
    const [dataRes, problemsRes] = await Promise.all([
      reportAPI.getReportData(trainingId.value),
      reportAPI.getCommonProblems(trainingId.value)
    ])
    reportData.value = dataRes.data
    commonProblems.value = problemsRes.data
    selectedTraining.value = dataRes.data.training.id
    if (dataRes.data.submissions.length > 0 && !selectedStudentReport.value) {
      await viewStudentReport(dataRes.data.submissions[0])
    }
    await loadAbnormalStudents()
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

const loadAbnormalStudents = async () => {
  try {
    const { data } = await reportAPI.getAbnormalStudents(trainingId.value, { threshold: warningThreshold.value })
    abnormalStudents.value = data.map(s => ({ ...s, follow_up_note: s.follow_note || '' }))
  } catch (e) {
    // handled by interceptor
  }
}

const handleRowClick = (row) => {
  viewStudentReport(row)
}

const viewStudentReport = async (row) => {
  if (!row || !row.id) return
  studentLoading.value = true
  try {
    const { data } = await reportAPI.getStudentReport(row.id)
    selectedStudentReport.value = data
    currentFollowUpNote.value = data.follow_up_note || ''
  } catch (e) {
    ElMessage.error('获取学生报告失败')
  } finally {
    studentLoading.value = false
  }
}

const generateStudentReport = async (row) => {
  try {
    await reportAPI.generateSingleStudent(row.id)
    ElMessage.success('报告生成成功')
    loadData()
  } catch (e) {
    ElMessage.error('生成报告失败')
  }
}

const openReviewModal = async (row) => {
  reviewForm.value = {
    submissionId: row.id,
    ai_score: row.ai_total_score,
    teacher_score: row.teacher_score,
    teacher_comment: row.teacher_comment || ''
  }
  reviewDialogVisible.value = true
}

const openReviewModalForCurrent = () => {
  if (!selectedStudentReport.value) return
  const sub = selectedStudentReport.value.submission
  const scores = selectedStudentReport.value.scores
  openReviewModal({
    id: sub.id,
    ai_total_score: scores.ai_total_score,
    teacher_score: scores.teacher_score,
    teacher_comment: selectedStudentReport.value.teacher_comment
  })
}

const submitReview = async () => {
  submittingReview.value = true
  try {
    await evaluationAPI.teacherReview(reviewForm.value.submissionId, {
      teacher_score: reviewForm.value.teacher_score,
      teacher_comment: reviewForm.value.teacher_comment
    })
    ElMessage.success('复核提交成功，已同步存入学生成长档案')
    reviewDialogVisible.value = false
    loadData()
    if (selectedStudentReport.value && selectedStudentReport.value.submission.id === reviewForm.value.submissionId) {
      await viewStudentReport({ id: reviewForm.value.submissionId })
    }
  } catch (e) {
    ElMessage.error('提交失败')
  } finally {
    submittingReview.value = false
  }
}

const saveFollowUpNoteForCurrent = async () => {
  if (!selectedStudentReport.value) return
  savingNote.value = true
  try {
    await evaluationAPI.teacherReview(selectedStudentReport.value.submission.id, {
      teacher_comment: currentFollowUpNote.value
    })
    ElMessage.success('跟进备注已保存')
    loadData()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingNote.value = false
  }
}

const saveFollowUpNote = async (row) => {
  try {
    await evaluationAPI.teacherReview(row.id, { teacher_comment: row.follow_up_note })
    ElMessage.success('备注已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const handleBatchExport = async (type) => {
  try {
    await ElMessageBox.confirm(`确定批量导出全班${type === 'pdf' ? 'PDF' : 'Excel'}报告吗？`, '确认批量导出', { type: 'warning' })
    batchExporting.value[type] = true
    if (type === 'pdf') {
      await reportAPI.batchGenerate(trainingId.value)
    } else {
      const { data } = await reportAPI.getReportData(trainingId.value)
      const csvContent = generateClassCsv(data)
      downloadBlob(csvContent, `${data.training.title}_全班成绩汇总.csv`, 'text/csv')
    }
    ElMessage.success('批量导出完成')
  } catch (e) {
    // cancelled or error
  } finally {
    batchExporting.value[type] = false
  }
}

const generateClassCsv = (data) => {
  const headers = ['学号', '姓名', 'AI评分', '教师评分', '最终评分', 'AI评阅状态', '文档状态']
  const rows = data.submissions.map(s => [
    s.student_id || '', s.student_name || '', s.ai_total_score ?? '', s.teacher_score ?? '', s.final_score ?? '',
    s.ai_review_status || '', s.document_status || ''
  ].join(','))
  return '\uFEFF' + [headers.join(','), ...rows].join('\n')
}

const downloadBlob = (content, filename, mimeType) => {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const exportProblems = async () => {
  try {
    const { data } = await reportAPI.exportProblems(trainingId.value)
    const blob = new Blob([data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `共性问题汇总.csv`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

const openAbnormalDrawer = () => {
  abnormalDrawerVisible.value = true
}

const handleStatClick = (stat) => {
  if (stat.clickable && typeof stat.onClick === 'function') {
    stat.onClick()
  }
}

watch(trainingId, () => {
  selectedStudentReport.value = null
  loadData()
})

onMounted(loadData)
</script>

<style scoped>
.report-view {
  padding-bottom: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0 0 6px 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-title);
}
.page-header p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}

.stats-row {
  margin-bottom: 16px;
}
.stat-card {
  cursor: default;
}
.stat-card.clickable {
  cursor: pointer;
}
.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.12);
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-title);
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

.toolbar-card {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  align-items: stretch;
}
.table-card {
  height: 100%;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.report-header h3 {
  margin: 0 0 6px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-title);
}
.report-subtitle {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}

.score-overview {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 100%);
  border-radius: 8px;
  border: 1px solid var(--border-light);
}
.score-ring {
  position: relative;
  width: 140px;
  height: 140px;
  flex-shrink: 0;
}
.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.score-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.score-number {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-title);
  line-height: 1;
}
.score-unit {
  font-size: 12px;
  color: var(--text-muted);
}
.dimension-bars {
  flex: 1;
}
.dimension-bar-item {
  margin-bottom: 12px;
}
.dimension-bar-item:last-child {
  margin-bottom: 0;
}
.dimension-bar-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-body);
  margin-bottom: 6px;
}
.dimension-bar-score {
  font-weight: 600;
  color: var(--text-title);
}

.ai-comment-box,
.follow-up-box,
.code-annotations-box {
  margin-bottom: 20px;
}
.ai-comment-box h4,
.follow-up-box h4,
.code-annotations-box h4,
.common-problems-card .card-title {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-title);
}
.ai-comment-box p {
  margin: 0;
  padding: 12px;
  background: #e6f7ff;
  border-left: 4px solid #1890ff;
  border-radius: 0 8px 8px 0;
  font-size: 13px;
  color: var(--text-body);
  line-height: 1.7;
}

.follow-up-actions {
  margin-top: 10px;
  text-align: right;
}

.annotation-item {
  margin-bottom: 12px;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
}
.annotation-item.error {
  background: #fff2f0;
  border-left: 4px solid #ff4d4f;
}
.annotation-item.warning {
  background: #fffbe6;
  border-left: 4px solid #faad14;
}
.annotation-item.suggestion {
  background: #e6f7ff;
  border-left: 4px solid #1890ff;
}
.annotation-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 6px;
}
.annotation-icon {
  font-size: 14px;
}
.error-icon {
  color: #ff4d4f;
}
.warning-icon {
  color: #faad14;
}
.suggestion-icon {
  color: #1890ff;
}
.annotation-content {
  color: var(--text-body);
  line-height: 1.6;
  margin-bottom: 6px;
}
.annotation-suggestion {
  color: var(--text-muted);
  line-height: 1.6;
}
.annotation-suggestion strong {
  color: var(--text-title);
}

.common-problems-card {
  padding-bottom: 8px;
}
.problem-list {
  margin-bottom: 16px;
}
.problem-item {
  margin-bottom: 12px;
}
.problem-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
}
.problem-name {
  color: var(--text-body);
}
.problem-count {
  color: var(--text-title);
  font-weight: 600;
}
.problem-actions {
  text-align: right;
}

.empty-hint {
  text-align: center;
  padding: 24px 0;
  color: var(--text-muted);
  font-size: 13px;
}

.abnormal-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.threshold-label {
  font-size: 14px;
  color: var(--text-body);
}
.threshold-unit {
  font-size: 14px;
  color: var(--text-muted);
}
</style>

<template>
  <div class="student-dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="item in statCards" :key="item.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: item.color }">
              <el-icon :size="28"><component :is="item.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ item.value }}</div>
              <div class="stat-label">{{ item.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 我的实训项目 -->
    <el-card shadow="hover" class="section-card">
      <template #header>
        <div class="card-header">
          <span>我的实训项目</span>
          <el-button size="small" text @click="$router.push('/student/projects')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <div v-loading="loading" class="project-grid">
        <div v-for="p in displayedProjects" :key="p.id"
          class="project-card" @click="viewProject(p)">
          <div class="project-card-top">
            <div class="project-card-status-bar" :class="'status-' + (p.status || 'pending')"></div>
            <div class="project-card-header">
              <div class="project-title-area">
                <div class="project-title">{{ p.title }}</div>
                <div class="project-course">{{ p.course_name || '' }}</div>
              </div>
              <div class="project-badges">
                <el-tag :type="p.status === 'active' ? 'success' : (p.status === 'completed' ? 'info' : 'warning')" size="small">
                  {{ p.status === 'active' ? '进行中' : (p.status === 'completed' ? '已归档' : '未开始') }}
                </el-tag>
                <el-tag v-if="p.hasSubmitted" :type="p.submission_status === 'evaluated' ? 'success' : 'primary'" size="small">
                  {{ p.submission_status === 'evaluated' ? '已评分' : '已提交' }}
                </el-tag>
                <el-tag v-else type="danger" size="small" effect="plain">未提交</el-tag>
              </div>
            </div>
            <div class="project-card-body">
              <div class="project-meta">
                <div class="project-meta-item">
                  <el-icon><User /></el-icon>
                  <span>{{ p.teacher_name || '未指定教师' }}</span>
                </div>
                <div class="project-meta-item" v-if="p.deadline">
                  <el-icon><Clock /></el-icon>
                  <span>截止：{{ p.deadline }}</span>
                </div>
              </div>
            </div>
            <div class="project-card-progress">
              <div class="progress-row">
                <template v-if="p.hasSubmitted && p.final_score != null">
                  <div class="score-display">{{ p.final_score }}<span class="score-unit">分</span></div>
                </template>
                <template v-else>
                  <div class="progress-bar-track">
                    <div class="progress-bar-fill" :style="{ width: progressPercent(p) + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ p.hasSubmitted ? '已提交' : '尚未提交' }}</span>
                </template>
              </div>
            </div>
          </div>
          <div class="project-card-footer">
            <span class="footer-info">{{ formatDate(p.updated_at) }} 更新</span>
            <el-button v-if="p.status === 'active' && !p.hasSubmitted" type="primary" size="small" @click.stop="goSubmit(p)">
              提交作业
            </el-button>
            <el-button v-else-if="p.status === 'active' && p.submission_status !== 'evaluated'" type="primary" size="small" @click.stop="goSubmit(p)">
              重新提交
            </el-button>
            <el-button v-else-if="p.submission_status === 'evaluated'" type="success" size="small" @click.stop="viewReport(p)">
              查看成绩
            </el-button>
            <el-button v-else text size="small" @click.stop="viewProject(p)">
              查看详情
            </el-button>
          </div>
        </div>
        <div v-if="!loading && projects.length === 0" class="empty-state">
          <el-empty description="暂无实训项目" />
        </div>
      </div>
    </el-card>

    <!-- 最近提交记录 -->
    <el-card shadow="hover" class="section-card">
      <template #header>
        <div class="card-header">
          <span>最近提交记录</span>
          <el-button v-if="submissions.length > 5" size="small" text @click="$router.push('/student/submissions')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table :data="recentSubmissions" v-loading="subLoading" stripe size="small" style="width: 100%">
        <el-table-column prop="training_title" label="实训项目" min-width="160" show-overflow-tooltip />
        <el-table-column prop="created_at" label="提交时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="final_score" label="得分" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.final_score != null" :type="scoreType(row.final_score)" size="small">
              {{ row.final_score }}
            </el-tag>
            <span v-else class="no-score">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'evaluated' ? 'success' : 'warning'" size="small">
              {{ row.status === 'evaluated' ? '已评价' : '待评价' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewSubmission(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!subLoading && submissions.length === 0" class="empty-table">
        <el-empty description="暂无提交记录" :image-size="80" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { trainingAPI } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()

const projects = ref([])
const submissions = ref([])
const loading = ref(false)
const subLoading = ref(false)

// 统计卡片
const stats = computed(() => {
  const total = projects.value.length
  const submitted = projects.value.filter(p => p.hasSubmitted).length
  const evaluated = projects.value.filter(p => p.submission_status === 'evaluated').length
  const scores = projects.value
    .filter(p => p.final_score != null)
    .map(p => p.final_score)
  const avg = scores.length > 0
    ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)
    : 0
  return { total, submitted, evaluated, avg }
})

const statCards = computed(() => [
  { label: '我的项目', value: stats.value.total, icon: 'Notebook', color: '#409EFF' },
  { label: '已提交', value: stats.value.submitted, icon: 'Upload', color: '#67C23A' },
  { label: '已评价', value: stats.value.evaluated, icon: 'Finished', color: '#E6A23C' },
  { label: '平均分', value: stats.value.avg, icon: 'TrendCharts', color: '#F56C6C' },
])

// 首页最多显示4个项目
const displayedProjects = computed(() => projects.value.slice(0, 4))

// 最近提交（最多5条）
const recentSubmissions = computed(() => submissions.value.slice(0, 5))

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const scoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}

const progressPercent = (p) => {
  if (p.status === 'completed') return 100
  if (p.hasSubmitted) return 80
  return 0
}

const viewProject = (p) => {
  router.push(`/student/project/${p.id}`)
}

const goSubmit = (p) => {
  router.push(`/student/submit/${p.id}`)
}

const viewReport = (p) => {
  router.push(`/student/report/${p.id}`)
}

const viewSubmission = (row) => {
  router.push(`/student/submission/${row.id}`)
}

onMounted(async () => {
  loading.value = true
  subLoading.value = true
  try {
    const [projRes, subRes] = await Promise.all([
      trainingAPI.myProjects(),
      trainingAPI.mySubmissions()
    ])
    projects.value = projRes.data || []
    submissions.value = subRes.data || []
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
    subLoading.value = false
  }
})
</script>

<style scoped>
.stats-row { margin-bottom: 20px; }
.stat-card .stat-content { display: flex; align-items: center; gap: 16px; }
.stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.stat-value { font-size: 28px; font-weight: bold; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.section-card { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header span { font-size: 16px; font-weight: 600; color: #303133; }

/* 项目卡片网格 */
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}
.project-card {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e5e6eb;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.project-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
  border-color: #bae0ff;
}
.project-card-status-bar {
  height: 4px;
  background: #e5e6eb;
}
.project-card-status-bar.status-active {
  background: linear-gradient(90deg, #52c41a, #73d13d);
}
.project-card-status-bar.status-completed {
  background: linear-gradient(90deg, #409eff, #7c3aed);
}
.project-card-status-bar.status-pending {
  background: linear-gradient(90deg, #faad14, #f59e0b);
}
.project-card-header {
  padding: 16px 16px 8px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.project-title-area { flex: 1; min-width: 0; }
.project-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.4;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.project-course { font-size: 12px; color: #86909c; }
.project-badges { display: flex; gap: 4px; flex-wrap: wrap; flex-shrink: 0; }
.project-badges .el-tag { margin: 0; }
.project-card-body { padding: 4px 16px 8px; }
.project-meta { display: flex; flex-wrap: wrap; gap: 6px 16px; }
.project-meta-item { display: flex; align-items: center; gap: 4px; font-size: 13px; color: #86909c; }
.project-meta-item .el-icon { font-size: 14px; }
.project-card-progress { padding: 0 16px 12px; }
.progress-row { display: flex; align-items: center; gap: 12px; }
.progress-bar-track { flex: 1; height: 6px; background: #f2f3f5; border-radius: 3px; overflow: hidden; }
.progress-bar-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #409eff, #7c3aed); transition: width 0.5s ease; }
.progress-text { font-size: 12px; color: #86909c; white-space: nowrap; }
.score-display { font-size: 22px; font-weight: 700; color: #409eff; line-height: 1; }
.score-display .score-unit { font-size: 12px; font-weight: 500; color: #86909c; }
.project-card-footer {
  padding: 12px 16px;
  border-top: 1px solid #f2f3f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.footer-info { font-size: 12px; color: #86909c; }
.empty-state { grid-column: 1 / -1; padding: 40px 0; }
.empty-table { padding: 20px 0; }
.no-score { color: #c0c4cc; }
</style>
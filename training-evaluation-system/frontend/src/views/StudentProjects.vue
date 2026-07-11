<template>
  <div class="student-projects">
    <div class="page-header">
      <h2>我的实训项目</h2>
      <el-input v-model="searchQuery" placeholder="搜索实训项目..." prefix-icon="Search" clearable style="width: 260px" />
    </div>

    <div v-loading="loading" class="project-grid">
      <div v-for="p in filteredProjects" :key="p.id"
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
    </div>

    <div v-if="!loading && filteredProjects.length === 0" class="empty-state">
      <el-empty description="暂无实训项目" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { trainingAPI } from '../api'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const searchQuery = ref('')

const filteredProjects = computed(() => {
  if (!searchQuery.value) return projects.value
  const q = searchQuery.value.toLowerCase()
  return projects.value.filter(p =>
    (p.title || '').toLowerCase().includes(q) ||
    (p.course_name || '').toLowerCase().includes(q) ||
    (p.teacher_name || '').toLowerCase().includes(q)
  )
})

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const progressPercent = (p) => {
  if (p.status === 'completed') return 100
  if (p.hasSubmitted) return 80
  return 0
}

const viewProject = (p) => router.push(`/student/project/${p.id}`)
const goSubmit = (p) => router.push(`/student/submit/${p.id}`)
const viewReport = (p) => router.push(`/student/report/${p.id}`)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await trainingAPI.myProjects()
    projects.value = data || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 20px; font-weight: 600; color: #1d2129; margin: 0; }
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
.project-card-status-bar.status-active { background: linear-gradient(90deg, #52c41a, #73d13d); }
.project-card-status-bar.status-completed { background: linear-gradient(90deg, #409eff, #7c3aed); }
.project-card-status-bar.status-pending { background: linear-gradient(90deg, #faad14, #f59e0b); }
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
.empty-state { padding: 60px 0; }
</style>
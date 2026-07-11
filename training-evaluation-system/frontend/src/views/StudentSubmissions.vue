<template>
  <div class="student-submissions">
    <div class="page-header">
      <h2>提交记录</h2>
    </div>

    <el-card shadow="hover">
      <el-table :data="submissions" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="training_title" label="实训项目" min-width="180" show-overflow-tooltip />
        <el-table-column prop="created_at" label="提交时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="文件数" width="80" align="center">
          <template #default="{ row }">{{ row.files?.length || 0 }}</template>
        </el-table-column>
        <el-table-column prop="final_score" label="得分" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.final_score != null" :type="scoreType(row.final_score)" size="small">
              {{ row.final_score }}
            </el-tag>
            <span v-else class="no-score">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'evaluated' ? 'success' : 'warning'" size="small">
              {{ row.status === 'evaluated' ? '已评价' : '待评价' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewDetail(row)">查看</el-button>
            <el-button v-if="row.status === 'evaluated'" size="small" type="success" link @click="viewReport(row)">评价报告</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!loading && submissions.length === 0" class="empty-table">
        <el-empty description="暂无提交记录" :image-size="80" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { trainingAPI } from '../api'

const router = useRouter()
const submissions = ref([])
const loading = ref(false)

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const scoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}

const viewDetail = (row) => router.push(`/student/submission/${row.id}`)
const viewReport = (row) => router.push(`/student/report/${row.id}`)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await trainingAPI.mySubmissions()
    submissions.value = data || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 20px; font-weight: 600; color: #1d2129; margin: 0; }
.no-score { color: #c0c4cc; }
.empty-table { padding: 20px 0; }
</style>
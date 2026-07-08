<template>
  <div class="training-list">
    <div class="page-header">
      <h2>实训项目管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 创建实训项目
      </el-button>
    </div>

    <el-card shadow="hover">
      <el-table :data="trainings" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="实训标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="course_name" label="课程" width="120" />
        <el-table-column prop="teacher_name" label="教师" width="100" />
        <el-table-column prop="submission_count" label="提交数" width="80" align="center" />
        <el-table-column prop="avg_score" label="平均分" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.avg_score > 0" :type="row.avg_score >= 80 ? 'success' : 'warning'" size="small">
              {{ row.avg_score }}
            </el-tag>
            <span v-else class="no-score">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/training/${row.id}`)">详情</el-button>
            <el-button size="small" type="success" link @click="$router.push('/evaluation-templates')">评价规则配置</el-button>
            <el-button size="small" type="warning" link @click="$router.push(`/report/${row.id}`)">报告</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="创建实训项目" width="600px" :close-on-click-modal="false">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="实训标题" required>
          <el-input v-model="createForm.title" placeholder="如：Web全栈开发实训" />
        </el-form-item>
        <el-form-item label="课程名称">
          <el-input v-model="createForm.course_name" placeholder="如：软件工程实训" />
        </el-form-item>
        <el-form-item label="教师姓名">
          <el-input v-model="createForm.teacher_name" placeholder="指导教师" />
        </el-form-item>
        <el-form-item label="实训描述">
          <el-input v-model="createForm.description" type="textarea" :rows="4" placeholder="描述实训项目的目标和要求" />
        </el-form-item>
        <el-form-item label="预期步骤">
          <el-input v-model="createForm.expected_steps" type="textarea" :rows="3"
            placeholder='JSON数组格式，如：["需求分析","系统设计","编码实现","测试验收"]' />
        </el-form-item>
        <el-form-item label="预期成果">
          <el-input v-model="createForm.expected_outcomes" type="textarea" :rows="3"
            placeholder="描述预期实训成果，如：学生应完成一个完整的Web应用..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { trainingAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const trainings = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)

const createForm = ref({
  title: '', course_name: '', teacher_name: '', description: '',
  expected_steps: '', expected_outcomes: ''
})

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await trainingAPI.list()
    trainings.value = data
  } finally { loading.value = false }
}

const handleCreate = async () => {
  if (!createForm.value.title) { ElMessage.warning('请输入实训标题'); return }
  creating.value = true
  try {
    await trainingAPI.create(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.value = { title: '', course_name: '', teacher_name: '', description: '', expected_steps: '', expected_outcomes: '' }
    loadData()
  } finally { creating.value = false }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除实训"${row.title}"吗？相关数据将一并删除。`, '确认删除', { type: 'warning' })
    await trainingAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 20px; color: #303133; }
.no-score { color: #c0c4cc; }
</style>
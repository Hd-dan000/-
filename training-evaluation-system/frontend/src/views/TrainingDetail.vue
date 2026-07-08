<template>
  <div class="training-detail">
    <div class="page-header">
      <el-button @click="$router.push('/training')" text>
        <el-icon><ArrowLeft /></el-icon> 返回列表
      </el-button>
      <h2>{{ training.title }}</h2>
      <div>
        <el-button type="warning" @click="$router.push('/evaluation-templates')">
          <el-icon><Setting /></el-icon> 评价规则配置
        </el-button>
        <el-button type="primary" @click="handleBatchEvaluate" :loading="batchEvaluating" :disabled="!hasPending">
          <el-icon><MagicStick /></el-icon> 批量智能评价
        </el-button>
      </div>
    </div>

    <el-card shadow="hover" class="info-card">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="实训标题">{{ training.title }}</el-descriptions-item>
        <el-descriptions-item label="课程名称">{{ training.course_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="教师">{{ training.teacher_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交数">{{ training.submission_count }}</el-descriptions-item>
        <el-descriptions-item label="实训描述" :span="2">{{ training.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预期步骤" :span="2">{{ training.expected_steps || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预期成果" :span="2">{{ training.expected_outcomes || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="hover" class="submission-card">
      <template #header>
        <div class="card-header">
          <span>学生提交列表 ({{ submissions.length }})</span>
          <el-button type="primary" size="small" @click="showSubmitDialog = true">
            <el-icon><Upload /></el-icon> 新增提交
          </el-button>
        </div>
      </template>
      <el-table :data="submissions" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="student_name" label="学生姓名" width="100" />
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column label="文件数" width="80" align="center">
          <template #default="{ row }">{{ row.files?.length || 0 }}</template>
        </el-table-column>
        <el-table-column prop="step_completeness" label="步骤完整性" width="100" align="center">
          <template #default="{ row }">{{ row.step_completeness ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="outcome_quality" label="成果质量" width="80" align="center">
          <template #default="{ row }">{{ row.outcome_quality ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="logic_score" label="逻辑性" width="80" align="center">
          <template #default="{ row }">{{ row.logic_score ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="ai_total_score" label="AI评分" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.ai_total_score" type="primary" size="small">{{ row.ai_total_score }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="teacher_score" label="教师评分" width="90" align="center">
          <template #default="{ row }">{{ row.teacher_score ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="final_score" label="最终得分" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.final_score" :type="scoreType(row.final_score)" size="small">{{ row.final_score }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'evaluated' ? 'success' : 'warning'" size="small">
              {{ row.status === 'evaluated' ? '已评价' : '待评价' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/submission/${row.id}`)">详情</el-button>
            <el-button size="small" type="success" link @click="handleEvaluate(row)" :loading="row._evaluating">评价</el-button>
            <el-button size="small" type="danger" link @click="handleDeleteSubmission(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showSubmitDialog" title="学生提交实训成果" width="550px">
      <el-form label-width="80px">
        <el-form-item label="学生姓名" required>
          <el-input v-model="submitForm.student_name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="submitForm.student_id" placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="实训文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="10"
            multiple
            drag
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 Word、PDF、Excel、图片、文本等格式，单文件不超过50MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSubmitDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { trainingAPI, evaluationAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const trainingId = computed(() => Number(route.params.id))

const training = ref({})
const submissions = ref([])
const loading = ref(false)
const showSubmitDialog = ref(false)
const submitting = ref(false)
const batchEvaluating = ref(false)

const submitForm = ref({ student_name: '', student_id: '' })
const selectedFiles = ref([])

const hasPending = computed(() => submissions.value.some(s => s.status !== 'evaluated'))

const scoreType = (s) => {
  if (s >= 90) return 'success'
  if (s >= 70) return 'warning'
  return 'danger'
}

const loadData = async () => {
  loading.value = true
  try {
    const [tRes, sRes] = await Promise.all([
      trainingAPI.get(trainingId.value),
      trainingAPI.submissions(trainingId.value)
    ])
    training.value = tRes.data
    submissions.value = sRes.data.map(s => ({ ...s, _evaluating: false }))
  } finally { loading.value = false }
}

const handleFileChange = (file) => { selectedFiles.value.push(file.raw) }
const handleFileRemove = (file) => {
  const idx = selectedFiles.value.findIndex(f => f.name === file.name)
  if (idx > -1) selectedFiles.value.splice(idx, 1)
}

const handleSubmit = async () => {
  if (!submitForm.value.student_name) { ElMessage.warning('请输入学生姓名'); return }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('student_name', submitForm.value.student_name)
    fd.append('student_id', submitForm.value.student_id)
    selectedFiles.value.forEach(f => fd.append('files', f))
    await trainingAPI.submit(trainingId.value, fd)
    ElMessage.success('提交成功')
    showSubmitDialog.value = false
    submitForm.value = { student_name: '', student_id: '' }
    selectedFiles.value = []
    loadData()
  } finally { submitting.value = false }
}

const handleEvaluate = async (row) => {
  row._evaluating = true
  try {
    await evaluationAPI.evaluate(row.id)
    ElMessage.success('评价完成')
    loadData()
  } finally { row._evaluating = false }
}

const handleBatchEvaluate = async () => {
  batchEvaluating.value = true
  try {
    const { data } = await evaluationAPI.batchEvaluate(trainingId.value)
    ElMessage.success(data.message)
    loadData()
  } finally { batchEvaluating.value = false }
}

const handleDeleteSubmission = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除"${row.student_name}"的提交吗？`, '确认删除', { type: 'warning' })
    await trainingAPI.deleteSubmission(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.page-header h2 { font-size: 20px; color: #303133; flex: 1; }
.info-card { margin-bottom: 16px; }
.submission-card { margin-top: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
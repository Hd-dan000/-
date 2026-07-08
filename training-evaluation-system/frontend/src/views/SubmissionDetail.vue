<template>
  <div class="submission-detail">
    <div class="page-header">
      <el-button @click="$router.go(-1)" text><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <h2>提交详情 - {{ submission.student_name }}</h2>
      <div>
        <el-button type="primary" @click="handleEvaluate" :loading="evaluating" v-if="submission.status !== 'evaluated'">
          <el-icon><MagicStick /></el-icon> 智能评价
        </el-button>
        <el-button type="success" @click="handleReparse" :loading="reparsing">
          <el-icon><Refresh /></el-icon> 重新解析
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>基本信息</template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="学生姓名">{{ submission.student_name }}</el-descriptions-item>
            <el-descriptions-item label="学号">{{ submission.student_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="submission.status === 'evaluated' ? 'success' : 'warning'" size="small">
                {{ submission.status === 'evaluated' ? '已评价' : '待评价' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="提交时间">{{ formatDate(submission.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="hover" class="files-card">
          <template #header>上传文件 ({{ submission.files?.length || 0 }})</template>
          <div v-if="submission.files?.length">
            <el-tag v-for="f in submission.files" :key="f.filename" class="file-tag" type="info" size="small">
              {{ f.filename }}
            </el-tag>
          </div>
          <div v-else class="no-data">无上传文件</div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="hover" class="score-card">
          <template #header>评分详情</template>
          <el-row :gutter="16" v-if="submission.status === 'evaluated'">
            <el-col :span="6">
              <div class="score-item">
                <div class="score-label">步骤完整性</div>
                <div class="score-value">{{ submission.step_completeness ?? '-' }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="score-item">
                <div class="score-label">成果质量</div>
                <div class="score-value">{{ submission.outcome_quality ?? '-' }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="score-item">
                <div class="score-label">逻辑性</div>
                <div class="score-value">{{ submission.logic_score ?? '-' }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="score-item final">
                <div class="score-label">最终得分</div>
                <div class="score-value">{{ submission.final_score ?? '-' }}</div>
              </div>
            </el-col>
          </el-row>
          <div v-else class="no-data">尚未评价</div>
        </el-card>

        <el-card shadow="hover" class="teacher-card">
          <template #header>教师主观补评</template>
          <el-form label-width="80px" size="small">
            <el-form-item label="评分">
              <el-input-number v-model="teacherForm.teacher_score" :min="0" :max="100" :step="0.5" />
            </el-form-item>
            <el-form-item label="评语">
              <el-input v-model="teacherForm.teacher_comment" type="textarea" :rows="3" placeholder="输入教师评语..." />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleTeacherReview" :loading="reviewing">提交补评</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="hover" v-if="submission.evaluation_detail">
          <template #header>评价详情数据</template>
          <pre class="json-view">{{ JSON.stringify(submission.evaluation_detail, null, 2) }}</pre>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { trainingAPI, evaluationAPI } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const submissionId = computed(() => Number(route.params.id))

const submission = ref({})
const evaluating = ref(false)
const reparsing = ref(false)
const reviewing = ref(false)

const teacherForm = ref({ teacher_score: null, teacher_comment: '' })

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const loadData = async () => {
  const { data } = await trainingAPI.getSubmission(submissionId.value)
  submission.value = data
  teacherForm.value = {
    teacher_score: data.teacher_score,
    teacher_comment: data.teacher_comment || ''
  }
}

const handleEvaluate = async () => {
  evaluating.value = true
  try {
    await evaluationAPI.evaluate(submissionId.value)
    ElMessage.success('评价完成')
    loadData()
  } finally { evaluating.value = false }
}

const handleReparse = async () => {
  reparsing.value = true
  try {
    await evaluationAPI.reparse(submissionId.value)
    ElMessage.success('重新解析完成')
    loadData()
  } finally { reparsing.value = false }
}

const handleTeacherReview = async () => {
  reviewing.value = true
  try {
    await evaluationAPI.teacherReview(submissionId.value, teacherForm.value)
    ElMessage.success('补评提交成功')
    loadData()
  } finally { reviewing.value = false }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; color: #303133; }
.files-card { margin-top: 16px; }
.file-tag { margin: 4px; }
.score-card { margin-bottom: 16px; }
.score-item { text-align: center; padding: 16px; background: #f5f7fa; border-radius: 8px; }
.score-item.final { background: #ecf5ff; }
.score-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.score-value { font-size: 28px; font-weight: bold; color: #409EFF; }
.score-item.final .score-value { color: #E6A23C; }
.teacher-card { margin-bottom: 16px; }
.json-view { background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 12px; max-height: 400px; overflow: auto; white-space: pre-wrap; }
.no-data { text-align: center; color: #c0c4cc; padding: 20px; }
</style>
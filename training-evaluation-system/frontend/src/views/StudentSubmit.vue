<template>
  <div class="student-submit">
    <div class="page-header">
      <el-button @click="$router.go(-1)" text>
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h2>提交作业 - {{ training.title }}</h2>
    </div>

    <el-card shadow="hover" class="info-card" v-if="training.id">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="实训标题">{{ training.title }}</el-descriptions-item>
        <el-descriptions-item label="课程名称">{{ training.course_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="教师">{{ training.teacher_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="截止日期">{{ training.deadline || '-' }}</el-descriptions-item>
        <el-descriptions-item label="实训描述" :span="2">{{ training.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="hover" class="submit-card">
      <template #header>提交实训成果</template>
      <el-form label-width="100px">
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
      <div class="submit-actions">
        <el-button type="primary" @click="handleSubmit" :loading="submitting" :disabled="selectedFiles.length === 0">
          提交作业
        </el-button>
        <el-button @click="$router.go(-1)">取消</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { trainingAPI } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const trainingId = computed(() => Number(route.params.id))

const training = ref({})
const selectedFiles = ref([])
const submitting = ref(false)
const uploadRef = ref(null)

const handleFileChange = (file) => { selectedFiles.value.push(file.raw) }
const handleFileRemove = (file) => {
  const idx = selectedFiles.value.findIndex(f => f.name === file.name)
  if (idx > -1) selectedFiles.value.splice(idx, 1)
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    const fd = new FormData()
    selectedFiles.value.forEach(f => fd.append('files', f))
    await trainingAPI.submit(trainingId.value, fd)
    ElMessage.success('提交成功')
    router.push('/student/projects')
  } finally { submitting.value = false }
}

onMounted(async () => {
  try {
    const { data } = await trainingAPI.get(trainingId.value)
    training.value = data
  } catch (e) { /* handled by interceptor */ }
})
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #1d2129; margin: 0; }
.info-card { margin-bottom: 20px; }
.submit-card { margin-bottom: 20px; }
.submit-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 16px; }
</style>
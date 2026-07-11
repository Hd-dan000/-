<template>
  <div class="student-report">
    <div class="page-header">
      <el-button @click="$router.go(-1)" text>
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h2>{{ submission.training_title || '评价报告' }}</h2>
    </div>

    <div v-loading="loading">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card shadow="hover" class="info-card">
            <template #header>基本信息</template>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="实训项目">{{ submission.training_title || '-' }}</el-descriptions-item>
              <el-descriptions-item label="提交时间">{{ formatDate(submission.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="评价状态">
                <el-tag :type="submission.status === 'evaluated' ? 'success' : 'warning'" size="small">
                  {{ submission.status === 'evaluated' ? '已评价' : '待评价' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <el-col :span="16">
          <el-card shadow="hover" class="score-card">
            <template #header>评分详情</template>
            <div v-if="submission.status === 'evaluated'">
              <el-row :gutter="16">
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
                    <div class="score-label">综合评分</div>
                    <div class="score-value">{{ submission.final_score ?? '-' }}</div>
                  </div>
                </el-col>
              </el-row>
              <div v-if="submission.teacher_comment" class="comment-section">
                <el-divider />
                <div class="comment-label">教师评语</div>
                <div class="comment-content">{{ submission.teacher_comment }}</div>
              </div>
            </div>
            <div v-else class="no-data">尚未评价，请耐心等待</div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { trainingAPI } from '../api'

const route = useRoute()
const submissionId = computed(() => Number(route.params.id))

const submission = ref({})
const loading = ref(false)

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await trainingAPI.getSubmission(submissionId.value)
    submission.value = data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #1d2129; margin: 0; }
.info-card { margin-bottom: 20px; }
.score-card { margin-bottom: 20px; }
.score-item { text-align: center; padding: 20px 12px; background: #f5f7fa; border-radius: 8px; }
.score-item.final { background: #ecf5ff; }
.score-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.score-value { font-size: 28px; font-weight: bold; color: #409eff; }
.score-item.final .score-value { color: #e6a23c; }
.no-data { text-align: center; color: #c0c4cc; padding: 40px 20px; }
.comment-section { margin-top: 16px; }
.comment-label { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 8px; }
.comment-content { font-size: 14px; color: #606266; line-height: 1.6; padding: 12px; background: #f5f7fa; border-radius: 6px; }
</style>
<template>
  <div class="evaluation-config">
    <div class="page-header">
      <el-button @click="$router.push(`/training/${trainingId}`)" text>
        <el-icon><ArrowLeft /></el-icon> 返回实训详情
      </el-button>
      <h2>评价指标配置</h2>
    </div>

    <el-card shadow="hover" class="config-card">
      <template #header>
        <div class="card-header">
          <span>自定义评价指标</span>
          <el-button type="primary" size="small" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon> 添加指标
          </el-button>
        </div>
      </template>
      <el-table :data="indicators" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="指标名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="weight" label="权重" width="80" align="center" />
        <el-table-column prop="max_score" label="满分" width="80" align="center" />
        <el-table-column prop="indicator_type" label="评分方式" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.indicator_type === 'auto' ? 'primary' : 'warning'" size="small">
              {{ row.indicator_type === 'auto' ? 'AI自动' : '教师手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="editIndicator(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="indicators.length === 0 && !loading" class="empty-hint">
        暂无自定义指标，AI将使用默认三维度等权重评价（步骤完整性、成果质量、逻辑性）
      </div>
    </el-card>

    <el-dialog v-model="showAddDialog" :title="editingId ? '编辑指标' : '添加指标'" width="500px">
      <el-form :model="indicatorForm" label-width="100px">
        <el-form-item label="指标名称" required>
          <el-input v-model="indicatorForm.name" placeholder="如：代码规范性" />
        </el-form-item>
        <el-form-item label="指标描述">
          <el-input v-model="indicatorForm.description" type="textarea" :rows="2" placeholder="描述该指标的评价标准" />
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="indicatorForm.weight" :min="0.1" :max="10" :step="0.1" :precision="1" />
          <span class="form-tip">权重越大，该指标对总分影响越大</span>
        </el-form-item>
        <el-form-item label="满分值">
          <el-input-number v-model="indicatorForm.max_score" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="评分方式">
          <el-radio-group v-model="indicatorForm.indicator_type">
            <el-radio value="auto">AI自动评分</el-radio>
            <el-radio value="manual">教师手动评分</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          {{ editingId ? '更新' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { evaluationAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const trainingId = computed(() => Number(route.params.trainingId))

const indicators = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const saving = ref(false)
const editingId = ref(null)

const indicatorForm = ref({
  name: '', description: '', weight: 1.0, max_score: 100, indicator_type: 'auto'
})

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await evaluationAPI.indicators(trainingId.value)
    indicators.value = data
  } finally { loading.value = false }
}

const editIndicator = (row) => {
  editingId.value = row.id
  indicatorForm.value = {
    name: row.name, description: row.description || '',
    weight: row.weight, max_score: row.max_score, indicator_type: row.indicator_type
  }
  showAddDialog.value = true
}

const handleSave = async () => {
  if (!indicatorForm.value.name) { ElMessage.warning('请输入指标名称'); return }
  saving.value = true
  try {
    if (editingId.value) {
      await evaluationAPI.updateIndicator(editingId.value, indicatorForm.value)
      ElMessage.success('更新成功')
    } else {
      await evaluationAPI.createIndicator({ ...indicatorForm.value, training_id: trainingId.value })
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    editingId.value = null
    indicatorForm.value = { name: '', description: '', weight: 1.0, max_score: 100, indicator_type: 'auto' }
    loadData()
  } finally { saving.value = false }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除指标"${row.name}"吗？`, '确认删除', { type: 'warning' })
    await evaluationAPI.deleteIndicator(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { font-size: 20px; color: #303133; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.empty-hint { text-align: center; color: #909399; padding: 30px 0; }
.form-tip { margin-left: 10px; color: #909399; font-size: 12px; }
</style>
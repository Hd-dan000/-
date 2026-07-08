<template>
  <div class="template-management">
    <div class="page-header">
      <div>
        <h2>评价规则配置</h2>
        <p>教师可先创建多套评价规则模板，再将规则应用到不同实训项目。</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">新建模板</el-button>
        <el-button @click="openCopyDialog" :disabled="!selectedTemplate">复制模板</el-button>
      </div>
    </div>

    <div class="template-tabs">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="评价指标配置" name="indicators">
          <div v-if="currentTemplate">
            <div class="template-info-bar">
              <span class="template-name">{{ currentTemplate.name }}</span>
              <el-tag v-if="currentTemplate.is_default" type="success">默认模板</el-tag>
              <el-tag v-if="currentTemplate.created_by_role === 'super_admin'" type="info">系统模板</el-tag>
              <span class="template-status">已应用项目: {{ assignedCount }}个</span>
              <el-button size="small" @click="openAssignDialog">应用到项目</el-button>
            </div>

            <el-card shadow="hover" class="config-card">
              <template #header>
                <div class="card-header">
                  <span>评价指标列表</span>
                  <div class="card-actions">
                    <span class="weight-total">当前总权重: {{ totalWeight }}%</span>
                    <el-button type="primary" size="small" @click="showAddIndicatorDialog = true">
                      <el-icon><Plus /></el-icon> 添加一级指标
                    </el-button>
                  </div>
                </div>
              </template>
              <el-table :data="currentTemplate.indicators" stripe style="width: 100%">
                <el-table-column type="expand" width="50">
                  <template #default="{ row }">
                    <el-table :data="row.children || []" style="width: 100%" border>
                      <el-table-column prop="name" label="二级指标" min-width="150">
                        <template #default="{ row }">
                          <span class="indent-20">{{ row.name }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="max_score" label="满分值" width="100" align="center">
                        <template #default="{ row }">
                          <el-input-number v-model="row.max_score" :min="1" :max="100" size="small" @change="recalcWeight" />
                        </template>
                      </el-table-column>
                      <el-table-column prop="weight" label="权重" width="100" align="center">
                        <template #default="{ row }">
                          <el-input-number v-model="row.weight" :min="1" :max="100" size="small" @change="recalcWeight" />
                        </template>
                      </el-table-column>
                      <el-table-column prop="evaluation_basis" label="评分依据" min-width="150">
                        <template #default="{ row }">
                          <el-input v-model="row.evaluation_basis" placeholder="评分依据" size="small" />
                        </template>
                      </el-table-column>
                      <el-table-column prop="scoring_body" label="评分主体" width="120" align="center">
                        <template #default="{ row }">
                          <el-select v-model="row.scoring_body" size="small" placeholder="选择评分主体">
                            <el-option label="AI自动" value="ai" />
                            <el-option label="教师手动" value="teacher" />
                            <el-option label="AI+教师" value="both" />
                          </el-select>
                        </template>
                      </el-table-column>
                      <el-table-column label="操作" width="100">
                        <template #default="{ row, $index }">
                          <el-button size="small" type="primary" link @click="editChildIndicator(row, $index)">编辑</el-button>
                          <el-button size="small" type="danger" link @click="deleteChildIndicator($index)">删除</el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                    <div v-if="!row.children?.length" class="empty-hint">暂无二级指标</div>
                    <el-button size="small" @click="showAddChildIndicatorDialog(row)">+ 添加二级指标</el-button>
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="指标名称" min-width="150">
                  <template #default="{ row }">
                    <span class="primary-indicator">{{ row.name }}</span>
                    <el-icon v-if="row.children?.length" class="expand-icon"><ArrowDown /></el-icon>
                  </template>
                </el-table-column>
                <el-table-column prop="max_score" label="满分值" width="100" align="center">
                  <template #default="{ row }">
                    <el-input-number v-model="row.max_score" :min="1" :max="100" size="small" @change="recalcWeight" />
                  </template>
                </el-table-column>
                <el-table-column prop="weight" label="权重" width="100" align="center">
                  <template #default="{ row }">
                    <el-input-number v-model="row.weight" :min="1" :max="100" size="small" @change="recalcWeight" />
                  </template>
                </el-table-column>
                <el-table-column label="权重占比" width="100" align="center">
                  <template #default="{ row }">
                    {{ getWeightRatio(row.weight) }}%
                  </template>
                </el-table-column>
                <el-table-column prop="evaluation_basis" label="评分依据" min-width="180">
                  <template #default="{ row }">
                    <el-input v-model="row.evaluation_basis" placeholder="评分依据" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="scoring_body" label="评分主体" width="120" align="center">
                  <template #default="{ row }">
                    <el-select v-model="row.scoring_body" size="small" placeholder="选择评分主体">
                      <el-option label="AI自动" value="ai" />
                      <el-option label="教师手动" value="teacher" />
                      <el-option label="AI+教师" value="both" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150">
                  <template #default="{ row, $index }">
                    <el-button size="small" type="primary" link @click="editIndicator(row)">编辑</el-button>
                    <el-button size="small" type="danger" link @click="deleteIndicator($index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div v-if="!currentTemplate.indicators.length" class="empty-hint">暂无评价指标，请点击上方按钮添加</div>
            </el-card>
          </div>
          <div v-else class="no-template">
            <el-empty description="请从左侧选择一个模板开始配置" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="智能评语模板" name="comments">
          <div v-if="currentTemplate">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>评语模板配置</span>
                  <el-button type="primary" size="small" @click="showAddCommentDialog = true">
                    <el-icon><Plus /></el-icon> 添加评语模板
                  </el-button>
                </div>
              </template>
              <el-table :data="currentTemplate.comment_templates" stripe style="width: 100%">
                <el-table-column prop="label" label="等级标签" width="100" align="center">
                  <template #default="{ row }">
                    <el-input v-model="row.label" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="min_score" label="最低分" width="100" align="center">
                  <template #default="{ row }">
                    <el-input-number v-model="row.min_score" :min="0" :max="100" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="max_score" label="最高分" width="100" align="center">
                  <template #default="{ row }">
                    <el-input-number v-model="row.max_score" :min="0" :max="100" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="template" label="评语内容" min-width="300">
                  <template #default="{ row }">
                    <el-input v-model="row.template" type="textarea" :rows="2" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ $index }">
                    <el-button size="small" type="danger" link @click="deleteCommentTemplate($index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
          <div v-else class="no-template">
            <el-empty description="请从左侧选择一个模板开始配置" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="错误识别规则" name="errors">
          <div v-if="currentTemplate">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>错误识别规则配置</span>
                  <el-button type="primary" size="small" @click="showAddErrorRuleDialog = true">
                    <el-icon><Plus /></el-icon> 添加规则
                  </el-button>
                </div>
              </template>
              <el-table :data="currentTemplate.error_rules" stripe style="width: 100%">
                <el-table-column prop="name" label="规则名称" width="150">
                  <template #default="{ row }">
                    <el-input v-model="row.name" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="keywords" label="关键词" min-width="200">
                  <template #default="{ row }">
                    <el-input v-model="row.keywords_str" placeholder="用逗号分隔" size="small" @blur="updateKeywords(row)" />
                  </template>
                </el-table-column>
                <el-table-column prop="severity" label="严重程度" width="120" align="center">
                  <template #default="{ row }">
                    <el-select v-model="row.severity" size="small">
                      <el-option label="高" value="high" />
                      <el-option label="中" value="medium" />
                      <el-option label="低" value="low" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ $index }">
                    <el-button size="small" type="danger" link @click="deleteErrorRule($index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
          <div v-else class="no-template">
            <el-empty description="请从左侧选择一个模板开始配置" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="预警阈值设置" name="alerts">
          <div v-if="currentTemplate">
            <el-card shadow="hover">
              <el-form :model="currentTemplate.alert_thresholds" label-width="180px">
                <el-form-item label="最低分数线">
                  <el-input-number v-model="currentTemplate.alert_thresholds.min_score" :min="0" :max="100" />
                  <span class="form-tip">低于此分数的学生将被标记为异常</span>
                </el-form-item>
                <el-form-item label="代码完整度阈值">
                  <el-input-number v-model="currentTemplate.alert_thresholds.code_completeness" :min="0" :max="1" :step="0.01" />
                  <span class="form-tip">低于此比例的提交将被标记</span>
                </el-form-item>
                <el-form-item label="低分率阈值">
                  <el-input-number v-model="currentTemplate.alert_thresholds.low_score_rate" :min="0" :max="1" :step="0.01" />
                  <span class="form-tip">班级低分率超过此值将触发预警</span>
                </el-form-item>
                <el-form-item label="启用可疑模式检测">
                  <el-switch v-model="currentTemplate.alert_thresholds.suspicious_pattern" />
                </el-form-item>
              </el-form>
            </el-card>
          </div>
          <div v-else class="no-template">
            <el-empty description="请从左侧选择一个模板开始配置" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="隐私配置" name="privacy">
          <div v-if="currentTemplate">
            <el-card shadow="hover">
              <el-form :model="currentTemplate.privacy_config" label-width="180px">
                <el-form-item label="显示班级能力分布">
                  <el-switch v-model="currentTemplate.privacy_config.show_ability_distribution" />
                </el-form-item>
                <el-form-item label="隐藏学生姓名">
                  <el-switch v-model="currentTemplate.privacy_config.hide_student_name" />
                </el-form-item>
                <el-form-item label="隐藏具体分数">
                  <el-switch v-model="currentTemplate.privacy_config.hide_specific_scores" />
                </el-form-item>
              </el-form>
            </el-card>
          </div>
          <div v-else class="no-template">
            <el-empty description="请从左侧选择一个模板开始配置" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="已应用项目" name="assignments">
          <div v-if="currentTemplate">
            <el-card shadow="hover">
              <template #header>
                <span>已应用的实训项目</span>
              </template>
              <el-table :data="assignments" stripe v-loading="loadingAssignments" style="width: 100%">
                <el-table-column prop="title" label="项目名称" min-width="200" />
                <el-table-column prop="course_name" label="所属课程" width="150" />
                <el-table-column prop="status" label="状态" width="120" align="center">
                  <template #default="{ row }">
                    <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="assigned_at" label="应用时间" width="170" />
                <el-table-column prop="assigned_by" label="操作人" width="120" />
              </el-table>
              <div v-if="!loadingAssignments && !assignments.length" class="empty-hint">该模板尚未应用到任何项目</div>
            </el-card>
          </div>
          <div v-else class="no-template">
            <el-empty description="请从左侧选择一个模板开始配置" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="template-sidebar">
      <div class="sidebar-header">
        <span>模板列表</span>
      </div>
      <div class="template-list">
        <div
          v-for="template in templates"
          :key="template.id"
          class="template-item"
          :class="{ active: currentTemplate?.id === template.id }"
          @click="selectTemplate(template)"
        >
          <div class="template-item-header">
            <span class="template-item-name">{{ template.name }}</span>
            <el-tag v-if="template.is_default" size="small" type="success">默认</el-tag>
          </div>
          <div class="template-item-meta">
            <span>{{ template.indicator_count }}个指标</span>
            <span>{{ template.created_at?.slice(0, 10) }}</span>
          </div>
          <div v-if="currentTemplate?.id === template.id" class="template-item-actions">
            <el-button size="small" @click.stop="openEditDialog">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="handleDelete">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新建模板' : '编辑模板'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="模板名称" required>
          <el-input v-model="form.name" placeholder="例如：软件实训通用评价模板" />
        </el-form-item>
        <el-form-item label="模板说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="说明模板适用范围和评价理念" />
        </el-form-item>
        <el-form-item label="设为默认" v-if="currentUser.role === 'super_admin'">
          <el-switch v-model="form.is_default" />
          <span class="form-tip">设为默认后，新建实训项目将自动使用此模板</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddIndicatorDialog" title="添加评价指标" width="500px">
      <el-form :model="indicatorForm" label-width="100px">
        <el-form-item label="指标名称" required>
          <el-input v-model="indicatorForm.name" placeholder="如：代码质量" />
        </el-form-item>
        <el-form-item label="满分值">
          <el-input-number v-model="indicatorForm.max_score" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="indicatorForm.weight" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="评分依据">
          <el-input v-model="indicatorForm.evaluation_basis" placeholder="评分依据描述" />
        </el-form-item>
        <el-form-item label="评分主体">
          <el-select v-model="indicatorForm.scoring_body">
            <el-option label="AI自动" value="ai" />
            <el-option label="教师手动" value="teacher" />
            <el-option label="AI+教师" value="both" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddIndicatorDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddIndicator">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddCommentDialog" title="添加评语模板" width="500px">
      <el-form :model="commentForm" label-width="100px">
        <el-form-item label="等级标签" required>
          <el-input v-model="commentForm.label" placeholder="如：优秀" />
        </el-form-item>
        <el-form-item label="分数范围">
          <el-input-number v-model="commentForm.min_score" :min="0" :max="100" />
          <span class="range-separator">~</span>
          <el-input-number v-model="commentForm.max_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="评语内容" required>
          <el-input v-model="commentForm.template" type="textarea" :rows="3" placeholder="评语模板内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCommentDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddComment">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddErrorRuleDialog" title="添加错误识别规则" width="500px">
      <el-form :model="errorRuleForm" label-width="100px">
        <el-form-item label="规则名称" required>
          <el-input v-model="errorRuleForm.name" placeholder="如：语法错误" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="errorRuleForm.keywords_str" placeholder="用逗号分隔多个关键词" />
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="errorRuleForm.severity">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddErrorRuleDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddErrorRule">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAssignDialog" title="应用模板到实训项目" width="700px">
      <div class="assign-dialog">
        <el-alert title="选择要应用此评价规则模板的实训项目，应用后将覆盖项目原有的评价配置" type="info" :closable="false" show-icon />
        <el-table ref="assignTable" :data="trainings" stripe v-loading="loadingTrainings" style="width: 100%" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="title" label="项目名称" min-width="200" />
          <el-table-column prop="course_name" label="所属课程" width="150" />
          <el-table-column prop="teacher_name" label="教师" width="120" />
          <el-table-column prop="status" label="状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" :loading="assigning" @click="handleAssign">确认应用</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCopyDialog" title="复制模板" width="500px">
      <el-form :model="copyForm" label-width="100px">
        <el-form-item label="新模板名称" required>
          <el-input v-model="copyForm.name" placeholder="输入新模板名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCopyDialog = false">取消</el-button>
        <el-button type="primary" :loading="copying" @click="handleCopy">复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowDown } from '@element-plus/icons-vue'
import { evaluationAPI, trainingAPI } from '../api'

const currentUser = getCurrentUser()
const loading = ref(false)
const saving = ref(false)
const assigning = ref(false)
const copying = ref(false)
const loadingAssignments = ref(false)
const loadingTrainings = ref(false)

const dialogVisible = ref(false)
const dialogMode = ref('create')
const editingId = ref(null)

const showAddIndicatorDialog = ref(false)
const showAddCommentDialog = ref(false)
const showAddErrorRuleDialog = ref(false)
const showAssignDialog = ref(false)
const showCopyDialog = ref(false)
const assignTable = ref(null)

const activeTab = ref('indicators')
const templates = ref([])
const currentTemplate = ref(null)
const assignments = ref([])
const trainings = ref([])
const selectedTrainings = ref([])

const form = reactive({ name: '', description: '', is_default: false })
const indicatorForm = reactive({ name: '', max_score: 100, weight: 20, evaluation_basis: '', scoring_body: 'ai' })
const commentForm = reactive({ label: '', min_score: 0, max_score: 100, template: '' })
const errorRuleForm = reactive({ name: '', keywords_str: '', severity: 'medium' })
const copyForm = reactive({ name: '' })

const selectedTemplate = computed(() => currentTemplate.value)
const totalWeight = computed(() => {
  if (!currentTemplate.value?.indicators?.length) return 0
  return currentTemplate.value.indicators.reduce((sum, ind) => sum + (ind.weight || 0), 0)
})

const assignedCount = computed(() => assignments.value.length)

function getCurrentUser() {
  try { return JSON.parse(localStorage.getItem('user') || '{}') }
  catch (e) { return {} }
}

function handleSelectionChange(val) {
  selectedTrainings.value = val
}

function resetForm() {
  form.name = ''; form.description = ''; form.is_default = false
}

function openCreateDialog() {
  dialogMode.value = 'create'
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEditDialog() {
  if (!currentTemplate.value) return
  dialogMode.value = 'edit'
  editingId.value = currentTemplate.value.id
  form.name = currentTemplate.value.name
  form.description = currentTemplate.value.description || ''
  form.is_default = Boolean(currentTemplate.value.is_default)
  dialogVisible.value = true
}

function openCopyDialog() {
  if (!currentTemplate.value) return
  copyForm.name = `${currentTemplate.value.name} (副本)`
  showCopyDialog.value = true
}

function openAssignDialog() {
  loadTrainings()
  showAssignDialog.value = true
}

function selectTemplate(template) {
  currentTemplate.value = { ...template }
  loadAssignments(template.id)
}

function getWeightRatio(weight) {
  if (!totalWeight.value) return 0
  return Math.round((weight / totalWeight.value) * 100)
}

function recalcWeight() {}

function editIndicator(row) {
  Object.assign(indicatorForm, {
    name: row.name, max_score: row.max_score, weight: row.weight,
    evaluation_basis: row.evaluation_basis || '', scoring_body: row.scoring_body || 'ai'
  })
  showAddIndicatorDialog.value = true
}

function deleteIndicator(index) {
  ElMessageBox.confirm('确定删除此指标吗？', '确认删除', { type: 'warning' })
    .then(() => {
      currentTemplate.value.indicators.splice(index, 1)
      ElMessage.success('删除成功')
    })
}

const editingParentIndex = ref(null)
const editingChildIndex = ref(null)
const childIndicatorForm = reactive({ name: '', max_score: 100, weight: 20, evaluation_basis: '', scoring_body: 'ai' })

function showAddChildIndicatorDialog(parentRow) {
  editingParentIndex.value = currentTemplate.value.indicators.indexOf(parentRow)
  editingChildIndex.value = null
  Object.assign(childIndicatorForm, { name: '', max_score: 100, weight: 20, evaluation_basis: '', scoring_body: 'ai' })
  showAddIndicatorDialog.value = true
}

function editChildIndicator(row, childIndex) {
  const parentIndex = currentTemplate.value.indicators.findIndex(p => p.children?.includes(row))
  if (parentIndex !== -1) {
    editingParentIndex.value = parentIndex
    editingChildIndex.value = childIndex
    Object.assign(childIndicatorForm, {
      name: row.name, max_score: row.max_score, weight: row.weight,
      evaluation_basis: row.evaluation_basis || '', scoring_body: row.scoring_body || 'ai'
    })
    showAddIndicatorDialog.value = true
  }
}

function deleteChildIndicator(childIndex) {
  if (editingParentIndex.value !== null) {
    ElMessageBox.confirm('确定删除此二级指标吗？', '确认删除', { type: 'warning' })
      .then(() => {
        currentTemplate.value.indicators[editingParentIndex.value].children.splice(childIndex, 1)
        ElMessage.success('删除成功')
      })
  }
}

function handleAddIndicator() {
  if (!indicatorForm.name && !childIndicatorForm.name) return ElMessage.warning('请输入指标名称')
  
  if (editingParentIndex.value !== null) {
    const parent = currentTemplate.value.indicators[editingParentIndex.value]
    if (!parent.children) parent.children = []
    
    if (editingChildIndex.value !== null) {
      parent.children[editingChildIndex.value] = { ...childIndicatorForm }
      ElMessage.success('二级指标更新成功')
    } else {
      parent.children.push({ ...childIndicatorForm })
      ElMessage.success('二级指标添加成功')
    }
    
    Object.assign(childIndicatorForm, { name: '', max_score: 100, weight: 20, evaluation_basis: '', scoring_body: 'ai' })
  } else {
    if (!currentTemplate.value.indicators) currentTemplate.value.indicators = []
    currentTemplate.value.indicators.push({ ...indicatorForm, children: [] })
    Object.assign(indicatorForm, { name: '', max_score: 100, weight: 20, evaluation_basis: '', scoring_body: 'ai' })
    ElMessage.success('一级指标添加成功')
  }
  
  showAddIndicatorDialog.value = false
  editingParentIndex.value = null
  editingChildIndex.value = null
}

function deleteCommentTemplate(index) {
  ElMessageBox.confirm('确定删除此评语模板吗？', '确认删除', { type: 'warning' })
    .then(() => {
      currentTemplate.value.comment_templates.splice(index, 1)
      ElMessage.success('删除成功')
    })
}

function handleAddComment() {
  if (!commentForm.label) return ElMessage.warning('请输入等级标签')
  if (!commentForm.template) return ElMessage.warning('请输入评语内容')
  if (!currentTemplate.value.comment_templates) currentTemplate.value.comment_templates = []
  currentTemplate.value.comment_templates.push({ ...commentForm })
  showAddCommentDialog.value = false
  Object.assign(commentForm, { label: '', min_score: 0, max_score: 100, template: '' })
  ElMessage.success('添加成功')
}

function updateKeywords(row) {
  row.keywords = row.keywords_str.split(',').map(k => k.trim()).filter(k => k)
}

function deleteErrorRule(index) {
  ElMessageBox.confirm('确定删除此规则吗？', '确认删除', { type: 'warning' })
    .then(() => {
      currentTemplate.value.error_rules.splice(index, 1)
      ElMessage.success('删除成功')
    })
}

function handleAddErrorRule() {
  if (!errorRuleForm.name) return ElMessage.warning('请输入规则名称')
  if (!currentTemplate.value.error_rules) currentTemplate.value.error_rules = []
  currentTemplate.value.error_rules.push({
    name: errorRuleForm.name,
    keywords: errorRuleForm.keywords_str.split(',').map(k => k.trim()).filter(k => k),
    keywords_str: errorRuleForm.keywords_str,
    severity: errorRuleForm.severity
  })
  showAddErrorRuleDialog.value = false
  Object.assign(errorRuleForm, { name: '', keywords_str: '', severity: 'medium' })
  ElMessage.success('添加成功')
}

function getStatusType(status) {
  const types = { not_started: 'info', in_progress: 'success', ended: 'warning', archived: 'default' }
  return types[status] || 'default'
}

function getStatusLabel(status) {
  const labels = { not_started: '待开始', in_progress: '进行中', ended: '已截止', archived: '已归档' }
  return labels[status] || status
}

async function loadTemplates() {
  loading.value = true
  try {
    const { data } = await evaluationAPI.templates()
    templates.value = data || []
    if (templates.value.length) selectTemplate(templates.value[0])
  } finally { loading.value = false }
}

async function loadAssignments(templateId) {
  loadingAssignments.value = true
  try {
    const { data } = await evaluationAPI.templateAssignments(templateId)
    assignments.value = data || []
  } catch {
    assignments.value = []
  } finally { loadingAssignments.value = false }
}

async function loadTrainings() {
  loadingTrainings.value = true
  try {
    const { data } = await trainingAPI.list()
    trainings.value = data || []
  } finally { loadingTrainings.value = false }
}

async function handleSubmit() {
  if (!form.name.trim()) return ElMessage.warning('请输入模板名称')
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      description: form.description,
      is_default: form.is_default,
      indicators: currentTemplate.value?.indicators || [],
      comment_templates: currentTemplate.value?.comment_templates || [],
      error_rules: currentTemplate.value?.error_rules || [],
      alert_thresholds: currentTemplate.value?.alert_thresholds || {},
      privacy_config: currentTemplate.value?.privacy_config || {}
    }
    if (dialogMode.value === 'create') {
      await evaluationAPI.createTemplate(payload)
      ElMessage.success('模板创建成功')
    } else {
      await evaluationAPI.updateTemplate(editingId.value, payload)
      ElMessage.success('模板更新成功')
    }
    dialogVisible.value = false
    await loadTemplates()
  } finally { saving.value = false }
}

async function handleDelete() {
  if (!currentTemplate.value) return
  await ElMessageBox.confirm(`确定删除模板“${currentTemplate.value.name}”吗？`, '确认删除', { type: 'warning' })
  await evaluationAPI.deleteTemplate(currentTemplate.value.id)
  ElMessage.success('模板已删除')
  await loadTemplates()
}

async function handleCopy() {
  if (!copyForm.name.trim()) return ElMessage.warning('请输入新模板名称')
  copying.value = true
  try {
    const payload = {
      name: copyForm.name.trim(),
      description: currentTemplate.value.description,
      is_default: false,
      indicators: [...currentTemplate.value.indicators],
      comment_templates: [...currentTemplate.value.comment_templates],
      error_rules: [...currentTemplate.value.error_rules],
      alert_thresholds: { ...currentTemplate.value.alert_thresholds },
      privacy_config: { ...currentTemplate.value.privacy_config }
    }
    await evaluationAPI.createTemplate(payload)
    ElMessage.success('模板复制成功')
    showCopyDialog.value = false
    await loadTemplates()
  } finally { copying.value = false }
}

async function handleAssign() {
  if (!currentTemplate.value) return
  const selectedIds = selectedTrainings.value.map(t => t.id)
  if (!selectedIds.length) return ElMessage.warning('请选择要应用的实训项目')
  assigning.value = true
  try {
    await evaluationAPI.assignTemplate(currentTemplate.value.id, { training_ids: selectedIds })
    ElMessage.success(`成功应用到 ${selectedIds.length} 个实训项目`)
    showAssignDialog.value = false
    await loadAssignments(currentTemplate.value.id)
  } finally { assigning.value = false }
}

function handleTabChange() {
  if (currentTemplate.value && activeTab.value === 'assignments') {
    loadAssignments(currentTemplate.value.id)
  }
}

watch(() => currentTemplate.value?.id, () => {
  if (currentTemplate.value) {
    currentTemplate.value.comment_templates = currentTemplate.value.comment_templates || [
      { min_score: 90, max_score: 100, label: '优秀', template: '该学生表现优秀，代码规范，功能完整，具有较强的创新能力。' },
      { min_score: 80, max_score: 89, label: '良好', template: '该学生表现良好，代码质量较高，功能实现完整，有一定的创新点。' },
      { min_score: 70, max_score: 79, label: '中等', template: '该学生基本完成任务，代码规范有待提高，功能实现基本完整。' },
      { min_score: 60, max_score: 69, label: '及格', template: '该学生勉强完成任务，存在一些问题需要改进。' },
      { min_score: 0, max_score: 59, label: '不及格', template: '该学生未能完成任务，需要加强学习。' }
    ]
    currentTemplate.value.error_rules = currentTemplate.value.error_rules || [
      { name: '语法错误', keywords: ['SyntaxError', 'IndentationError', 'NameError'], keywords_str: 'SyntaxError, IndentationError, NameError', severity: 'high' },
      { name: '逻辑漏洞', keywords: ['SQL注入', '越界访问', '空指针'], keywords_str: 'SQL注入, 越界访问, 空指针', severity: 'high' },
      { name: '代码规范', keywords: ['未使用变量', '硬编码', '魔数'], keywords_str: '未使用变量, 硬编码, 魔数', severity: 'medium' },
      { name: '性能问题', keywords: ['O(n^2)', '重复计算'], keywords_str: 'O(n^2), 重复计算', severity: 'medium' }
    ]
    currentTemplate.value.alert_thresholds = currentTemplate.value.alert_thresholds || {
      min_score: 60, code_completeness: 0.6, low_score_rate: 0.3, suspicious_pattern: true
    }
    currentTemplate.value.privacy_config = currentTemplate.value.privacy_config || {
      show_ability_distribution: true, hide_student_name: false, hide_specific_scores: false
    }
  }
})

onMounted(loadTemplates)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-header h2 { font-size: 22px; color: #303133; margin-bottom: 6px; }
.page-header p { color: #909399; font-size: 13px; }

.header-actions { display: flex; gap: 10px; }

.template-management {
  display: flex;
  gap: 16px;
  height: calc(100vh - 120px);
}

.template-tabs { flex: 1; overflow: hidden; }

.template-sidebar {
  width: 280px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  font-weight: 600;
  border-bottom: 1px solid #ebeef5;
}

.template-list { flex: 1; overflow-y: auto; padding: 8px; }

.template-item {
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.template-item:hover { border-color: #e4e7ed; }
.template-item.active { border-color: #409eff; background: #ecf5ff; }

.template-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.template-item-name { font-weight: 500; font-size: 14px; }
.template-item-meta { display: flex; gap: 12px; font-size: 12px; color: #909399; }
.template-item-actions { display: flex; gap: 6px; margin-top: 8px; }

.primary-indicator { font-weight: 600; font-size: 14px; }
.expand-icon { margin-left: 8px; color: #909399; }
.indent-20 { padding-left: 20px; }

.template-info-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 16px;
}

.template-info-bar .template-name { font-size: 16px; font-weight: 600; }
.template-status { color: #909399; font-size: 13px; }

.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-actions { display: flex; align-items: center; gap: 12px; }
.weight-total { color: #409eff; font-weight: 500; }

.empty-hint { text-align: center; color: #909399; padding: 30px 0; }
.no-template { display: flex; align-items: center; justify-content: center; height: 400px; }

.form-tip { margin-left: 10px; color: #909399; font-size: 12px; }
.range-separator { margin: 0 8px; color: #909399; }

.assign-dialog { max-height: 400px; overflow-y: auto; }
</style>
<template>
  <div class="user-management">
    <template v-if="canAccess">
      <div class="page-header">
        <div>
          <h2>账号权限管理</h2>
          <p>统一维护学生、教师与管理员账号，支持新增、编辑、禁用和删除。</p>
        </div>
        <el-button type="primary" @click="openCreateDialog">新增账号</el-button>
      </div>

      <el-row :gutter="16" class="summary-row">
        <el-col :span="6" v-for="item in summaryCards" :key="item.label">
          <el-card shadow="hover" class="summary-card">
            <div class="summary-value">{{ item.value }}</div>
            <div class="summary-label">{{ item.label }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="hover" class="panel-card">
        <div class="toolbar">
          <div class="toolbar-left">
            <el-select v-model="filters.accountType" placeholder="账号类型" clearable style="width: 160px;">
              <el-option label="管理员" value="admin" />
              <el-option label="教师" value="teacher" />
              <el-option label="学生" value="student" />
            </el-select>
            <el-select v-model="filters.status" placeholder="状态" clearable style="width: 140px;">
              <el-option label="启用" value="1" />
              <el-option label="禁用" value="0" />
            </el-select>
            <el-input v-model="filters.keyword" placeholder="搜索账号、姓名、邮箱、班级" clearable style="width: 280px;" />
          </div>
          <el-button @click="loadUsers" :loading="loading">刷新</el-button>
        </div>

        <el-table :data="filteredUsers" v-loading="loading" stripe border>
          <el-table-column label="类型" width="90">
            <template #default="{ row }">
              <el-tag :type="accountTypeTag(row.account_type)">{{ accountTypeLabel(row.account_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="username" label="账号" width="150" />
          <el-table-column prop="display_name" label="姓名/显示名" width="130" />
          <el-table-column prop="class_name" label="班级" min-width="140" show-overflow-tooltip />
          <el-table-column prop="major" label="专业/部门" min-width="160" show-overflow-tooltip />
          <el-table-column prop="phone" label="电话" width="130" />
          <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
          <el-table-column prop="is_active" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="170" />
          <el-table-column label="操作" width="230" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
              <el-button link :type="row.is_active ? 'warning' : 'success'" @click="handleToggleStatus(row)">
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增账号' : '编辑账号'" width="760px">
        <el-form label-width="110px" :model="form" class="user-form">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="账号类型">
                <el-select v-model="form.account_type" :disabled="dialogMode === 'edit'" style="width: 100%" @change="syncAccountTypeFields">
                  <el-option label="管理员" value="admin" />
                  <el-option label="教师" value="teacher" />
                  <el-option label="学生" value="student" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12" v-if="form.account_type === 'admin'">
              <el-form-item label="管理员角色">
                <el-select v-model="form.role" style="width: 100%">
                  <el-option label="管理员" value="admin" />
                  <el-option label="超级管理员" value="super_admin" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item :label="form.account_type === 'admin' ? '登录用户名' : form.account_type === 'student' ? '学号' : '工号'">
                <el-input v-model="form.username" placeholder="请输入账号" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="姓名/显示名">
                <el-input v-model="form.display_name" placeholder="请输入姓名或显示名" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="16" v-if="form.account_type === 'student'">
            <el-col :span="8">
              <el-form-item label="性别">
                <el-select v-model="form.gender" style="width: 100%">
                  <el-option label="男" value="男" />
                  <el-option label="女" value="女" />
                  <el-option label="其他" value="其他" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="班级">
                <el-input v-model="form.class_name" placeholder="例如：软件2601" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="专业">
                <el-input v-model="form.major" placeholder="请输入专业" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="电话">
                <el-input v-model="form.phone" placeholder="请输入联系电话" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="邮箱">
                <el-input v-model="form.email" placeholder="请输入邮箱" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="密码">
                <el-input v-model="form.password" type="password" show-password :placeholder="dialogMode === 'create' ? '请输入初始密码' : '留空则不修改密码'" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="状态">
                <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
        </template>
      </el-dialog>
    </template>

    <el-result
      v-else
      icon="warning"
      title="无权限访问"
      sub-title="当前登录账号不是超级管理员，暂时无法进入账号权限管理。"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usersAPI } from '../api'

const currentUser = getCurrentUser()
const canAccess = computed(() => currentUser.role === 'super_admin')
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const users = ref([])

const filters = reactive({
  accountType: '',
  status: '',
  keyword: '',
})

const form = reactive(defaultForm())

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch (e) {
    return {}
  }
}

function defaultForm() {
  return {
    id: null,
    account_type: 'teacher',
    username: '',
    display_name: '',
    role: 'teacher',
    gender: '',
    class_name: '',
    major: '',
    phone: '',
    email: '',
    password: '',
    is_active: true,
  }
}

const summaryCards = computed(() => {
  const total = users.value.length
  const adminCount = users.value.filter((item) => item.account_type === 'admin').length
  const teacherCount = users.value.filter((item) => item.account_type === 'teacher').length
  const studentCount = users.value.filter((item) => item.account_type === 'student').length
  return [
    { label: '总账号数', value: total },
    { label: '管理员', value: adminCount },
    { label: '教师', value: teacherCount },
    { label: '学生', value: studentCount },
  ]
})

const filteredUsers = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return users.value.filter((item) => {
    if (filters.accountType && item.account_type !== filters.accountType) return false
    if (filters.status !== '' && String(item.is_active) !== filters.status) return false
    if (!keyword) return true
    return [item.username, item.display_name, item.phone, item.email, item.class_name, item.major]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword))
  })
})

function accountTypeLabel(value) {
  return { admin: '管理员', teacher: '教师', student: '学生' }[value] || value
}

function accountTypeTag(value) {
  return { admin: 'danger', teacher: 'primary', student: 'success' }[value] || 'info'
}

function syncAccountTypeFields() {
  if (form.account_type === 'admin') {
    form.role = 'admin'
    form.gender = ''
    form.class_name = ''
    form.major = ''
  } else if (form.account_type === 'teacher') {
    form.role = 'teacher'
    form.gender = ''
    form.class_name = ''
    form.major = ''
  } else {
    form.role = 'student'
  }
}

function resetForm() {
  Object.assign(form, defaultForm())
}

function openCreateDialog() {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  dialogMode.value = 'edit'
  Object.assign(form, {
    id: row.id,
    account_type: row.account_type,
    username: row.username,
    display_name: row.display_name,
    role: row.role,
    gender: row.gender || '',
    class_name: row.class_name || '',
    major: row.major || '',
    phone: row.phone || '',
    email: row.email || '',
    password: '',
    is_active: Boolean(row.is_active),
  })
  dialogVisible.value = true
}

async function loadUsers() {
  loading.value = true
  try {
    const { data } = await usersAPI.list()
    users.value = data || []
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!form.username.trim()) return ElMessage.warning('请输入账号')
  if (!form.display_name.trim()) return ElMessage.warning('请输入姓名或显示名')
  if (dialogMode.value === 'create' && !form.password.trim()) return ElMessage.warning('请输入初始密码')
  if (form.account_type === 'student' && !form.class_name.trim()) return ElMessage.warning('学生账号需要填写班级')

  const payload = {
    account_type: form.account_type,
    username: form.username.trim(),
    display_name: form.display_name.trim(),
    role: form.account_type === 'admin' ? form.role : form.account_type,
    gender: form.gender,
    class_name: form.class_name,
    major: form.major,
    phone: form.phone,
    email: form.email,
    is_active: form.is_active ? 1 : 0,
  }

  if (form.password.trim()) {
    payload.password = form.password
  }

  saving.value = true
  try {
    if (dialogMode.value === 'create') {
      await usersAPI.create(payload)
      ElMessage.success('账号创建成功')
    } else {
      await usersAPI.update(form.id, payload)
      ElMessage.success('账号更新成功')
    }
    dialogVisible.value = false
    await loadUsers()
  } finally {
    saving.value = false
  }
}

async function handleToggleStatus(row) {
  try {
    await usersAPI.update(row.id, {
      account_type: row.account_type,
      is_active: row.is_active ? 0 : 1,
    })
    ElMessage.success(row.is_active ? '已禁用' : '已启用')
    await loadUsers()
  } catch (e) {
    // handled by interceptor
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除 ${row.display_name} 的账号吗？`, '确认删除', { type: 'warning' })
  await usersAPI.delete(row.id, row.account_type)
  ElMessage.success('账号已删除')
  await loadUsers()
}

onMounted(loadUsers)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 22px;
  color: #303133;
  margin-bottom: 6px;
}

.page-header p {
  color: #909399;
  font-size: 13px;
}

.summary-row {
  margin-bottom: 16px;
}

.summary-card {
  text-align: center;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.summary-label {
  margin-top: 4px;
  color: #909399;
  font-size: 13px;
}

.panel-card {
  margin-top: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.user-form {
  padding-right: 6px;
}
</style>
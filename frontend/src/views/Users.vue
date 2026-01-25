<template>
  <div class="users">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            创建用户
          </el-button>
        </div>
      </template>
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="full_name" label="姓名" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_superuser" label="管理员" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_superuser ? 'warning' : 'info'">
              {{ row.is_superuser ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-button 
              :type="row.is_active ? 'warning' : 'success'" 
              size="small" 
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" size="small" @click="deleteUser(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" :title="editingUser ? '编辑用户' : '创建用户'" width="500px">
      <el-form :model="userForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="userForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="密码" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="userForm.is_superuser" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const users = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const editingUser = ref(null)
const userForm = ref({
  username: '',
  email: '',
  full_name: '',
  password: '',
  is_superuser: false
})

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await api.getUsers()
    users.value = response
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const editUser = (user) => {
  editingUser.value = user
  userForm.value = {
    username: user.username,
    email: user.email,
    full_name: user.full_name,
    password: '',
    is_superuser: user.is_superuser
  }
  showCreateDialog.value = true
}

const saveUser = async () => {
  if (!userForm.value.username || !userForm.value.email) {
    ElMessage.warning('请填写必填信息')
    return
  }

  if (!editingUser.value && !userForm.value.password) {
    ElMessage.warning('请输入密码')
    return
  }

  saving.value = true
  try {
    if (editingUser.value) {
      await api.updateUser(editingUser.value.id, userForm.value)
      ElMessage.success('用户更新成功')
    } else {
      await api.createUser(userForm.value)
      ElMessage.success('用户创建成功')
    }
    showCreateDialog.value = false
    editingUser.value = null
    userForm.value = {
      username: '',
      email: '',
      full_name: '',
      password: '',
      is_superuser: false
    }
    loadUsers()
  } catch (error) {
    ElMessage.error(editingUser.value ? '用户更新失败' : '用户创建失败')
  } finally {
    saving.value = false
  }
}

const toggleUserStatus = async (user) => {
  try {
    await api.updateUser(user.id, {
      is_active: !user.is_active
    })
    ElMessage.success('用户状态更新成功')
    loadUsers()
  } catch (error) {
    ElMessage.error('用户状态更新失败')
  }
}

const deleteUser = async (userId) => {
  try {
    await api.deleteUser(userId)
    ElMessage.success('用户删除成功')
    loadUsers()
  } catch (error) {
    ElMessage.error('用户删除失败')
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.users {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
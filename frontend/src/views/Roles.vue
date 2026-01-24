<template>
  <div class="roles">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            创建角色
          </el-button>
        </div>
      </template>
      <el-table :data="roles" v-loading="loading">
        <el-table-column prop="name" label="角色名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editRole(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="deleteRole(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" :title="editingRole ? '编辑角色' : '创建角色'" width="500px">
      <el-form :model="roleForm" label-width="100px">
        <el-form-item label="角色名称">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="roleForm.description" type="textarea" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRole" :loading="saving">
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

const roles = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const editingRole = ref(null)
const roleForm = ref({
  name: '',
  description: ''
})

const loadRoles = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/v1/roles')
    roles.value = response.data
  } catch (error) {
    ElMessage.error('加载角色列表失败')
  } finally {
    loading.value = false
  }
}

const editRole = (role) => {
  editingRole.value = role
  roleForm.value = {
    name: role.name,
    description: role.description
  }
  showCreateDialog.value = true
}

const saveRole = async () => {
  if (!roleForm.value.name) {
    ElMessage.warning('请输入角色名称')
    return
  }

  saving.value = true
  try {
    if (editingRole.value) {
      await api.put(`/api/v1/roles/${editingRole.value.id}`, roleForm.value)
      ElMessage.success('角色更新成功')
    } else {
      await api.post('/api/v1/roles', roleForm.value)
      ElMessage.success('角色创建成功')
    }
    showCreateDialog.value = false
    editingRole.value = null
    roleForm.value = { name: '', description: '' }
    loadRoles()
  } catch (error) {
    ElMessage.error(editingRole.value ? '角色更新失败' : '角色创建失败')
  } finally {
    saving.value = false
  }
}

const deleteRole = async (roleId) => {
  try {
    await api.delete(`/api/v1/roles/${roleId}`)
    ElMessage.success('角色删除成功')
    loadRoles()
  } catch (error) {
    ElMessage.error('角色删除失败')
  }
}

onMounted(() => {
  loadRoles()
})
</script>

<style scoped>
.roles {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
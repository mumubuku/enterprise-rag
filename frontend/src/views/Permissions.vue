<template>
  <div class="permissions">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>权限管理</span>
          <el-button type="primary" @click="showGrantDialog = true">
            授予权限
          </el-button>
        </div>
      </template>
      <el-table :data="permissions" v-loading="loading">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="permission_type" label="权限类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getPermissionType(row.permission_type)">
              {{ row.permission_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="granted_at" label="授予时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="revokePermission(row)">
              撤销
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showGrantDialog" title="授予权限" width="500px">
      <el-form :model="grantForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="grantForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="权限类型">
          <el-select v-model="grantForm.permission_type" placeholder="请选择权限类型">
            <el-option label="读取" value="read" />
            <el-option label="写入" value="write" />
            <el-option label="删除" value="delete" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGrantDialog = false">取消</el-button>
        <el-button type="primary" @click="grantPermission" :loading="granting">
          授予
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const permissions = ref([])
const loading = ref(false)
const granting = ref(false)
const showGrantDialog = ref(false)
const grantForm = ref({
  username: '',
  permission_type: 'read'
})

const loadPermissions = async () => {
  loading.value = true
  try {
    const response = await api.getPermissions()
    permissions.value = response
  } catch (error) {
    ElMessage.error('加载权限列表失败')
  } finally {
    loading.value = false
  }
}

const grantPermission = async () => {
  if (!grantForm.value.username || !grantForm.value.permission_type) {
    ElMessage.warning('请填写完整信息')
    return
  }

  granting.value = true
  try {
    await api.createPermission(grantForm.value)
    ElMessage.success('权限授予成功')
    showGrantDialog.value = false
    grantForm.value = { username: '', permission_type: 'read' }
    loadPermissions()
  } catch (error) {
    ElMessage.error('权限授予失败')
  } finally {
    granting.value = false
  }
}

const revokePermission = async (permission) => {
  try {
    await api.deletePermission(permission.user_id, permission.permission_type)
    ElMessage.success('权限撤销成功')
    loadPermissions()
  } catch (error) {
    ElMessage.error('权限撤销失败')
  }
}

const getPermissionType = (type) => {
  const types = {
    read: 'info',
    write: 'warning',
    delete: 'danger',
    admin: 'success'
  }
  return types[type] || 'info'
}

onMounted(() => {
  loadPermissions()
})
</script>

<style scoped>
.permissions {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
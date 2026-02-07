<template>
  <div class="profile">
    <el-card>
      <template #header>
        <span>个人中心</span>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="avatar-section">
            <el-avatar :size="120" :src="user.avatar">
              <el-icon :size="60"><User /></el-icon>
            </el-avatar>
            <el-button type="primary" size="small" style="margin-top: 16px;">
              更换头像
            </el-button>
          </div>
        </el-col>
        
        <el-col :span="16">
          <el-form :model="profileForm" label-width="100px">
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" />
            </el-form-item>
            <el-form-item label="姓名">
              <el-input v-model="profileForm.full_name" />
            </el-form-item>
            <el-form-item label="部门">
              <el-select v-model="profileForm.department_id" placeholder="请选择部门" clearable>
                <el-option 
                  v-for="dept in departments" 
                  :key="dept.id" 
                  :label="dept.name" 
                  :value="dept.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updateProfile" :loading="updating">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-col>
      </el-row>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>修改密码</span>
      </template>
      
      <el-form :model="passwordForm" label-width="100px" style="max-width: 500px;">
        <el-form-item label="当前密码">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="changePassword" :loading="changingPassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>操作日志</span>
      </template>
      
      <el-table :data="activityLogs" v-loading="loadingLogs">
        <el-table-column prop="action" label="操作" width="150" />
        <el-table-column prop="description" label="描述" min-width="300" />
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadActivityLogs"
        @current-change="loadActivityLogs"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { authAPI, departmentAPI } from '@/api'

const user = ref({})
const departments = ref([])
const profileForm = ref({
  username: '',
  email: '',
  full_name: '',
  department_id: null
})
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const updating = ref(false)
const changingPassword = ref(false)
const activityLogs = ref([])
const loadingLogs = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0
})

const loadUserProfile = async () => {
  try {
    const currentUser = await authAPI.getCurrentUser()
    user.value = currentUser
    profileForm.value = {
      username: currentUser.username,
      email: currentUser.email,
      full_name: currentUser.full_name || '',
      department_id: currentUser.department_id
    }
  } catch (error) {
    ElMessage.error('加载用户信息失败')
  }
}

const loadDepartments = async () => {
  try {
    departments.value = await departmentAPI.getDepartments()
  } catch (error) {
    ElMessage.error('加载部门列表失败')
  }
}

const updateProfile = async () => {
  if (!profileForm.value.email) {
    ElMessage.warning('请输入邮箱')
    return
  }

  updating.value = true
  try {
    await authAPI.updateUser(user.value.id, {
      email: profileForm.value.email,
      full_name: profileForm.value.full_name,
      department_id: profileForm.value.department_id
    })
    ElMessage.success('个人信息更新成功')
    loadUserProfile()
  } catch (error) {
    ElMessage.error('个人信息更新失败')
  } finally {
    updating.value = false
  }
}

const changePassword = async () => {
  if (!passwordForm.value.old_password) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (!passwordForm.value.new_password) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (passwordForm.value.new_password.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }

  changingPassword.value = true
  try {
    await authAPI.changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    passwordForm.value = {
      old_password: '',
      new_password: '',
      confirm_password: ''
    }
  } catch (error) {
    ElMessage.error('密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

const loadActivityLogs = async () => {
  loadingLogs.value = true
  try {
    const response = await authAPI.getActivityLogs({
      skip: (pagination.value.page - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    })
    activityLogs.value = response.logs || []
    pagination.value.total = response.total || 0
  } catch (error) {
    ElMessage.error('加载操作日志失败')
  } finally {
    loadingLogs.value = false
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(async () => {
  await Promise.all([
    loadUserProfile(),
    loadDepartments(),
    loadActivityLogs()
  ])
})
</script>

<style scoped>
.profile {
  padding: 20px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}
</style>
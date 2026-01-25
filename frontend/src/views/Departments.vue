<template>
  <div class="departments">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>部门管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            创建部门
          </el-button>
        </div>
      </template>
      <el-table :data="departments" v-loading="loading" row-key="id" :tree-props="{ children: 'children', hasChildren: 'hasChildren' }">
        <el-table-column prop="name" label="部门名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="user_count" label="用户数" width="100" align="center" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editDepartment(row)">编辑</el-button>
            <el-button 
              :type="row.is_active ? 'warning' : 'success'" 
              size="small" 
              @click="toggleDepartmentStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" size="small" @click="deleteDepartment(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" :title="editingDepartment ? '编辑部门' : '创建部门'" width="500px">
      <el-form :model="departmentForm" label-width="100px">
        <el-form-item label="部门名称">
          <el-input v-model="departmentForm.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="departmentForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="上级部门">
          <el-select v-model="departmentForm.parent_id" placeholder="请选择上级部门" clearable>
            <el-option 
              v-for="dept in flatDepartments" 
              :key="dept.id" 
              :label="dept.name" 
              :value="dept.id"
              :disabled="editingDepartment && dept.id === editingDepartment.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" v-if="editingDepartment">
          <el-switch v-model="departmentForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDepartment" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { departmentAPI } from '@/api'

const departments = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const editingDepartment = ref(null)
const departmentForm = ref({
  name: '',
  description: '',
  parent_id: null,
  is_active: true
})

const flatDepartments = computed(() => {
  const flatten = (depts) => {
    const result = []
    depts.forEach(dept => {
      result.push(dept)
      if (dept.children && dept.children.length > 0) {
        result.push(...flatten(dept.children))
      }
    })
    return result
  }
  return flatten(departments.value)
})

const loadDepartments = async () => {
  loading.value = true
  try {
    const response = await departmentAPI.getDepartments()
    console.log('部门数据:', response)
    departments.value = buildTree(response)
  } catch (error) {
    console.error('加载部门失败:', error)
    ElMessage.error('加载部门列表失败')
  } finally {
    loading.value = false
  }
}

const buildTree = (flatList) => {
  const map = {}
  const tree = []
  
  flatList.forEach(item => {
    map[item.id] = { ...item, children: [] }
  })
  
  flatList.forEach(item => {
    const node = map[item.id]
    if (item.parent_id && map[item.parent_id]) {
      map[item.parent_id].children.push(node)
    } else {
      tree.push(node)
    }
  })
  
  return tree
}

const editDepartment = (department) => {
  editingDepartment.value = department
  departmentForm.value = {
    name: department.name,
    description: department.description,
    parent_id: department.parent_id,
    is_active: department.is_active
  }
  showCreateDialog.value = true
}

const saveDepartment = async () => {
  if (!departmentForm.value.name) {
    ElMessage.warning('请输入部门名称')
    return
  }

  saving.value = true
  try {
    if (editingDepartment.value) {
      await departmentAPI.updateDepartment(editingDepartment.value.id, departmentForm.value)
      ElMessage.success('部门更新成功')
    } else {
      await departmentAPI.createDepartment(departmentForm.value)
      ElMessage.success('部门创建成功')
    }
    showCreateDialog.value = false
    editingDepartment.value = null
    departmentForm.value = {
      name: '',
      description: '',
      parent_id: null,
      is_active: true
    }
    loadDepartments()
  } catch (error) {
    ElMessage.error(editingDepartment.value ? '部门更新失败' : '部门创建失败')
  } finally {
    saving.value = false
  }
}

const toggleDepartmentStatus = async (department) => {
  try {
    await departmentAPI.updateDepartment(department.id, {
      is_active: !department.is_active
    })
    ElMessage.success('部门状态更新成功')
    loadDepartments()
  } catch (error) {
    ElMessage.error('部门状态更新失败')
  }
}

const deleteDepartment = async (deptId) => {
  try {
    await ElMessageBox.confirm('确定要删除该部门吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await departmentAPI.deleteDepartment(deptId)
    ElMessage.success('部门删除成功')
    loadDepartments()
  } catch {
    if (error !== 'cancel') {
      ElMessage.error('部门删除失败')
    }
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadDepartments()
})
</script>

<style scoped>
.departments {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
<template>
  <div class="knowledge-bases">
    <div class="page-header">
      <h2>知识库管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建知识库
      </el-button>
    </div>
    
    <el-card class="kb-list">
      <el-table :data="kbStore.knowledgeBases" v-loading="kbStore.loading">
        <el-table-column prop="name" label="知识库名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="embedding_model" label="嵌入模型" width="150" />
        <el-table-column prop="llm_model" label="大模型" width="150" />
        <el-table-column prop="document_count" label="文档数" width="100" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">
              查看详情
            </el-button>
            <el-button link type="primary" @click="editKB(row)">
              编辑
            </el-button>
            <el-button link type="danger" @click="deleteKB(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog
      v-model="showCreateDialog"
      :title="editingKB ? '编辑知识库' : '创建知识库'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="嵌入模型" prop="embedding_model">
          <el-select v-model="form.embedding_model" placeholder="请选择嵌入模型">
            <el-option label="OpenAI" value="openai" />
            <el-option label="阿里云" value="alibaba" />
            <el-option label="本地模型" value="local" />
          </el-select>
        </el-form-item>
        <el-form-item label="大模型" prop="llm_model">
          <el-select v-model="form.llm_model" placeholder="请选择大模型">
            <el-option label="OpenAI" value="openai" />
            <el-option label="阿里云" value="alibaba" />
            <el-option label="智谱AI" value="zhipuai" />
          </el-select>
        </el-form-item>
        <el-divider content-position="left">高级配置</el-divider>
        <el-form-item label="分块大小" prop="chunk_size">
          <el-input-number v-model="form.chunk_size" :min="100" :max="5000" :step="100" />
          <span style="margin-left: 8px; color: #999;">字符数</span>
        </el-form-item>
        <el-form-item label="分块重叠" prop="chunk_overlap">
          <el-input-number v-model="form.chunk_overlap" :min="0" :max="1000" :step="50" />
          <span style="margin-left: 8px; color: #999;">字符数</span>
        </el-form-item>
        <el-form-item label="检索数量" prop="retrieval_top_k">
          <el-input-number v-model="form.retrieval_top_k" :min="1" :max="20" :step="1" />
          <span style="margin-left: 8px; color: #999;">返回的相关文档数</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitting">
          {{ editingKB ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'

const router = useRouter()
const kbStore = useKnowledgeBaseStore()

const showCreateDialog = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const editingKB = ref(null)

const form = ref({
  name: '',
  description: '',
  embedding_model: 'openai',
  llm_model: 'openai',
  chunk_size: 1000,
  chunk_overlap: 200,
  retrieval_top_k: 4
})

const rules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' }
  ]
}

onMounted(async () => {
  await fetchKnowledgeBases()
})

async function fetchKnowledgeBases() {
  await kbStore.fetchKnowledgeBases()
}

function viewDetail(kb) {
  kbStore.setCurrentKB(kb)
  router.push(`/knowledge-bases/${kb.id}`)
}

function editKB(kb) {
  editingKB.value = kb
  form.value = {
    name: kb.name,
    description: kb.description,
    embedding_model: kb.embedding_model || 'openai',
    llm_model: kb.llm_model || 'openai',
    chunk_size: kb.chunk_size || 1000,
    chunk_overlap: kb.chunk_overlap || 200,
    retrieval_top_k: kb.retrieval_top_k || 4
  }
  showCreateDialog.value = true
}

async function deleteKB(kb) {
  try {
    await ElMessageBox.confirm(`确定要删除知识库"${kb.name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await kbStore.deleteKnowledgeBase(kb.id)
    ElMessage.success('删除成功')
    await fetchKnowledgeBases()
  } catch {
    // 用户取消
  }
}

async function handleCreate() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (editingKB.value) {
          await kbStore.updateKnowledgeBase(editingKB.value.id, form.value)
          ElMessage.success('更新成功')
        } else {
          await kbStore.createKnowledgeBase(form.value)
          ElMessage.success('创建成功')
        }
        showCreateDialog.value = false
        resetForm()
        await fetchKnowledgeBases()
      } finally {
        submitting.value = false
      }
    }
  })
}

function resetForm() {
  editingKB.value = null
  form.value = {
    name: '',
    description: '',
    embedding_model: 'openai',
    llm_model: 'openai',
    chunk_size: 1000,
    chunk_overlap: 200,
    retrieval_top_k: 4
  }
  formRef.value?.resetFields()
}

function formatDate(date) {
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.knowledge-bases {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.kb-list {
  border-radius: 12px;
}
</style>
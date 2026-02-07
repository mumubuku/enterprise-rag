<template>
  <div class="knowledge-base-detail">
    <el-page-header @back="goBack" :content="knowledgeBaseName">
      <template #extra>
        <el-button @click="showBatchUploadDialog = true">
          <el-icon><FolderAdd /></el-icon>
          批量上传
        </el-button>
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传文档
        </el-button>
      </template>
    </el-page-header>

    <el-divider />

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>文档列表</span>
              <el-button text @click="loadDocuments">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <el-table :data="documents" v-loading="loading">
            <el-table-column prop="file_name" label="文件名" />
            <el-table-column prop="file_type" label="类型" width="100" />
            <el-table-column prop="chunk_count" label="片段数" width="100" />
            <el-table-column prop="created_at" label="上传时间" width="180" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="previewDocument(row)">
                  预览
                </el-button>
                <el-button type="danger" size="small" @click="deleteDocument(row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>知识库信息</span>
              <el-button type="primary" size="small" @click="showEditDialog = true">
                <el-icon><Edit /></el-icon>
                编辑配置
              </el-button>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="名称">
              {{ knowledgeBaseName }}
            </el-descriptions-item>
            <el-descriptions-item label="描述">
              {{ knowledgeBaseDescription }}
            </el-descriptions-item>
            <el-descriptions-item label="文档数">
              {{ documents.length }}
            </el-descriptions-item>
            <el-descriptions-item label="分块大小">
              {{ config.chunk_size }}
            </el-descriptions-item>
            <el-descriptions-item label="分块重叠">
              {{ config.chunk_overlap }}
            </el-descriptions-item>
            <el-descriptions-item label="检索数量">
              {{ config.retrieval_top_k }}
            </el-descriptions-item>
            <el-descriptions-item label="嵌入模型">
              {{ config.embedding_model || '默认' }}
            </el-descriptions-item>
            <el-descriptions-item label="LLM模型">
              {{ config.llm_model || '默认' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showUploadDialog" title="上传文档" width="500px">
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
      </el-upload>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadDocument" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showBatchUploadDialog" title="批量上传文档" width="700px">
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleBatchFileChange"
        :on-remove="handleFileRemove"
        :file-list="batchFileList"
        multiple
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽多个文件到此处或 <em>点击选择</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持批量上传多个文档，系统将依次处理每个文件
          </div>
        </template>
      </el-upload>
      <div v-if="batchUploadProgress.length > 0" class="batch-progress">
        <div class="progress-header">
          <span>上传进度</span>
          <span>{{ batchUploadProgress.filter(p => p.status === 'success').length }}/{{ batchUploadProgress.length }}</span>
        </div>
        <div v-for="item in batchUploadProgress" :key="item.name" class="progress-item">
          <div class="progress-info">
            <span class="file-name">{{ item.name }}</span>
            <el-tag :type="item.status === 'success' ? 'success' : item.status === 'error' ? 'danger' : 'info'" size="small">
              {{ item.status === 'success' ? '成功' : item.status === 'error' ? '失败' : '处理中' }}
            </el-tag>
          </div>
          <el-progress v-if="item.status === 'uploading'" :percentage="item.percentage" :stroke-width="6" />
        </div>
      </div>
      <template #footer>
        <el-button @click="cancelBatchUpload">取消</el-button>
        <el-button type="primary" @click="startBatchUpload" :loading="batchUploading" :disabled="batchFileList.length === 0">
          开始上传 ({{ batchFileList.length }})
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPreviewDialog" title="文档预览" width="80%" top="5vh">
      <div v-if="previewLoading" class="preview-loading">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
      <div v-else-if="previewContent" class="preview-content">
        <div class="preview-header">
          <h3>{{ previewDocumentName }}</h3>
          <el-tag>{{ previewDocumentType }}</el-tag>
        </div>
        <div class="preview-body">
          <pre>{{ previewContent }}</pre>
        </div>
      </div>
      <div v-else class="preview-error">
        <el-icon :size="40"><Warning /></el-icon>
        <p>无法预览此文档</p>
      </div>
      <template #footer>
        <el-button @click="showPreviewDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑知识库配置" width="600px">
      <el-form :model="editForm" label-width="120px">
        <el-form-item label="知识库名称">
          <el-input v-model="editForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="分块大小">
          <el-input-number v-model="editForm.chunk_size" :min="100" :max="4000" :step="100" />
          <span class="form-tip">文档分块的大小（字符数）</span>
        </el-form-item>
        <el-form-item label="分块重叠">
          <el-input-number v-model="editForm.chunk_overlap" :min="0" :max="1000" :step="50" />
          <span class="form-tip">相邻分块之间的重叠字符数</span>
        </el-form-item>
        <el-form-item label="检索数量">
          <el-input-number v-model="editForm.retrieval_top_k" :min="1" :max="20" :step="1" />
          <span class="form-tip">每次检索返回的相关文档片段数量</span>
        </el-form-item>
        <el-form-item label="嵌入模型">
          <el-select v-model="editForm.embedding_model" placeholder="请选择嵌入模型">
            <el-option label="默认" value="" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="阿里云" value="alibaba" />
            <el-option label="本地模型" value="local" />
          </el-select>
        </el-form-item>
        <el-form-item label="LLM模型">
          <el-select v-model="editForm.llm_model" placeholder="请选择LLM模型">
            <el-option label="默认" value="" />
            <el-option label="OpenAI GPT-4" value="gpt-4" />
            <el-option label="OpenAI GPT-3.5" value="gpt-3.5-turbo" />
            <el-option label="阿里云通义千问" value="qwen-turbo" />
            <el-option label="智谱AI" value="glm-4" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, Refresh, UploadFilled, Loading, Warning, Edit, FolderAdd } from '@element-plus/icons-vue'
import { kbAPI } from '@/api'

const route = useRoute()
const router = useRouter()

const kbId = route.params.id
const knowledgeBaseName = ref('')
const knowledgeBaseDescription = ref('')
const documents = ref([])
const loading = ref(false)
const uploading = ref(false)
const batchUploading = ref(false)
const saving = ref(false)
const showUploadDialog = ref(false)
const showEditDialog = ref(false)
const showBatchUploadDialog = ref(false)
const selectedFile = ref(null)
const batchFileList = ref([])
const batchUploadProgress = ref([])
const showPreviewDialog = ref(false)
const previewLoading = ref(false)
const previewContent = ref('')
const previewDocumentName = ref('')
const previewDocumentType = ref('')
const config = ref({
  chunk_size: 1000,
  chunk_overlap: 200,
  retrieval_top_k: 4,
  embedding_model: '',
  llm_model: ''
})
const editForm = ref({
  name: '',
  description: '',
  chunk_size: 1000,
  chunk_overlap: 200,
  retrieval_top_k: 4,
  embedding_model: '',
  llm_model: ''
})

const loadKnowledgeBase = async () => {
  try {
    const knowledgeBase = await kbAPI.getKnowledgeBase(kbId)
    knowledgeBaseName.value = knowledgeBase.name
    knowledgeBaseDescription.value = knowledgeBase.description
    config.value = {
      chunk_size: knowledgeBase.chunk_size || 1000,
      chunk_overlap: knowledgeBase.chunk_overlap || 200,
      retrieval_top_k: knowledgeBase.retrieval_top_k || 4,
      embedding_model: knowledgeBase.embedding_model || '',
      llm_model: knowledgeBase.llm_model || ''
    }
    editForm.value = { ...config.value, name: knowledgeBase.name, description: knowledgeBase.description }
  } catch (error) {
    ElMessage.error('加载知识库信息失败')
  }
}

const loadDocuments = async () => {
  loading.value = true
  try {
    documents.value = await kbAPI.getDocuments(kbId)
  } catch (error) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleBatchFileChange = (file, fileList) => {
  batchFileList.value = fileList
}

const handleFileRemove = (file, fileList) => {
  batchFileList.value = fileList
}

const uploadDocument = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    await kbAPI.uploadDocument(kbId, selectedFile.value)
    ElMessage.success('文档上传成功')
    showUploadDialog.value = false
    loadDocuments()
  } catch (error) {
    ElMessage.error('文档上传失败')
  } finally {
    uploading.value = false
  }
}

const startBatchUpload = async () => {
  if (batchFileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  batchUploading.value = true
  batchUploadProgress.value = batchFileList.value.map(file => ({
    name: file.name,
    status: 'pending',
    percentage: 0
  }))

  let successCount = 0
  let failCount = 0

  for (let i = 0; i < batchFileList.value.length; i++) {
    const file = batchFileList.value[i]
    const progressItem = batchUploadProgress.value[i]
    
    progressItem.status = 'uploading'
    progressItem.percentage = 0

    try {
      await kbAPI.uploadDocument(kbId, file.raw)
      progressItem.status = 'success'
      progressItem.percentage = 100
      successCount++
    } catch (error) {
      progressItem.status = 'error'
      failCount++
    }
  }

  batchUploading.value = false
  loadDocuments()

  if (failCount === 0) {
    ElMessage.success(`成功上传 ${successCount} 个文件`)
  } else if (successCount === 0) {
    ElMessage.error(`上传失败，共 ${failCount} 个文件`)
  } else {
    ElMessage.warning(`上传完成：成功 ${successCount} 个，失败 ${failCount} 个`)
  }

  setTimeout(() => {
    showBatchUploadDialog.value = false
    batchFileList.value = []
    batchUploadProgress.value = []
  }, 2000)
}

const cancelBatchUpload = () => {
  if (batchUploading.value) {
    ElMessage.warning('正在上传中，请稍后...')
    return
  }
  showBatchUploadDialog.value = false
  batchFileList.value = []
  batchUploadProgress.value = []
}

const deleteDocument = async (docId) => {
  try {
    await kbAPI.deleteDocument(docId)
    ElMessage.success('文档删除成功')
    loadDocuments()
  } catch (error) {
    ElMessage.error('文档删除失败')
  }
}

const previewDocument = async (document) => {
  showPreviewDialog.value = true
  previewLoading.value = true
  previewContent.value = ''
  previewDocumentName.value = document.file_name
  previewDocumentType.value = document.file_type

  try {
    const content = await kbAPI.getDocumentContent(document.id)
    previewContent.value = content
  } catch (error) {
    ElMessage.error('加载文档内容失败')
    previewContent.value = ''
  } finally {
    previewLoading.value = false
  }
}

const goBack = () => {
  router.push('/knowledge-bases')
}

const saveConfig = async () => {
  if (!editForm.value.name) {
    ElMessage.warning('请输入知识库名称')
    return
  }

  saving.value = true
  try {
    await kbAPI.updateKnowledgeBase(kbId, editForm.value)
    ElMessage.success('配置保存成功')
    showEditDialog.value = false
    loadKnowledgeBase()
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadKnowledgeBase()
  loadDocuments()
})
</script>

<style scoped>
.knowledge-base-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
}

.preview-loading p {
  margin-top: 16px;
}

.preview-content {
  max-height: 60vh;
  overflow-y: auto;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.preview-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.preview-body {
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.preview-body pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}

.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
}

.preview-error p {
  margin-top: 16px;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.batch-progress {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 500;
  color: #303133;
}

.progress-item {
  margin-bottom: 12px;
  padding: 8px;
  background: white;
  border-radius: 4px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.file-name {
  font-size: 14px;
  color: #606266;
  flex: 1;
  margin-right: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
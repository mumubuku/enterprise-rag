<template>
  <div class="knowledge-base-detail">
    <el-page-header @back="goBack" :content="knowledgeBaseName">
      <template #extra>
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
            <span>知识库信息</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, Refresh, UploadFilled, Loading, Warning } from '@element-plus/icons-vue'
import { kbAPI } from '@/api'

const route = useRoute()
const router = useRouter()

const kbId = route.params.id
const knowledgeBaseName = ref('')
const knowledgeBaseDescription = ref('')
const documents = ref([])
const loading = ref(false)
const uploading = ref(false)
const showUploadDialog = ref(false)
const selectedFile = ref(null)
const showPreviewDialog = ref(false)
const previewLoading = ref(false)
const previewContent = ref('')
const previewDocumentName = ref('')
const previewDocumentType = ref('')

const loadKnowledgeBase = async () => {
  try {
    const knowledgeBase = await kbAPI.getKnowledgeBase(kbId)
    knowledgeBaseName.value = knowledgeBase.name
    knowledgeBaseDescription.value = knowledgeBase.description
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
</style>
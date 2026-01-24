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
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, Refresh, UploadFilled } from '@element-plus/icons-vue'
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
</style>
<template>
  <div class="query-logs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>查询历史</span>
          <div class="header-actions">
            <el-button @click="loadStats">
              <el-icon><Refresh /></el-icon>
              刷新统计
            </el-button>
          </div>
        </div>
      </template>
      
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <el-icon :size="24" color="white"><ChatDotRound /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.total_queries || 0 }}</div>
                <div class="stat-label">总查询次数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <el-icon :size="24" color="white"><Timer /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ (stats.avg_retrieval_time || 0).toFixed(2) }}s</div>
                <div class="stat-label">平均检索时间</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <el-icon :size="24" color="white"><MagicStick /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ (stats.avg_generation_time || 0).toFixed(2) }}s</div>
                <div class="stat-label">平均生成时间</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <el-icon :size="24" color="white"><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ (stats.avg_total_time || 0).toFixed(2) }}s</div>
                <div class="stat-label">平均总时间</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-divider />

      <div class="filter-bar">
        <el-select v-model="filters.knowledge_base_id" placeholder="选择知识库" clearable style="width: 200px; margin-right: 12px;">
          <el-option 
            v-for="kb in knowledgeBases" 
            :key="kb.id" 
            :label="kb.name" 
            :value="kb.id"
          />
        </el-select>
        <el-button type="primary" @click="loadQueryLogs">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
        <el-button @click="resetFilters">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
      </div>

      <el-table :data="queryLogs" v-loading="loading" style="margin-top: 16px;">
        <el-table-column prop="query" label="问题" min-width="300" show-overflow-tooltip />
        <el-table-column prop="answer" label="回答" min-width="400" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="answer-text">{{ row.answer }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="user_name" label="用户" width="120" />
        <el-table-column prop="knowledge_base_name" label="知识库" width="150" />
        <el-table-column prop="retrieval_count" label="检索数" width="80" align="center" />
        <el-table-column prop="total_time" label="总耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.total_time ? `${row.total_time.toFixed(2)}s` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="查询时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadQueryLogs"
        @current-change="loadQueryLogs"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-card>

    <el-dialog v-model="showDetailDialog" title="查询详情" width="800px">
      <el-descriptions :column="2" border v-if="selectedLog">
        <el-descriptions-item label="问题" :span="2">{{ selectedLog.query }}</el-descriptions-item>
        <el-descriptions-item label="回答" :span="2">
          <div class="answer-detail">{{ selectedLog.answer }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="用户">{{ selectedLog.user_name }}</el-descriptions-item>
        <el-descriptions-item label="知识库">{{ selectedLog.knowledge_base_name }}</el-descriptions-item>
        <el-descriptions-item label="检索数量">{{ selectedLog.retrieval_count }}</el-descriptions-item>
        <el-descriptions-item label="检索时间">{{ selectedLog.retrieval_time ? `${selectedLog.retrieval_time.toFixed(3)}s` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="生成时间">{{ selectedLog.generation_time ? `${selectedLog.generation_time.toFixed(3)}s` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="总耗时">{{ selectedLog.total_time ? `${selectedLog.total_time.toFixed(3)}s` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="查询时间" :span="2">{{ formatDate(selectedLog.created_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search, RefreshLeft, ChatDotRound, Timer, MagicStick, Clock } from '@element-plus/icons-vue'
import { queryLogAPI, kbAPI } from '@/api'

const queryLogs = ref([])
const knowledgeBases = ref([])
const loading = ref(false)
const showDetailDialog = ref(false)
const selectedLog = ref(null)
const stats = ref({
  total_queries: 0,
  avg_retrieval_time: 0,
  avg_generation_time: 0,
  avg_total_time: 0
})

const filters = ref({
  knowledge_base_id: null
})

const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const loadStats = async () => {
  try {
    const response = await queryLogAPI.getQueryLogStats()
    stats.value = response
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  }
}

const loadKnowledgeBases = async () => {
  try {
    const response = await kbAPI.getKnowledgeBases()
    knowledgeBases.value = response
  } catch (error) {
    ElMessage.error('加载知识库列表失败')
  }
}

const loadQueryLogs = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.page - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize,
      ...filters.value
    }
    const response = await queryLogAPI.getQueryLogs(params)
    queryLogs.value = response
    pagination.value.total = response.length
  } catch (error) {
    ElMessage.error('加载查询日志失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    knowledge_base_id: null
  }
  pagination.value.page = 1
  loadQueryLogs()
}

const viewDetail = (log) => {
  selectedLog.value = log
  showDetailDialog.value = true
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(async () => {
  await Promise.all([
    loadStats(),
    loadKnowledgeBases(),
    loadQueryLogs()
  ])
})
</script>

<style scoped>
.query-logs {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.filter-bar {
  display: flex;
  align-items: center;
}

.answer-text {
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.answer-detail {
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
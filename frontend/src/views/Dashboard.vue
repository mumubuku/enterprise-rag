<template>
  <div class="dashboard">
    <el-row :gutter="24">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
              <el-icon :size="32" color="white"><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_knowledge_bases || 0 }}</div>
              <div class="stat-label">知识库总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
              <el-icon :size="32" color="white"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_documents || 0 }}</div>
              <div class="stat-label">文档总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
              <el-icon :size="32" color="white"><Reading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_chunks || 0 }}</div>
              <div class="stat-label">文档片段</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
              <el-icon :size="32" color="white"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_queries || 0 }}</div>
              <div class="stat-label">查询次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="24" style="margin-top: 24px;">
      <el-col :span="12">
        <el-card class="welcome-card">
          <template #header>
            <div class="card-header">
              <span>欢迎使用企业RAG知识库</span>
            </div>
          </template>
          <div class="welcome-content">
            <p>企业RAG知识库是一个智能的知识管理和问答系统，帮助企业高效管理和利用知识资产。</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon color="#667eea"><Check /></el-icon>
                <span>支持多种文档格式</span>
              </div>
              <div class="feature-item">
                <el-icon color="#667eea"><Check /></el-icon>
                <span>智能向量检索</span>
              </div>
              <div class="feature-item">
                <el-icon color="#667eea"><Check /></el-icon>
                <span>AI智能问答</span>
              </div>
              <div class="feature-item">
                <el-icon color="#667eea"><Check /></el-icon>
                <span>细粒度权限控制</span>
              </div>
            </div>
            <el-button type="primary" @click="$router.push('/knowledge-bases')">
              开始使用
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="quick-actions-card">
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <div class="action-item" @click="$router.push('/knowledge-bases')">
              <div class="action-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <el-icon :size="24" color="white"><Plus /></el-icon>
              </div>
              <span>创建知识库</span>
            </div>
            <div class="action-item" @click="$router.push('/chat')">
              <div class="action-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <el-icon :size="24" color="white"><ChatDotRound /></el-icon>
              </div>
              <span>智能问答</span>
            </div>
            <div class="action-item" @click="$router.push('/knowledge-bases')">
              <div class="action-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <el-icon :size="24" color="white"><Upload /></el-icon>
              </div>
              <span>上传文档</span>
            </div>
            <div class="action-item" @click="$router.push('/users')">
              <div class="action-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <el-icon :size="24" color="white"><User /></el-icon>
              </div>
              <span>用户管理</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ragAPI } from '@/api'
import {
  FolderOpened,
  Document,
  Reading,
  ChatDotRound,
  Check,
  Plus,
  Upload,
  User
} from '@element-plus/icons-vue'

const stats = ref({
  total_knowledge_bases: 0,
  total_documents: 0,
  total_chunks: 0,
  total_queries: 0
})

onMounted(async () => {
  try {
    stats.value = await ragAPI.getStats()
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stat-card {
  border-radius: 12px;
  overflow: hidden;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.welcome-card,
.quick-actions-card {
  border-radius: 12px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.welcome-content p {
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
}

.feature-list {
  margin-bottom: 24px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #666;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  background: #f5f7fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-item:hover {
  background: #e8eaf0;
  transform: translateY(-2px);
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-item span {
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 500;
}
</style>
<template>
  <div class="chat">
    <div class="chat-container">
      <div class="chat-sidebar">
        <div class="sidebar-header">
          <h3>知识库选择</h3>
        </div>
        <div class="kb-list">
          <div
            v-for="kb in knowledgeBases"
            :key="kb.id"
            class="kb-item"
            :class="{ active: selectedKB?.id === kb.id }"
            @click="selectKB(kb)"
          >
            <el-icon><FolderOpened /></el-icon>
            <span>{{ kb.name }}</span>
          </div>
        </div>
      </div>
      
      <div class="chat-main">
        <div class="chat-header">
          <h3>{{ selectedKB?.name || '请选择知识库' }}</h3>
        </div>
        
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <el-icon :size="64" color="#d9d9d9"><ChatDotRound /></el-icon>
            <p>开始提问吧！</p>
          </div>
          
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="message"
            :class="message.role"
          >
            <div class="message-avatar">
              <el-icon v-if="message.role === 'user'" :size="24"><User /></el-icon>
              <el-icon v-else :size="24"><Service /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div v-if="message.sources && message.sources.length > 0" class="message-sources">
                <div class="sources-title">参考来源：</div>
                <div
                  v-for="(source, idx) in message.sources"
                  :key="idx"
                  class="source-item"
                >
                  <el-icon><Document /></el-icon>
                  <span>{{ source.metadata?.file_name || '未知文档' }}</span>
                  <span class="source-score">相似度: {{ (source.score * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="loading" class="message assistant">
            <div class="message-avatar">
              <el-icon :size="24"><Service /></el-icon>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="chat-input">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题..."
            :disabled="!selectedKB || loading"
            @keydown.ctrl.enter="sendMessage"
          />
          <el-button
            type="primary"
            :disabled="!selectedKB || loading || !inputMessage.trim()"
            @click="sendMessage"
          >
            <el-icon><Promotion /></el-icon>
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { FolderOpened, User, Service, Document, Promotion, ChatDotRound } from '@element-plus/icons-vue'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import { ragAPI } from '@/api'

const kbStore = useKnowledgeBaseStore()

const knowledgeBases = ref([])
const selectedKB = ref(null)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

onMounted(async () => {
  await fetchKnowledgeBases()
})

async function fetchKnowledgeBases() {
  try {
    await kbStore.fetchKnowledgeBases()
    knowledgeBases.value = kbStore.knowledgeBases
    if (knowledgeBases.value.length > 0) {
      selectKB(knowledgeBases.value[0])
    }
  } catch (error) {
    console.error('Failed to fetch knowledge bases:', error)
    ElMessage.error('获取知识库失败，请检查网络连接')
  }
}

function selectKB(kb) {
  selectedKB.value = kb
  messages.value = []
}

async function sendMessage() {
  if (!inputMessage.value.trim() || !selectedKB.value) return
  
  const userMessage = inputMessage.value.trim()
  messages.value.push({
    role: 'user',
    content: userMessage
  })
  
  inputMessage.value = ''
  loading.value = true
  
  await scrollToBottom()
  
  try {
    const response = await ragAPI.questionAnswer({
      question: userMessage,
      knowledge_base_id: selectedKB.value.id,
      top_k: 4
    })
    
    messages.value.push({
      role: 'assistant',
      content: response.answer,
      sources: response.sources
    })
  } catch (error) {
    console.error('Failed to get answer:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，回答问题时出现错误，请稍后重试。'
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.chat {
  height: calc(100vh - 120px);
}

.chat-container {
  display: flex;
  height: 100%;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.chat-sidebar {
  width: 280px;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.kb-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.kb-item:hover {
  background: #f5f7fa;
}

.kb-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.kb-item span {
  font-size: 14px;
  font-weight: 500;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.chat-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.empty-state p {
  margin-top: 16px;
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-content {
  max-width: 70%;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  background: #f5f7fa;
  color: #1a1a1a;
  line-height: 1.6;
  word-wrap: break-word;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-sources {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.sources-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.source-score {
  margin-left: auto;
  color: #667eea;
  font-weight: 500;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 12px;
  width: fit-content;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #999;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #e8e8e8;
}

.chat-input .el-textarea {
  flex: 1;
}

.chat-input .el-button {
  height: auto;
  align-self: flex-end;
}
</style>
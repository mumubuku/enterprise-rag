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
              <div v-if="message.role === 'user'" class="message-text">{{ message.content }}</div>
              <MarkdownRenderer v-else :content="message.content" />
              <div v-if="message.sources && message.sources.length > 0" class="message-sources">
                <div class="sources-title">参考来源：</div>
                <div
                  v-for="(source, idx) in mergeSources(message.sources)"
                  :key="idx"
                  class="source-item"
                >
                  <el-icon><Document /></el-icon>
                  <span>{{ source.fileName }}</span>
                  <span v-if="source.pages.length > 0" class="source-pages">
                    第{{ formatPages(source.pages) }}页
                  </span>
                  <span class="source-score">相似度: {{ Math.min(100, source.maxScore * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="chat-input">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题... (Enter发送，Shift+Enter换行)"
            :disabled="!selectedKB || loading"
            @keydown.enter.prevent="handleEnterKey"
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
import { ref, onMounted, nextTick, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { FolderOpened, User, Service, Document, Promotion, ChatDotRound } from '@element-plus/icons-vue'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import { ragAPI } from '@/api'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

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
  loadChatHistory(kb.id)
}

async function loadChatHistory(kbId) {
  try {
    const history = await ragAPI.getChatHistory(kbId, 7)
    messages.value = []
    
    const reversedHistory = [...history].reverse()
    
    for (const log of reversedHistory) {
      messages.value.push({
        role: 'user',
        content: log.query
      })
      if (log.answer) {
        messages.value.push({
          role: 'assistant',
          content: log.answer,
          sources: log.sources || []
        })
      }
    }
    
    await nextTick()
    await scrollToBottom()
  } catch (error) {
    console.error('Failed to load chat history:', error)
    messages.value = []
  }
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
    const conversationHistory = messages.value.slice(-6).map(msg => ({
      role: msg.role,
      content: msg.content
    }))
    
    const assistantMessage = reactive({
      role: 'assistant',
      content: '',
      sources: []
    })
    
    messages.value.push(assistantMessage)
    
    await scrollToBottom()
    
    ragAPI.questionAnswerStream({
      question: userMessage,
      knowledge_base_id: selectedKB.value.id,
      top_k: 4,
      conversation_history: conversationHistory
    }, (chunk) => {
      console.log('Received chunk in Chat:', chunk)
      if (chunk.answer) {
        assistantMessage.content = chunk.answer
      }
      if (chunk.sources) {
        console.log('Updating sources:', chunk.sources)
        assistantMessage.sources = chunk.sources
      }
      scrollToBottom()
    }, () => {
      console.log('Stream completed in Chat')
      loading.value = false
    }, (error) => {
      console.error('Stream error in Chat:', error)
      assistantMessage.content = '抱歉，回答问题时出现错误，请稍后重试。'
      loading.value = false
    })
  } catch (error) {
    console.error('Failed to get answer:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，回答问题时出现错误，请稍后重试。'
    })
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

function handleEnterKey(event) {
  if (event.shiftKey) {
    return
  }
  sendMessage()
}

function formatPages(pages) {
  if (pages.length === 0) return ''
  if (pages.length === 1) return pages[0]
  
  const sorted = [...pages].sort((a, b) => a - b)
  const ranges = []
  let start = sorted[0]
  let end = sorted[0]
  
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] === end + 1) {
      end = sorted[i]
    } else {
      ranges.push(start === end ? `${start}` : `${start}-${end}`)
      start = sorted[i]
      end = sorted[i]
    }
  }
  ranges.push(start === end ? `${start}` : `${start}-${end}`)
  
  return ranges.join('、')
}

function mergeSources(sources) {
  console.log('mergeSources called with:', sources)
  if (!sources || sources.length === 0) return []
  
  const merged = {}
  
  sources.forEach(source => {
    const fileName = source.metadata?.file_name || '未知文档'
    console.log('Processing source:', source, 'fileName:', fileName)
    const page = source.metadata?.page
    const chunkIndex = source.metadata?.chunk_index
    
    if (!merged[fileName]) {
      merged[fileName] = {
        fileName,
        pages: new Set(),
        scores: [],
        maxScore: 0
      }
    }
    
    if (page !== undefined) {
      merged[fileName].pages.add(page + 1)
    }
    
    merged[fileName].scores.push(source.score)
    merged[fileName].maxScore = Math.max(merged[fileName].maxScore, source.score)
  })
  
  const result = Object.values(merged).map(item => ({
    fileName: item.fileName,
    pages: Array.from(item.pages).sort((a, b) => a - b),
    maxScore: item.maxScore,
    avgScore: item.scores.reduce((sum, score) => sum + score, 0) / item.scores.length
  }))
  
  console.log('mergeSources result:', result)
  return result
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

.message.assistant :deep(.markdown-content) {
  padding: 12px 16px;
  border-radius: 12px;
  background: #ffffff;
  color: #1a1a1a;
  line-height: 1.6;
  word-wrap: break-word;
  border: 1px solid #e8e8e8;
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

.source-pages {
  background: #e8f4ff;
  color: #667eea;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
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
<template>
  <div class="chat-page">
    <!-- 顶部导航栏 -->
    <div class="chat-header">
      <div class="header-content">
        <h1 class="chat-title">
          <i class="fas fa-robot"></i>
          AI 智能助手
        </h1>
        <div class="header-actions">
          <button @click="toggleSidebar" class="btn-sidebar">
            <i class="fas fa-bars"></i>
          </button>
        </div>
      </div>
    </div>

    <div class="chat-container" @click="handleContainerClick">
      <!-- 侧边栏 -->
      <div class="sidebar" :class="{ 'sidebar-open': sidebarOpen }" @click.stop>
        <div class="sidebar-content">
          <div class="conversation-list">
            <h3 class="conversation-title-header">
              <i class="fas fa-history"></i>
              对话历史
            </h3>
            <div class="conversation-item" 
                 v-for="conversation in conversations" 
                 :key="conversation.id"
                 :class="{ active: currentConversationId === conversation.id }"
                 @click="switchConversation(conversation.id)">
              <div class="conversation-content">
                <div class="conversation-title">{{ conversation.title }}</div>
                <div class="conversation-time">{{ formatTime(conversation.updatedAt) }}</div>
              </div>
              <button 
                class="btn-delete-conversation"
                @click.stop="deleteConversation(conversation.id)"
                title="删除对话">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
          <button @click="newConversation" class="btn-new-chat">
            <i class="fas fa-plus"></i>
            新建对话
          </button>
        </div>
      </div>

      <!-- 主聊天区域 - 居中显示 -->
      <div class="chat-main-wrapper">
        <div class="chat-main">
        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <div class="empty-icon">
              <i class="fas fa-comments"></i>
            </div>
            <h3>开始新的对话</h3>
            <p>你可以直接输入问题，或者上传文件进行分析</p>
            <div class="quick-actions">
              <button @click="sendQuickMessage('帮我分析一下这个文档')" class="quick-btn">
                文档分析
              </button>
              <button @click="sendQuickMessage('总结一下主要内容')" class="quick-btn">
                内容总结
              </button>
              <button @click="sendQuickMessage('有什么建议吗？')" class="quick-btn">
                获取建议
              </button>
            </div>
            <!-- 输入区域 - 在文档分析按钮下方 -->
            <div class="input-container-empty">
              <div class="input-wrapper">
                <!-- 文件上传区域 -->
                <div v-if="showFileUpload" class="file-upload-area">
                  <div class="upload-zone" 
                       @drop="handleFileDrop" 
                       @dragover.prevent 
                       @dragenter.prevent
                       :class="{ 'drag-over': isDragOver }"
                       @dragenter="isDragOver = true"
                       @dragleave="isDragOver = false">
                    <i class="fas fa-cloud-upload-alt"></i>
                    <p>拖拽文件到此处，或点击选择文件</p>
                    <input 
                      type="file" 
                      ref="fileInput" 
                      @change="handleFileSelect" 
                      multiple 
                      accept=".pdf,.doc,.docx,.txt,.md">
                    <button @click="() => fileInput?.click()" class="btn-select-file">
                      选择文件
                    </button>
                  </div>
                  <div v-if="selectedFiles.length > 0" class="selected-files">
                    <div v-for="file in selectedFiles" :key="file.name" class="file-item">
                      <i class="fas fa-file"></i>
                      <span>{{ file.name }}</span>
                      <button @click="removeFile(file)" class="btn-remove">
                        <i class="fas fa-times"></i>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- 文本输入区域 -->
                <div class="text-input-area">
                  <textarea 
                    v-model="inputMessage" 
                    @keydown="handleKeyDown"
                    placeholder="输入你的问题..."
                    rows="1"
                    ref="messageInput"
                    class="message-input">
                  </textarea>
                  <div class="input-actions">
                    <button @click="toggleFileUpload" class="btn-attach" :class="{ active: showFileUpload }">
                      <i class="fas fa-paperclip"></i>
                    </button>
                    <button @click="sendMessage" :disabled="!canSend" class="btn-send">
                      <i class="fas fa-paper-plane"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <transition-group name="message-fade" tag="div">
            <template v-for="item in displayItems" :key="item.key">
              <div v-if="item.type === 'separator'" class="time-separator">
                <span>{{ item.label }}</span>
              </div>
              <div v-else class="message" :class="item.message.role">
                <div class="message-avatar">
                  <i v-if="item.message.role === 'user'" class="fas fa-user"></i>
                  <i v-else class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                  <div class="message-text" v-html="formatMessage(item.message.content)"></div>
                  <div class="message-time">{{ formatTime(item.message.timestamp) }}</div>
                  <div v-if="item.message.attachments && item.message.attachments.length > 0" class="message-attachments">
                    <div v-for="attachment in item.message.attachments" :key="attachment.id" class="attachment">
                      <i class="fas fa-file"></i>
                      <span>{{ attachment.name }}</span>
                      <button @click="downloadAttachment(attachment)" class="btn-download">
                        <i class="fas fa-download"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </transition-group>

          <!-- 加载状态 -->
          <div v-if="isLoading" class="message assistant">
            <div class="message-avatar">
              <i class="fas fa-robot"></i>
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

        <!-- 输入区域 - 有消息时显示 -->
        <div v-if="messages.length > 0" class="input-container has-messages">
          <div class="input-wrapper">
            <!-- 文件上传区域 -->
            <div v-if="showFileUpload" class="file-upload-area">
              <div class="upload-zone" 
                   @drop="handleFileDrop" 
                   @dragover.prevent 
                   @dragenter.prevent
                   :class="{ 'drag-over': isDragOver }"
                   @dragenter="isDragOver = true"
                   @dragleave="isDragOver = false">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>拖拽文件到此处，或点击选择文件</p>
                <input 
                  type="file" 
                  ref="fileInput" 
                  @change="handleFileSelect" 
                  multiple 
                  accept=".pdf,.doc,.docx,.txt,.md">
                <button @click="() => fileInput?.click()" class="btn-select-file">
                  选择文件
                </button>
              </div>
              <div v-if="selectedFiles.length > 0" class="selected-files">
                <div v-for="file in selectedFiles" :key="file.name" class="file-item">
                  <i class="fas fa-file"></i>
                  <span>{{ file.name }}</span>
                  <button @click="removeFile(file)" class="btn-remove">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- 文本输入区域 -->
            <div class="text-input-area">
              <textarea 
                v-model="inputMessage" 
                @keydown="handleKeyDown"
                placeholder="输入你的问题..."
                rows="1"
                ref="messageInput"
                class="message-input">
              </textarea>
              <div class="input-actions">
                <button @click="toggleFileUpload" class="btn-attach" :class="{ active: showFileUpload }">
                  <i class="fas fa-paperclip"></i>
                </button>
                <button @click="sendMessage" :disabled="!canSend" class="btn-send">
                  <i class="fas fa-paper-plane"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/store/chatStore'
import type { Message, Attachment } from '@/types/chat'

// Store
const chatStore = useChatStore()

// 响应式数据
const sidebarOpen = ref(true)
const inputMessage = ref('')
const showFileUpload = ref(false)
const isDragOver = ref(false)
const selectedFiles = ref<File[]>([])
const messagesContainer = ref<HTMLElement>()
const messageInput = ref<HTMLTextAreaElement>()
const fileInput = ref<HTMLInputElement>()

// 计算属性
const messages = computed(() => chatStore.currentMessages)

type DisplaySeparator = { type: 'separator'; key: string; label: string }
type DisplayMessage = { type: 'message'; key: string; message: Message }
type DisplayItem = DisplaySeparator | DisplayMessage

const displayItems = computed<DisplayItem[]>(() => {
  const items: DisplayItem[] = []
  let lastSeparator = ''
  let lastTimestamp = 0

  for (const msg of messages.value) {
    const date = new Date(msg.timestamp)
    const separator = `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`

    // 日期切换分割
    if (separator !== lastSeparator) {
      items.push({
        type: 'separator',
        key: `sep-${separator}`,
        label: formatSeparatorLabel(date)
      })
      lastSeparator = separator
      lastTimestamp = msg.timestamp
    } else {
      // 同一日内，超过30分钟也插入时间分割
      if (msg.timestamp - lastTimestamp > 30 * 60 * 1000) {
        items.push({
          type: 'separator',
          key: `sep-${msg.timestamp}`,
          label: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        })
        lastTimestamp = msg.timestamp
      }
    }

    items.push({ type: 'message', key: String(msg.id), message: msg })
  }

  return items
})

const formatSeparatorLabel = (date: Date) => {
  const now = new Date()
  const sameDay = date.toDateString() === now.toDateString()
  if (sameDay) return '今天'

  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) return '昨天'

  return date.toLocaleDateString()
}
const conversations = computed(() => chatStore.conversations)
const currentConversationId = computed(() => chatStore.currentConversationId)
const isLoading = computed(() => chatStore.isLoading)

const canSend = computed(() => {
  return !!inputMessage.value.trim() || selectedFiles.value.length > 0
})

// 方法
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

// 点击遮罩层关闭侧边栏（移动端）
const handleContainerClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  // 如果点击的是遮罩层（通过::after伪元素实现，需要特殊处理）
  // 在移动端，点击容器非侧边栏区域时关闭侧边栏
  if (sidebarOpen.value && window.innerWidth <= 768) {
    if (!target.closest('.sidebar')) {
      sidebarOpen.value = false
    }
  }
}

const newConversation = () => {
  chatStore.createNewConversation()
  sidebarOpen.value = false
}

const switchConversation = (conversationId: string) => {
  chatStore.switchConversation(conversationId)
  sidebarOpen.value = false
}

const deleteConversation = async (conversationId: string) => {
  if (confirm('确定要删除这个对话吗？删除后无法恢复。')) {
    try {
      await chatStore.deleteConversation(conversationId)
    } catch (error) {
      console.error('删除对话失败:', error)
    }
  }
}

const sendMessage = async () => {
  if (!canSend.value) return

  const message = inputMessage.value.trim()
  const attachments = selectedFiles.value.map(file => ({
    id: Date.now().toString(),
    name: file.name,
    type: file.type,
    size: file.size,
    file: file
  }))

  // 先清空输入，立即反馈到UI
  inputMessage.value = ''
  selectedFiles.value = []
  showFileUpload.value = false

  // 重置输入框高度
  await nextTick()
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
  }

  // 触发发送（store 会立刻把用户消息 push 进去，气泡即时出现）
  // 不等待完成，避免阻塞 UI
  void chatStore.sendMessage(message, attachments)

  // 滚动到底部
  await nextTick()
  scrollToBottom()
}

const sendQuickMessage = async (message: string) => {
  inputMessage.value = message
  await sendMessage()
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const toggleFileUpload = () => {
  showFileUpload.value = !showFileUpload.value
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    selectedFiles.value.push(...Array.from(target.files))
  }
}

const handleFileDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  if (event.dataTransfer?.files) {
    selectedFiles.value.push(...Array.from(event.dataTransfer.files))
  }
}

const removeFile = (file: File) => {
  const index = selectedFiles.value.indexOf(file)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
  }
}

const downloadAttachment = (attachment: Attachment) => {
  // 实现文件下载逻辑
  console.log('下载附件:', attachment)
}

const formatMessage = (content: string) => {
  // 简单的markdown渲染
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleDateString()
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动
watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

// 自动调整输入框高度
watch(inputMessage, () => {
  nextTick(() => {
    if (messageInput.value) {
      messageInput.value.style.height = 'auto'
      messageInput.value.style.height = messageInput.value.scrollHeight + 'px'
    }
  })
})

onMounted(async () => {
  try {
    // 初始化聊天
    await chatStore.initializeChat()
  } catch (error) {
    console.warn('初始化聊天失败，可能是后端服务未启动:', error)
    // 不阻止页面渲染，只是显示警告
  }
})
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  position: relative;
  overflow: hidden;
}

.chat-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.chat-header {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 1rem 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 20;
  transition: all 0.3s ease;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.chat-title i {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 1.75rem;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-clear, .btn-sidebar {
  padding: 0.625rem 1.25rem;
  border: 1px solid rgba(102, 126, 234, 0.2);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  color: #4a5568;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.btn-clear:hover, .btn-sidebar:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.btn-clear:active, .btn-sidebar:active {
  transform: translateY(0) scale(0.98);
}

.chat-container {
  flex: 1;
  display: flex;
  width: 100%;
  height: calc(100vh - 64px);
  position: relative;
  z-index: 1;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  position: fixed;
  left: 0;
  top: 64px;
  bottom: 0;
  transform: translateX(-100%);
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 10;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
}

.sidebar-open {
  transform: translateX(0);
}

/* 侧边栏打开时的遮罩层 */
.chat-container::after {
  content: '';
  display: none;
}

.chat-main-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  width: 100%;
  height: 100%;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 桌面端：侧边栏打开时，对话区域不需要偏移，因为侧边栏是fixed定位，不占用布局空间 */

.sidebar-content {
  padding: 1rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.conversation-list h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.1rem;
}

.conversation-title-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  font-weight: 600;
  color: #4a5568;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 1rem !important;
}

.conversation-title-header i {
  color: #667eea;
  font-size: 1rem;
}

.conversation-item {
  padding: 1rem;
  border-radius: 12px;
  cursor: pointer;
  margin-bottom: 0.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid transparent;
}

.conversation-item:hover {
  background: rgba(102, 126, 234, 0.08);
  transform: translateX(4px);
  border-color: rgba(102, 126, 234, 0.2);
}

.conversation-item.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  color: #667eea;
  border-color: rgba(102, 126, 234, 0.3);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.conversation-item.active::before {
  content: '';
  position: absolute;
  left: -1rem;
  top: 0.5rem;
  bottom: 0.5rem;
  width: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.conversation-content {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-weight: 500;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-time {
  font-size: 0.8rem;
  color: #666;
}

.btn-delete-conversation {
  padding: 0.25rem 0.5rem;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #999;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  flex-shrink: 0;
}

.conversation-item:hover .btn-delete-conversation {
  opacity: 1;
}

.btn-delete-conversation:hover {
  background: #ffebee;
  color: #d32f2f;
}

.btn-delete-conversation:active {
  transform: scale(0.95);
}

.btn-new-chat {
  margin-top: auto;
  padding: 0.875rem 1.25rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-new-chat:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.btn-new-chat:active {
  transform: translateY(0);
}

.chat-main {
  width: 100%;
  max-width: 900px;
  display: flex;
  flex-direction: column;
  background: transparent;
  margin: 0 auto;
  height: 100%;
  position: relative;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 1.5rem 1rem;
  scroll-behavior: smooth;
  overscroll-behavior: contain;
  background: transparent;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 确保可以正确滚动 */
  /* 完全隐藏滚动条 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

/* 完全隐藏滚动条 - Webkit browsers */
.messages-container::-webkit-scrollbar {
  display: none;
}

/* 时间分割条 */
.time-separator {
  display: flex;
  justify-content: center;
  margin: 2rem 0;
  position: relative;
}

.time-separator::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(102, 126, 234, 0.2) 50%, transparent 100%);
}

.time-separator span {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  color: #667eea;
  font-size: 0.75rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  position: relative;
  z-index: 1;
  border: 1px solid rgba(102, 126, 234, 0.2);
  font-weight: 500;
  backdrop-filter: blur(10px);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 200px);
  text-align: center;
  color: #666;
  animation: fadeInUp 0.6s ease-out;
  padding: 2rem 0;
  width: 100%;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-icon {
  font-size: 5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1.5rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.empty-state h3 {
  margin: 0 0 0.75rem 0;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 600;
}

.empty-state p {
  margin: 0 0 2rem 0;
  color: #718096;
  font-size: 1rem;
}

.quick-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-btn {
  padding: 0.75rem 1.5rem;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  color: #4a5568;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.quick-btn:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-color: rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.quick-btn:active {
  transform: translateY(0);
}

.message {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  align-items: flex-start;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: messageSlideIn 0.4s ease-out;
  width: 100%;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
  color: #4a5568;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
}

.message-avatar i {
  font-size: 1.25rem;
}

.message-content {
  max-width: 70%;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 1rem 1.25rem;
  border-radius: 18px;
  position: relative;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
  border: none;
}

/* 系统消息样式 */
.message.system {
  justify-content: center;
}
.message.system .message-content.system-content {
  max-width: 80%;
  background: #fff8e1;
  color: #8d6e63;
  border: 1px solid #ffe0b2;
  text-align: center;
}
.message.system .message-content.system-content::after { display: none; }

/* 气泡小尾巴 */
.message-content::after {
  content: '';
  position: absolute;
  top: 16px;
  left: -8px;
  width: 16px;
  height: 16px;
  background: inherit;
  transform: rotate(45deg);
  border-radius: 0 0 0 4px;
  border-left: 1px solid rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.message.user .message-content::after {
  left: auto;
  right: -8px;
  border-left: none;
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.message:hover .message-content {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.message.user:hover .message-content {
  box-shadow: 0 6px 24px rgba(102, 126, 234, 0.4);
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

/* 文本排版与代码样式优化 */
.message-text p { margin: 0 0 0.5rem 0; }
.message-text ul,
.message-text ol { margin: 0.5rem 0 0.5rem 1.25rem; }
.message-text h1,
.message-text h2,
.message-text h3 { margin: 0.75rem 0 0.5rem 0; line-height: 1.25; }
.message-text h1 { font-size: 1.25rem; }
.message-text h2 { font-size: 1.15rem; }
.message-text h3 { font-size: 1.05rem; }

.message-text code {
  background: rgba(0,0,0,0.06);
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.9em;
}

.message.user .message-text code {
  background: rgba(255,255,255,0.18);
}

.message-text pre {
  background: #0f172a; /* slate-900 */
  color: #e2e8f0;      /* slate-200 */
  padding: 0.75rem 1rem;
  border-radius: 8px;
  overflow: auto;
  margin: 0.5rem 0 0 0;
}

.message-text pre code {
  background: transparent;
  padding: 0;
}

.message-text blockquote {
  margin: 0.5rem 0;
  padding: 0.5rem 0.75rem;
  border-left: 3px solid #1976d2;
  background: rgba(25,118,210,0.06);
  border-radius: 0 8px 8px 0;
}

.message-time {
  font-size: 0.75rem;
  color: #999;
  margin-top: 0.5rem;
}

.message.user .message-time {
  color: rgba(255,255,255,0.7);
}

.message-attachments {
  margin-top: 0.5rem;
}

.attachment {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(0,0,0,0.05);
  border-radius: 6px;
  margin-bottom: 0.25rem;
}

.btn-download {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  transition: color 0.2s, transform 0.12s;
}

.btn-download:hover { color: #333; }
.btn-download:active { transform: scale(0.96); }

.typing-indicator {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  padding: 0.5rem 0;
}

.typing-indicator span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  animation: typing 1.4s infinite ease-in-out;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0) scale(1);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-12px) scale(1.2);
    opacity: 1;
  }
}

/* 输入框在empty-state内部时的样式 */
.input-container-empty {
  margin-top: 2.5rem;
  padding: 1.25rem 1.5rem;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid transparent;
  border-radius: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  width: 100%;
  max-width: 700px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-container-empty:hover {
  background: rgba(255, 255, 255, 0.4);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.2);
}

/* 有消息时：输入框在底部正常布局 */
.input-container {
  padding: 1.25rem 1.5rem;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid transparent;
  border-radius: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  z-index: 10;
  width: 90%;
  max-width: 900px;
  margin: 0 auto;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0; /* 防止输入框被压缩 */
}

.input-container.has-messages {
  position: relative;
  margin-top: auto; /* 在flex布局中推到底部 */
  margin-bottom: 1rem;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.input-container.has-messages:hover {
  background: rgba(255, 255, 255, 0.4);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.2);
}

.input-wrapper {
  width: 100%;
  margin: 0 auto;
}

.file-upload-area {
  margin-bottom: 1rem;
}

.upload-zone {
  border: 2px dashed rgba(102, 126, 234, 0.3);
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
}

.upload-zone:hover, .upload-zone.drag-over {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  transform: scale(1.02);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
}

.upload-zone input[type="file"] {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.upload-zone i {
  font-size: 2rem;
  color: #ddd;
  margin-bottom: 0.5rem;
}

.btn-select-file {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-select-file:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.btn-select-file:active {
  transform: translateY(0);
}

.selected-files {
  margin-top: 1rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.btn-remove {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
}

.text-input-area {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  border: 2px solid transparent;
  border-radius: 16px;
  padding: 0.875rem 1.25rem;
  resize: none;
  min-height: 48px;
  max-height: 120px;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.message-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(102, 126, 234, 0.3);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.message-input::placeholder {
  color: #a0aec0;
}

.input-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-attach, .btn-send {
  width: 48px;
  height: 48px;
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.btn-attach:hover, .btn-send:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.btn-attach.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
}

.btn-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none !important;
}

.btn-send:not(:disabled) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
}

.btn-attach:active, .btn-send:active { 
  transform: scale(0.95);
}

/* 轻微的浮起动效 */
.btn-send:not(:disabled):hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 260px;
    top: 64px;
  }

  .chat-container:has(.sidebar-open) .chat-main-wrapper {
    padding-left: 0;
  }

  .chat-main {
    max-width: 100%;
    padding: 0;
  }

  .messages-container {
    padding: 1.5rem 1rem;
  }

  .input-container-empty {
    padding: 1rem;
    width: 95%;
    max-width: 95%;
  }
  
  .input-container {
    padding: 1rem;
    width: 95%;
  }
  
  .input-container.has-messages {
    max-width: 95%;
    margin-bottom: 0.5rem;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .quick-actions {
    flex-direction: column;
    align-items: center;
  }
}

/* 滚动条已完全隐藏，无需额外样式 */

/* Message appear/disappear animations */
.message-fade-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.message-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.message-fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.9);
}
.message-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}
.message-fade-move {
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>

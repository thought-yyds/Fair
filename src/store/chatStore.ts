import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import ChatApi from '@/api/chatApi'
import type { 
  Message, 
  Conversation, 
  ChatState, 
  SendMessageRequest,
  Attachment,
  ChatSettings
} from '@/types/chat'
import { DEFAULT_CHAT_SETTINGS } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const settings = ref<ChatSettings>(DEFAULT_CHAT_SETTINGS)

  // 计算属性
  const currentConversation = computed(() => {
    if (!currentConversationId.value) return null
    return conversations.value.find(c => c.id === currentConversationId.value) || null
  })

  const currentMessages = computed(() => {
    return currentConversation.value?.messages || []
  })

  const hasConversations = computed(() => {
    return conversations.value.length > 0
  })

  // 方法
  const initializeChat = async () => {
    try {
      isLoading.value = true
      error.value = null
      
      // 加载对话列表
      const loadedConversations = await ChatApi.getConversations()
      // 兜底：确保每个会话的 messages 为数组
      conversations.value = (loadedConversations || []).map(c => ({
        ...c,
        messages: Array.isArray(c.messages) ? c.messages : []
      }))
      
      // 恢复上一次打开的会话ID
      const savedId = localStorage.getItem('chat.currentConversationId')
      const exists = savedId && conversations.value.some(c => c.id === savedId)

      // 如果有对话，优先选择上次打开的；否则选择第一个
      if (loadedConversations.length > 0 && !currentConversationId.value) {
        currentConversationId.value = exists ? (savedId as string) : loadedConversations[0].id
      }

      // 首次进入时，若当前会话存在但没有预载消息，则拉取消息
      if (currentConversationId.value) {
        const conv = conversations.value.find(c => c.id === currentConversationId.value)
        if (conv && (!Array.isArray(conv.messages) || conv.messages.length === 0)) {
          const msgs = await ChatApi.getConversationMessages(currentConversationId.value)
          conv.messages = Array.isArray(msgs) ? msgs : []
        }
      }
    } catch (err) {
      // 如果是网络错误或后端未启动，不显示错误，只记录日志
      if (err instanceof Error && (err.message.includes('fetch') || err.message.includes('500'))) {
        console.warn('后端服务可能未启动，聊天功能将受限:', err.message)
        // 初始化空状态，不显示错误
        conversations.value = []
        error.value = null
      } else {
        error.value = err instanceof Error ? err.message : '初始化聊天失败'
        console.error('初始化聊天失败:', err)
      }
    } finally {
      isLoading.value = false
    }
  }

  const createNewConversation = async (title?: string) => {
    try {
      isLoading.value = true
      error.value = null
      
      const newConversation = await ChatApi.createConversation(title)
      // 兜底：确保 messages 存在，并使用当前时间
      const normalized = {
        ...newConversation,
        messages: Array.isArray(newConversation?.messages) ? newConversation.messages : [],
        createdAt: Date.now(), // 确保使用当前时间
        updatedAt: Date.now()   // 确保使用当前时间
      }
      conversations.value.unshift(normalized)
      currentConversationId.value = normalized.id
      
      return newConversation
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建对话失败'
      console.error('创建对话失败:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const switchConversation = async (conversationId: string) => {
    try {
      if (currentConversationId.value === conversationId) return
      
      isLoading.value = true
      error.value = null
      
      // 先切换ID（以便UI快速响应），并持久化
      currentConversationId.value = conversationId
      localStorage.setItem('chat.currentConversationId', conversationId)

      // 确保会话存在于内存
      let conversation = conversations.value.find(c => c.id === conversationId)
      if (!conversation) {
        conversation = {
          id: conversationId,
          title: `对话 ${conversationId.slice(0, 8)}`,
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now()
        }
        conversations.value.push(conversation)
      }

      // 如果消息未加载或为空，则从后端拉取
      if (!Array.isArray(conversation.messages) || conversation.messages.length === 0) {
        const msgs = await ChatApi.getConversationMessages(conversationId)
        conversation.messages = Array.isArray(msgs) ? msgs : []
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '切换对话失败'
      console.error('切换对话失败:', err)
    } finally {
      isLoading.value = false
    }
  }

  const sendMessage = async (content: string, attachments: Attachment[] = []) => {
    if (!content.trim() && attachments.length === 0) return

    try {
      isLoading.value = true
      error.value = null

      // 如果没有当前对话，创建一个新的
      if (!currentConversationId.value) {
        await createNewConversation()
      }

      // 创建用户消息
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: content.trim(),
        timestamp: Date.now(),
        attachments: attachments.length > 0 ? attachments : undefined
      }

      // 添加到当前对话
      const conversation = currentConversation.value
      if (conversation) {
        conversation.messages = Array.isArray(conversation.messages) ? conversation.messages : []
        conversation.messages.push(userMessage)
        conversation.updatedAt = Date.now()
        
        // 更新对话标题（如果是第一条消息）
        if (conversation.messages.length === 1) {
          const title = content.slice(0, 30) + (content.length > 30 ? '...' : '')
          conversation.title = title
          await ChatApi.updateConversationTitle(conversation.id, title)
        }
      }

      // 发送到服务器
      const request: SendMessageRequest = {
        message: content,
        attachments,
        conversationId: currentConversationId.value!,
        settings: settings.value
      }

      // 使用流式响应
      let assistantMessage = ''
      const assistantMessageId = (Date.now() + 1).toString()
      
      const assistantMessageObj: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: Date.now()
      }

      if (conversation) {
        conversation.messages = Array.isArray(conversation.messages) ? conversation.messages : []
        conversation.messages.push(assistantMessageObj)
      }

      await ChatApi.sendMessageStream(
        request,
        (chunk: string) => {
          assistantMessage += chunk
          if (conversation) {
            const msg = (conversation.messages || []).find(m => m.id === assistantMessageId)
            if (msg) {
              msg.content = assistantMessage
            }
          }
        },
        () => {
          // 完成
          if (conversation) {
            conversation.updatedAt = Date.now()
          }
          // 持久化当前会话ID（若为新建会话时）
          if (currentConversationId.value) {
            localStorage.setItem('chat.currentConversationId', currentConversationId.value)
          }
        },
        (err: Error) => {
          error.value = err.message
          if (conversation) {
            const msg = conversation.messages.find(m => m.id === assistantMessageId)
            if (msg) {
              msg.content = '抱歉，处理您的请求时出现了错误。请稍后重试。'
            }
          }
        }
      )

    } catch (err) {
      error.value = err instanceof Error ? err.message : '发送消息失败'
      console.error('发送消息失败:', err)
      
      // 添加错误消息
      if (currentConversation.value) {
        const errorMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: '抱歉，处理您的请求时出现了错误。请稍后重试。',
          timestamp: Date.now()
        }
        currentConversation.value.messages = Array.isArray(currentConversation.value.messages) ? currentConversation.value.messages : []
        currentConversation.value.messages.push(errorMessage)
      }
    } finally {
      isLoading.value = false
    }
  }

  const clearCurrentConversation = async () => {
    if (!currentConversationId.value) return
    
    try {
      isLoading.value = true
      error.value = null
      
      // 调用后端API清空消息
      await ChatApi.clearConversationMessages(currentConversationId.value)
      
      // 更新前端状态
      if (currentConversation.value) {
        currentConversation.value.messages = []
        currentConversation.value.updatedAt = Date.now()
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '清空对话失败'
      console.error('清空对话失败:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deleteConversation = async (conversationId: string) => {
    try {
      await ChatApi.deleteConversation(conversationId)
      conversations.value = conversations.value.filter(c => c.id !== conversationId)
      
      if (currentConversationId.value === conversationId) {
        currentConversationId.value = conversations.value.length > 0 ? conversations.value[0].id : null
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除对话失败'
      console.error('删除对话失败:', err)
      throw err
    }
  }

  const uploadFile = async (file: File): Promise<Attachment> => {
    try {
      const response = await ChatApi.uploadFile(file)
      if (!response.success || !response.attachment) {
        throw new Error(response.error || '文件上传失败')
      }
      return response.attachment
    } catch (err) {
      error.value = err instanceof Error ? err.message : '文件上传失败'
      console.error('文件上传失败:', err)
      throw err
    }
  }

  const analyzeFile = async (attachmentId: string, prompt?: string): Promise<string> => {
    try {
      return await ChatApi.analyzeFile(attachmentId, prompt)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '文件分析失败'
      console.error('文件分析失败:', err)
      throw err
    }
  }

  const updateSettings = async (newSettings: Partial<ChatSettings>) => {
    try {
      settings.value = { ...settings.value, ...newSettings }
      await ChatApi.updateChatSettings(settings.value)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新设置失败'
      console.error('更新设置失败:', err)
      throw err
    }
  }

  const exportConversation = async (conversationId: string, format: 'json' | 'txt' | 'pdf' = 'json') => {
    try {
      const blob = await ChatApi.exportConversation(conversationId, format)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `conversation_${conversationId}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '导出对话失败'
      console.error('导出对话失败:', err)
      throw err
    }
  }

  const searchConversations = async (query: string): Promise<Conversation[]> => {
    try {
      return await ChatApi.searchConversations(query)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '搜索对话失败'
      console.error('搜索对话失败:', err)
      throw err
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // 状态
    conversations,
    currentConversationId,
    isLoading,
    error,
    settings,
    
    // 计算属性
    currentConversation,
    currentMessages,
    hasConversations,
    
    // 方法
    initializeChat,
    createNewConversation,
    switchConversation,
    sendMessage,
    clearCurrentConversation,
    deleteConversation,
    uploadFile,
    analyzeFile,
    updateSettings,
    exportConversation,
    searchConversations,
    clearError
  }
})

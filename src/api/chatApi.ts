import request from '@/utils/request'
import type { 
  SendMessageRequest, 
  SendMessageResponse, 
  Conversation, 
  Message, 
  FileUploadResponse
} from '@/types/chat'

// 聊天API接口
export class ChatApi {
  private static baseUrl = '/api/chat'

  // 将后端的会话结构映射为前端的 Conversation 结构
  private static mapSessionToConversation(session: any): Conversation {
    return {
      id: String(session.session_id || session.id), // 使用 session_id 作为前端会话ID
      title: session.title || `对话 ${String(session.session_id || session.id).slice(0, 8)}`,
      messages: Array.isArray(session.messages) ? session.messages : [],
      createdAt: session.created_at ? new Date(session.created_at).getTime() : Date.now(),
      updatedAt: session.updated_at ? new Date(session.updated_at).getTime() : Date.now(),
      metadata: session.message_count != null ? { totalMessages: session.message_count } : undefined
    }
  }

  // 将后端消息结构映射为前端的 Message 结构
  private static mapBackendMessage(msg: any): Message {
    return {
      id: String(msg.id),
      role: msg.role === 'assistant' ? 'assistant' : 'user',
      content: msg.content ?? '',
      timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now()
    }
  }

  /**
   * 发送消息
   */
  static async sendMessage(data: SendMessageRequest): Promise<SendMessageResponse> {
    try {
      const response = await request<SendMessageResponse>({
        method: 'POST',
        url: `${this.baseUrl}/message`,
        data
      })
      return response
    } catch (error) {
      console.error('发送消息失败:', error)
      throw error
    }
  }

  /**
   * 获取对话列表
   */
  static async getConversations(): Promise<Conversation[]> {
    try {
      const response = await request<any[]>({
        method: 'GET',
        url: `${this.baseUrl}/conversations`
      })
      return (response || []).map(s => this.mapSessionToConversation(s))
    } catch (error) {
      console.error('获取对话列表失败:', error)
      throw error
    }
  }

  /**
   * 获取特定对话的消息
   */
  static async getConversationMessages(conversationId: string): Promise<Message[]> {
    try {
      const response = await request<any[]>({
        method: 'GET',
        url: `${this.baseUrl}/conversations/${conversationId}/messages`
      })
      return (response || []).map(m => this.mapBackendMessage(m))
    } catch (error) {
      console.error('获取对话消息失败:', error)
      throw error
    }
  }

  /**
   * 创建新对话
   */
  static async createConversation(title?: string): Promise<Conversation> {
    try {
      const response = await request<any>({
        method: 'POST',
        url: `${this.baseUrl}/conversations`,
        data: { title }
      })
      return this.mapSessionToConversation(response)
    } catch (error) {
      console.error('创建对话失败:', error)
      throw error
    }
  }

  /**
   * 删除对话
   */
  static async deleteConversation(conversationId: string): Promise<void> {
    try {
      await request<void>({
        method: 'DELETE',
        url: `${this.baseUrl}/conversations/${conversationId}`
      })
    } catch (error) {
      console.error('删除对话失败:', error)
      throw error
    }
  }

  /**
   * 清空对话消息
   */
  static async clearConversationMessages(conversationId: string): Promise<void> {
    try {
      await request<void>({
        method: 'DELETE',
        url: `${this.baseUrl}/conversations/${conversationId}/messages`
      })
    } catch (error) {
      console.error('清空对话消息失败:', error)
      throw error
    }
  }

  /**
   * 更新对话标题
   */
  static async updateConversationTitle(conversationId: string, title: string): Promise<void> {
    try {
      const formData = new FormData()
      formData.append('title', title)

      await request<void>({
        method: 'PUT',
        url: `${this.baseUrl}/conversations/${conversationId}`,
        data: formData
      })
    } catch (error) {
      console.error('更新对话标题失败:', error)
      throw error
    }
  }

  /**
   * 上传文件
   */
  static async uploadFile(file: File, sessionId?: string, messageId?: number): Promise<FileUploadResponse> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (sessionId) formData.append('session_id', sessionId)
      if (messageId != null) formData.append('message_id', String(messageId))

      const response = await request<FileUploadResponse>({
        method: 'POST',
        url: `${this.baseUrl}/upload`,
        data: formData,
        timeout: 30000 // 30秒超时
      })
      return response
    } catch (error) {
      console.error('文件上传失败:', error)
      throw error
    }
  }

  /**
   * 分析文件内容
   */
  static async analyzeFile(attachmentId: string, prompt?: string): Promise<string> {
    try {
      const response = await request<{ analysis: string }>({
        method: 'POST',
        url: `${this.baseUrl}/analyze`,
        data: {
          attachment_id: attachmentId,
          prompt: prompt || '请分析这个文件的内容'
        }
      })
      return response.analysis
    } catch (error) {
      console.error('文件分析失败:', error)
      throw error
    }
  }

  /**
   * 获取聊天设置
   */
  static async getChatSettings(): Promise<any> {
    try {
      const response = await request<any>({
        method: 'GET',
        url: `${this.baseUrl}/settings`
      })
      return response
    } catch (error) {
      console.error('获取聊天设置失败:', error)
      throw error
    }
  }

  /**
   * 更新聊天设置
   */
  static async updateChatSettings(settings: any): Promise<void> {
    try {
      await request<void>({
        method: 'PUT',
        url: `${this.baseUrl}/settings`,
        data: settings
      })
    } catch (error) {
      console.error('更新聊天设置失败:', error)
      throw error
    }
  }

  /**
   * 流式发送消息（用于实时响应）
   */
  static async sendMessageStream(
    data: SendMessageRequest,
    onMessage: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
          message: data.message,
          session_id: data.conversationId,
          user_id: undefined,
          context: undefined,
          attachments: data.attachments
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法获取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          onComplete()
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              onComplete()
              return
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                onMessage(parsed.content)
              }
            } catch (e) {
              console.warn('解析流数据失败:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('流式发送消息失败:', error)
      onError(error as Error)
    }
  }

  /**
   * 导出对话
   */
  static async exportConversation(conversationId: string, format: 'json' | 'txt' | 'pdf' = 'json'): Promise<Blob> {
    try {
      const response = await request<Blob>({
        method: 'GET',
        url: `${this.baseUrl}/conversations/${conversationId}/export`,
        params: { format },
        responseType: 'blob'
      })
      return response
    } catch (error) {
      console.error('导出对话失败:', error)
      throw error
    }
  }

  /**
   * 搜索对话
   */
  static async searchConversations(query: string): Promise<Conversation[]> {
    try {
      const response = await request<Conversation[]>({
        method: 'GET',
        url: `${this.baseUrl}/search`,
        params: { q: query }
      })
      return response
    } catch (error) {
      console.error('搜索对话失败:', error)
      throw error
    }
  }
}

// 导出默认实例
export default ChatApi

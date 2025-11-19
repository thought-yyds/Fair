// 聊天相关的类型定义

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  attachments?: Attachment[]
  metadata?: {
    model?: string
    tokens?: number
    processingTime?: number
  }
}

export interface Attachment {
  id: string
  name: string
  type: string
  size: number
  url?: string
  file?: File
  content?: string // 文件内容（用于文本文件）
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
  updatedAt: number
  metadata?: {
    totalMessages?: number
    totalTokens?: number
    lastActivity?: string
  }
}

export interface ChatSettings {
  model: string
  temperature: number
  maxTokens: number
  systemPrompt?: string
  enableFileUpload: boolean
  maxFileSize: number
  allowedFileTypes: string[]
}

export interface ChatState {
  conversations: Conversation[]
  currentConversationId: string | null
  isLoading: boolean
  error: string | null
  settings: ChatSettings
}

export interface SendMessageRequest {
  message: string
  attachments?: Attachment[]
  conversationId?: string
  settings?: Partial<ChatSettings>
}

export interface SendMessageResponse {
  message: Message
  conversationId: string
  success: boolean
  error?: string
}

export interface FileUploadResponse {
  success: boolean
  attachment?: Attachment
  error?: string
}

// 预设的系统提示词
export const SYSTEM_PROMPTS = {
  assistant: '你是一个专门从事公平竞争审查任务的专业助手。你的主要职责是帮助用户进行公平竞争相关的文档审查、分析和评估。你具备深厚的公平竞争法律法规知识，能够识别潜在的竞争问题，分析市场行为是否符合公平竞争原则，并提供专业的审查建议。请用专业、准确、客观的语气回复用户的问题。',
  analyst: '你是一个专业的文档分析师，擅长分析各种类型的文档，提取关键信息，并提供深入的见解。',
  summarizer: '你是一个内容总结专家，能够快速准确地总结文档内容，提取要点和关键信息。',
  reviewer: '你是一个专业的审查员，能够从多个角度分析文档，识别潜在问题并提供改进建议。'
}

// 支持的文件类型
export const SUPPORTED_FILE_TYPES = {
  documents: ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'],
  images: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
  spreadsheets: ['.xls', '.xlsx', '.csv'],
  presentations: ['.ppt', '.pptx'],
  archives: ['.zip', '.rar', '.7z']
}

// 文件大小限制（字节）
export const FILE_SIZE_LIMITS = {
  small: 5 * 1024 * 1024, // 5MB
  medium: 10 * 1024 * 1024, // 10MB
  large: 50 * 1024 * 1024, // 50MB
  xlarge: 100 * 1024 * 1024 // 100MB
}

// 默认聊天设置
export const DEFAULT_CHAT_SETTINGS: ChatSettings = {
  model: 'gpt-3.5-turbo',
  temperature: 0.7,
  maxTokens: 2000,
  systemPrompt: SYSTEM_PROMPTS.assistant,
  enableFileUpload: true,
  maxFileSize: FILE_SIZE_LIMITS.medium,
  allowedFileTypes: [
    ...SUPPORTED_FILE_TYPES.documents,
    ...SUPPORTED_FILE_TYPES.images,
    ...SUPPORTED_FILE_TYPES.spreadsheets
  ]
}

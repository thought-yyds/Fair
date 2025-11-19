import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Article } from '@/types/article'

export const useFileStore = defineStore('file', () => {
  // 状态
  const files = ref<Article[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const pendingFiles = computed(() => 
    files.value.filter(file => file.status === '待审查')
  )
  
  const reviewedFiles = computed(() => 
    files.value.filter(file => file.status === '已审查')
  )
  
  const totalFiles = computed(() => files.value.length)

  // 操作
  const setFiles = (newFiles: Article[]) => {
    files.value = newFiles
  }

  const addFile = (file: Article) => {
    files.value.push(file)
  }

  const removeFile = (fileId: number) => {
    const index = files.value.findIndex(file => file.id === fileId)
    if (index > -1) {
      files.value.splice(index, 1)
    }
  }

  const updateFile = (fileId: number, updates: Partial<Article>) => {
    const file = files.value.find(f => f.id === fileId)
    if (file) {
      Object.assign(file, updates)
    }
  }

  const setLoading = (isLoading: boolean) => {
    loading.value = isLoading
  }

  const setError = (errorMessage: string | null) => {
    error.value = errorMessage
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // 状态
    files,
    loading,
    error,
    // 计算属性
    pendingFiles,
    reviewedFiles,
    totalFiles,
    // 操作
    setFiles,
    addFile,
    removeFile,
    updateFile,
    setLoading,
    setError,
    clearError
  }
})

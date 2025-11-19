<!-- src/components/FileUploader.vue -->
<template>
  <div class="file-uploader bg-white p-4 rounded-xl shadow-sm">
    <h3 class="text-lg font-semibold mb-4 flex items-center">
      <i class="fa fa-upload text-primary mr-2"></i>上传文件
    </h3>
    
    <!-- 上传区域：拖拽+点击选择 -->
    <div 
      class="upload-area border-2 border-dashed border-gray-200 rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer"
      @click="handleClickUpload"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <input 
        ref="fileInputRef" 
        type="file" 
        class="hidden" 
        accept=".docx,.pdf" 
        @change="handleFileSelect"
      >
      
      <i class="fa fa-file-text-o text-4xl text-gray-300 mb-3"></i>
      <p class="text-gray-600 mb-2">点击或拖拽文件至此处上传</p>
      <p class="text-xs text-gray-400">支持格式：docx、pdf（单个文件≤10MB）</p>
      
      <!-- 拖拽时高亮 -->
      <div v-if="isDragging" class="absolute inset-0 bg-primary/5 rounded-lg pointer-events-none"></div>
    </div>
    
    <!-- 上传状态反馈 -->
    <div v-if="uploadStatus" class="mt-4 p-3 rounded-lg text-sm font-medium" :class="statusClass">
  <!-- 用数组语法分隔动态类和静态类，添加逗号 -->
  <i :class="[statusIcon, 'mr-1']"></i>
  {{ uploadMessage }}
</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { uploadFile } from '@/api/fileApi'
import type { UploadFileParams, Article } from '@/types/article'
import { ElMessage } from 'element-plus'
import { validateFileUpload } from '@/utils/validators'

// 1. 响应式变量
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const uploadLoading = ref(false) // 上传中状态
const uploadStatus = ref<'success' | 'error' | null>(null) // 上传结果状态
const uploadMessage = ref('')

// 2. 父组件通信：上传成功后通知刷新列表
const emit = defineEmits<{
  (e: 'uploadSuccess', data: Article): void // 上传成功：传递文件信息
}>()

// 3. 计算属性：上传状态样式
const statusClass = computed(() => {
  if (uploadStatus.value === 'success') return 'bg-green-100 text-green-800'
  if (uploadStatus.value === 'error') return 'bg-red-100 text-red-800'
  return ''
})

const statusIcon = computed(() => {
  if (uploadStatus.value === 'success') return 'fa fa-check-circle'
  if (uploadStatus.value === 'error') return 'fa fa-exclamation-circle'
  return ''
})

// 4. 上传逻辑：触发文件选择
const handleClickUpload = () => {
  fileInputRef.value?.click()
}

// 拖拽上传
const handleDrop = (e: DragEvent) => {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    handleFile(files[0]) // 只处理单个文件
  }
}

// 点击选择文件
const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    handleFile(target.files[0])
    target.value = '' // 重置输入，支持重复选择同一文件
  }
}

// 5. 文件处理：校验+上传
const handleFile = async (file: File) => {
  // 第一步：使用统一验证工具校验文件
  const validation = validateFileUpload(file)
  if (!validation.valid) {
    uploadStatus.value = 'error'
    uploadMessage.value = validation.message || '文件验证失败'
    setTimeout(() => uploadStatus.value = null, 3000)
    return
  }

  // 第二步：调用API上传
  uploadLoading.value = true
  uploadStatus.value = null
  try {
    const params: UploadFileParams = { file }
    const response = await uploadFile(params) // 复用fileApi的uploadFile
    const result = response.data
    
    // 上传成功：通知父组件刷新列表
    uploadStatus.value = 'success'
    uploadMessage.value = `文件 "${result.name}" 上传成功！`
    emit('uploadSuccess', result)
    ElMessage.success(uploadMessage.value)
  } catch (error) {
    uploadStatus.value = 'error'
    uploadMessage.value = '上传失败！请检查网络或联系管理员'
    console.error('文件上传失败:', error)
    ElMessage.error(uploadMessage.value)
  } finally {
    uploadLoading.value = false
    setTimeout(() => uploadStatus.value = null, 3000) // 3秒后清除状态
  }
}
</script>

<style scoped>
.upload-area {
  position: relative;
}
</style>
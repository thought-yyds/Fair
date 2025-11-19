<template>
  <!-- 根容器：和 Home 一致（min-h-screen bg-gray-50 全局浅灰背景） -->
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- 1. 顶部渐变 Header：和 Home 完全一样 -->
    <header class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg transition-all duration-300">
      <div class="container mx-auto px-4 py-6">
        <h1 class="text-[clamp(1.5rem,3vw,2.5rem)] font-bold tracking-tight flex items-center">
          <i class="fa-solid fa-balance-scale mr-3 text-yellow-300"></i>
          公平审查大数据平台
        </h1>
      </div>
    </header>

    <!-- 2. 导航菜单：和 Home 1:1 对齐（首页+文件管理按钮） -->
    <nav class="bg-white shadow-md sticky top-0 z-10 transition-all duration-300">
      <div class="container mx-auto px-4">
        <ul class="flex space-x-3 py-3">
          <!-- 首页按钮：样式和 Home 完全一致 -->
          <li>
            <router-link
              to="/"
              class="inline-flex items-center px-5 py-2.5 rounded-md font-medium text-sm transition-all duration-200"
              :class="{ 
                'bg-blue-600 text-white shadow-sm': $route.path === '/', 
                'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700': $route.path !== '/' 
              }"
            >
              <i class="fa-solid fa-home mr-2"></i>
              首页
            </router-link>
          </li>
          <!-- 文件管理按钮：激活状态和 Home 一致 -->
          <li>
            <router-link
              to="/file-manage"
              class="inline-flex items-center px-5 py-2.5 rounded-md font-medium text-sm transition-all duration-200"
              :class="{ 
                'bg-blue-600 text-white shadow-sm': $route.path === '/file-manage', 
                'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700': $route.path !== '/file-manage' 
              }"
            >
              <i class="fa-solid fa-folder mr-2"></i>
              文件管理
            </router-link>
          </li>
        </ul>
      </div>
    </nav>

    <!-- 3. 主要内容区：和 Home 一致的容器+间距 -->
    <main class="flex-grow container mx-auto px-4 py-8">
      <!-- 页面描述：和 Home 风格统一 -->
      <div class="mb-8 text-gray-600">
        <p>集中管理所有上传文件，支持搜索、分页和批量操作</p>
      </div>


      <!-- 文件列表区域：卡片样式和 Home 一致，最大化宽度 -->
      <section class="bg-white rounded-xl shadow-lg p-6 transform hover:shadow-xl transition-all duration-300 border border-gray-100 w-full">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-semibold text-gray-800 flex items-center">
              <i class="fa-solid fa-list-alt text-blue-600 mr-2"></i>
              所有文件列表
            </h2>
            <!-- 总数标签：和 Home 待审查数量样式一致 -->
            <span class="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-normal">
              共 {{ totalFiles }} 个文件
            </span>
          </div>

          <!-- 文件列表内容：复用组件，样式和 Home 文件项对齐 -->
          <div class="file-list space-y-4">
            <FileList 
              @updateTotal="(total: number) => totalFiles = total"
              :fileItemClass="fileItemClass"
              @viewDetail="handleViewDetail"
              @deleteFile="handleConfirmDelete"
            />
          </div>
      </section>
    </main>

    <!-- 4. 页脚：和 Home 完全一致 -->
    <footer class="bg-gray-800 text-white py-4 mt-auto">
      <div class="container mx-auto px-4 text-center text-sm">
        <p>© 2023 公平审查大数据平台 版权所有</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import FileList from '@/components/FileList.vue'
import { handleAsyncError } from '@/utils/errorHandler'
import { confirm, operation } from '@/utils/feedbackManager'

// 响应式变量
const totalFiles = ref(0)
const router = useRouter()

// 文件项样式：和 Home 一致
const fileItemClass = ref({
  base: 'border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:bg-blue-50 hover:shadow-sm transition-all duration-200 flex flex-wrap justify-between items-center',
  details: 'flex-grow mb-3 sm:mb-0',
  name: 'font-medium text-gray-800 mb-1 flex items-center truncate',
  time: 'text-sm text-gray-500',
  actions: 'flex items-center gap-4 flex-wrap justify-end'
})


// 查看详情：和 Home 路由一致
const handleViewDetail = (articleId: number) => {
  router.push(`/review/${articleId}`)
}

// 删除文件：使用统一的错误处理和确认机制
const handleConfirmDelete = async (articleId: number, fileName: string) => {
  const confirmed = await confirm.confirmDelete(fileName, '文件')
  
  if (!confirmed) return

  const result = await handleAsyncError(async () => {
    const { deleteFile } = await import('@/api/fileApi')
    const response = await deleteFile(articleId)
    
    if (response.success) {
      operation.deleteSuccess(fileName)
      return true
    } else {
      throw new Error(response.msg || '删除失败')
    }
  })

  if (result) {
    console.log('文件删除成功')
  }
}
</script>

<!-- 响应式样式：和 Home 完全一致 -->
<style scoped>
@media (max-width: 1024px) {
  .file-actions {
    width: 100%;
    margin-top: 0.8rem;
    flex-direction: column;
    align-items: flex-start !important;
    gap: 0.5rem;
  }
  .file-actions > div:last-child {
    margin-top: 0.5rem;
    align-self: flex-end;
  }
}

@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
  .file-actions {
    align-items: stretch !important;
  }
  .file-actions button {
    width: 100%;
    justify-content: center;
  }
  .file-actions > div:first-child {
    width: 100%;
    justify-content: center;
    margin-bottom: 0.5rem;
  }
}

@media (max-width: 480px) {
  header .container {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }
  h1 {
    font-size: 1.5rem !important;
  }
  .nav ul {
    justify-content: center;
  }
  section {
    padding: 4px !important;
  }
}
</style>
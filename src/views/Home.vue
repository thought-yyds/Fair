<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- 1. 顶部导航栏（渐变主题，和文件管理页统一） -->
    <header class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg transition-all duration-300">
      <div class="container mx-auto px-4 py-6">
        <h1 class="text-[clamp(1.5rem,3vw,2.5rem)] font-bold tracking-tight flex items-center">
          <i class="fa fa-balance-scale mr-3 text-yellow-300"></i> <!-- 使用图标 -->
          公平审查大数据平台
        </h1>
      </div>
    </header>

    <!-- 2. 导航菜单（修复首页链接刷新问题，增加激活状态） -->
    <!-- 2. 导航菜单（核心优化：让“首页”和“文件管理”按钮样式完全统一） -->
<!-- 2. 导航菜单（最终优化：首页和文件管理样式100%统一） -->
<nav class="bg-white shadow-md sticky top-0 z-10 transition-all duration-300">
  <div class="container mx-auto px-4">
    <ul class="flex space-x-3 py-3"> <!-- 统一按钮间距为space-x-3，避免太挤 -->
      <!-- 首页按钮：基础样式+状态样式完全固定 -->
      <li>
        <router-link
          to="/"
          class="inline-flex items-center px-5 py-2.5 rounded-md font-medium text-sm transition-all duration-200"
          :class="{ 
            // 激活状态：统一深蓝色背景+白色文字+细阴影
            'bg-blue-600 text-white shadow-sm': $route.path === '/', 
            // 未激活状态：统一浅灰色背景+深灰色文字，hover时变浅蓝
            'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700': $route.path !== '/' 
          }"
        >
          <i class="fa fa-home mr-2"></i>
          首页
        </router-link>
      </li>

      <!-- 文件管理按钮：和首页按钮的所有样式类完全一致（只改图标和文字） -->
      <li>
        <router-link
          to="/file-manage"
          class="inline-flex items-center px-5 py-2.5 rounded-md font-medium text-sm transition-all duration-200"
          :class="{ 
            // 激活状态：和首页激活样式完全一样
            'bg-blue-600 text-white shadow-sm': $route.path === '/file-manage', 
            // 未激活状态：和首页未激活样式完全一样（bg-gray-100等完全相同）
            'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700': $route.path !== '/file-manage' 
          }"
        >
          <i class="fa fa-folder mr-2"></i>
          文件管理
        </router-link>
      </li>

      <!-- AI智能助手按钮：和其他按钮样式完全一致 -->
      <li>
        <router-link
          to="/chat"
          class="inline-flex items-center px-5 py-2.5 rounded-md font-medium text-sm transition-all duration-200"
          :class="{ 
            // 激活状态：和其他按钮激活样式完全一样
            'bg-blue-600 text-white shadow-sm': $route.path === '/chat', 
            // 未激活状态：和其他按钮未激活样式完全一样
            'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700': $route.path !== '/chat' 
          }"
        >
          <i class="fa fa-robot mr-2"></i>
          AI智能助手
        </router-link>
      </li>
    </ul>
  </div>
</nav>

    <!-- 3. 主要内容区（优化卡片阴影和间距） -->
    <main class="flex-grow container mx-auto px-4 py-8">
      <!-- 文件上传区域（增加浅蓝色背景，突出功能） -->
      <section class="bg-white rounded-xl shadow-lg p-6 mb-8 transform hover:shadow-xl transition-all duration-300 border border-gray-100">
        <h2 class="text-xl font-semibold text-gray-800 mb-6 flex items-center">
          <i class="fa fa-upload text-blue-600 mr-2"></i>
          文件上传
        </h2>

        <div class="flex flex-wrap items-center gap-4 p-4 bg-blue-50 rounded-lg">
          <div class="flex-grow min-w-[250px]">
            <input
              type="text"
              v-model="fileName"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
              readonly
              placeholder="未选择文件"
            >
          </div>

          <input
            type="file"
            ref="fileInputRef"
            accept=".docx, .pdf"
            class="hidden"
            @change="handleFileChange"
          >

          <!-- 选择文件按钮：优化 hover 效果 -->
          <button
            type="button"
            @click="handleOpenFileSelector"
            class="px-6 py-3 bg-indigo-600 text-white rounded-lg shadow hover:bg-indigo-700 hover:shadow-md transition-all duration-200 flex items-center"
          >
            <i class="fa fa-folder-open mr-2"></i>选择文件
          </button>

          <!-- 上传按钮：优化禁用样式 -->
          <button
            type="button"
            @click="handleFileUpload"
            :disabled="!isFileSelected"
            class="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 hover:shadow-md transition-all duration-200 flex items-center disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
          >
            <i class="fa fa-cloud-upload mr-2"></i>上传文件
          </button>
        </div>
      </section>

      <!-- 两个文件列表区域（移除审查中区域，优化间距） -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- 待审查文件区域（增加间距，优化布局） -->
        <section class="bg-white rounded-xl shadow-lg p-8 transform hover:shadow-xl transition-all duration-300 border border-gray-100">
          <h2 class="text-xl font-semibold text-gray-800 mb-8 flex items-center">
            <i class="fa fa-clock-o text-amber-500 mr-2"></i>
            待审查文件
            <span class="ml-2 px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-normal">
              {{ pendingArticles.length }}
            </span>
          </h2>

          <div class="file-list space-y-6 min-h-[300px]">
            <!-- 空状态：优化图标大小和文字间距 -->
            <div v-if="pendingArticles.length === 0" class="text-center py-16 text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
              <i class="fa fa-file-o text-5xl mb-4 opacity-50 text-amber-400"></i>
              <p class="text-xl font-medium">暂无待审查文件</p>
              <p class="text-sm mt-3 text-gray-400">上传文件后将显示在这里</p>
            </div>

            <!-- 待审查文件项：优化间距和文件名显示 -->
            <div
              v-for="article in pendingArticles"
              :key="article.id"
              class="file-item border border-gray-200 rounded-lg p-6 hover:border-amber-300 hover:bg-amber-50 hover:shadow-sm transition-all duration-200 flex flex-col gap-4"
            >
              <div class="file-details">
                <div class="font-medium text-gray-800 mb-2 flex items-center">
                  <i class="fa fa-file-text text-amber-500 mr-2 flex-shrink-0"></i>
                  <span class="truncate" :title="article.name">{{ article.name }}</span>
                </div>
                <div class="text-sm text-gray-500 flex items-center gap-4">
                  <span>上传时间: {{ article.upload_time }}</span>
                  <span class="px-2 py-1 bg-amber-100 text-amber-800 rounded text-xs">
                    待审查
                  </span>
                </div>
              </div>

              <div class="file-actions flex gap-3 justify-end">
                <!-- 开始审查按钮：优化颜色和大小 -->
                <button
                  @click="handleStartReview(article.id)"
                  class="px-6 py-2 bg-amber-500 text-white rounded-lg shadow hover:bg-amber-600 hover:shadow-md transition-all duration-200 flex items-center text-sm"
                >
                  <i class="fa fa-check-circle mr-1"></i> 开始审查
                </button>
                <!-- 删除按钮：优化 hover 颜色 -->
                <button
                  @click="handleConfirmDelete(article.id, article.name)"
                  class="px-4 py-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors duration-200 flex items-center"
                >
                  <i class="fa fa-trash mr-1"></i> 删除
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- 已审查文件区域（增加间距，优化布局） -->
        <section class="bg-white rounded-xl shadow-lg p-8 transform hover:shadow-xl transition-all duration-300 border border-gray-100">
          <h2 class="text-xl font-semibold text-gray-800 mb-8 flex items-center">
            <i class="fa fa-check-square-o text-green-500 mr-2"></i>
            已审查文件
            <span class="ml-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-normal">
              {{ reviewedArticles.length }}
            </span>
          </h2>

          <div class="file-list space-y-6 min-h-[300px]">
            <!-- 空状态：和待审查样式统一 -->
            <div v-if="reviewedArticles.length === 0" class="text-center py-16 text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
              <i class="fa fa-file-text-o text-5xl mb-4 opacity-50 text-green-400"></i>
              <p class="text-xl font-medium">暂无已审查文件</p>
              <p class="text-sm mt-3 text-gray-400">待审查文件完成审查后将显示在这里</p>
            </div>

            <!-- 已审查文件项：优化风险等级标签样式和间距 -->
            <div
              v-for="article in reviewedArticles"
              :key="article.id"
              class="file-item border border-gray-200 rounded-lg p-6 hover:border-green-300 hover:bg-green-50 hover:shadow-sm transition-all duration-200 flex flex-col gap-4"
            >
              <div class="file-details">
                <div class="font-medium text-gray-800 mb-2 flex items-center">
                  <i class="fa fa-file-text text-green-500 mr-2 flex-shrink-0"></i>
                  <span class="truncate" :title="article.name">{{ article.name }}</span>
                </div>
                <div class="text-sm text-gray-500 flex items-center gap-4">
                  <span>上传时间: {{ article.upload_time }}</span>
                  <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                    已审查
                  </span>
                </div>
              </div>

              <div class="file-actions flex items-center justify-between flex-wrap gap-4">
                <!-- 风险等级：优化标签样式 -->
                <div class="flex items-center">
                  <span class="text-sm font-medium mr-2">风险等级：</span>
                  <span
                    :class="getRiskLevelClass(article.risk_level)"
                    class="px-3 py-1 rounded-full text-xs font-medium"
                  >
                    {{ article.risk_level || '未评估' }}
                  </span>
                </div>

                <div class="flex gap-3">
                  <!-- 查看详情：优化 hover 背景 -->
                  <button
                    @click="handleViewArticle(article.id)"
                    class="px-4 py-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors duration-200 flex items-center"
                  >
                    <i class="fa fa-eye mr-1"></i> 查看详情
                  </button>
                  <!-- 删除按钮：和待审查样式统一 -->
                  <button
                    @click="handleConfirmDelete(article.id, article.name)"
                    class="px-4 py-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors duration-200 flex items-center"
                  >
                    <i class="fa fa-trash mr-1"></i> 删除
                  </button>
                </div>
              </div>
            </div>
            
            <!-- 查看更多提示 -->
            <div v-if="articles.filter(article => article.status === '已审查').length > 2" class="text-center py-4">
              <p class="text-sm text-gray-500 mb-3">
                还有 {{ articles.filter(article => article.status === '已审查').length - 2 }} 个已审查文件
              </p>
              <router-link
                to="/file-manage"
                class="inline-flex items-center px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors duration-200 text-sm"
              >
                <i class="fa fa-folder mr-2"></i>
                查看全部文件
              </router-link>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- 4. 页脚（和文件管理页完全统一） -->
    <footer class="bg-gray-800 text-white py-4 mt-auto">
      <div class="container mx-auto px-4 text-center text-sm">
        <p>© 2023 公平审查大数据平台 版权所有</p>
      </div>
    </footer>

    <!-- 5. 审查进度弹窗（优化进度条和文字样式） -->
    <div v-if="showReviewProgress" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4 transform transition-all duration-300 shadow-2xl">
        <h3 class="text-xl font-semibold text-gray-800 mb-4 flex items-center">
          <i class="fa fa-cog fa-spin text-blue-600 mr-2"></i>
          正在审查文件
        </h3>

        <p class="text-gray-600 mb-5">请稍候，系统正在进行文件审查...</p>

        <!-- 进度条：优化高度和圆角 -->
        <div class="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div
            class="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
            :style="{ width: `${reviewProgress}%` }"
          ></div>
        </div>

        <p class="text-sm text-gray-500 text-center">
          已完成: {{ reviewProgress }}%
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus' // 导入Element提示组件，替换原生alert
import type { AxiosResponse } from 'axios'
import { handleAsyncError, handleUploadError, handleReviewError } from '@/utils/errorHandler'
import {  confirm, operation } from '@/utils/feedbackManager'
// ========================== 1. 导入类型定义（统一使用types目录中的定义）==========================
import type { Article } from '@/types/article';
import type { ReviewProgress } from '@/types/review';

// 本地接口定义
// interface ApiResponse {
//   success: boolean;
//   msg?: string;
//   data?: any;
// }

// ========================== 2. 定义响应式变量（保持不变）==========================
const fileName = ref<string>('未选择文件')
const fileInputRef = ref<HTMLInputElement | null>(null)
const articles = ref<Article[]>([])
const showReviewProgress = ref<boolean>(false)
const reviewProgress = ref<number>(0)
const progressInterval = ref<NodeJS.Timeout | null>(null)
const listRefreshInterval = ref<NodeJS.Timeout | null>(null)
const isReviewInitiated = ref<boolean>(false)
const router = useRouter()

// ========================== 3. 计算属性（简化状态分类，移除审查中区域，待审查文件不省略，已审查文件限制显示数量）==========================
const pendingArticles = computed<Article[]>(() => {
  return articles.value.filter(article => article.status === '待审查')
})
const reviewedArticles = computed<Article[]>(() => {
  return articles.value.filter(article => article.status === '已审查').slice(0, 2)
})
const isFileSelected = computed<boolean>(() => {
  return fileName.value !== '未选择文件' && !!fileName.value
})

// ========================== 4. 工具函数（更新类型引用）==========================
const getRiskLevelClass = (level?: Article['risk_level']): string => {
  switch (level) {
    case '无风险':
      return 'bg-green-100 text-green-800';
    case '低风险':
      return 'bg-blue-100 text-blue-800';
    case '中风险':
      return 'bg-yellow-100 text-yellow-800';
    case '高风险':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

// ========================== 5. 文件选择相关函数（保持不变）==========================
const handleOpenFileSelector = (): void => {
  fileInputRef.value?.click()
}
const handleFileChange = (e: Event): void => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  fileName.value = file ? file.name : '未选择文件'
}

// ========================== 6. 文件上传函数（使用统一错误处理）==========================
const handleFileUpload = async (): Promise<void> => {
  const file = fileInputRef.value?.files?.[0]
  if (!file) {
    ElMessage.warning('请先选择文件')
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  const result = await handleAsyncError(async () => {
    const response: AxiosResponse<{ success: boolean; msg: string; data: Article }> = await axios.post('/api/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.success) {
      operation.uploadSuccess(file.name)
      // 重置状态
      fileName.value = '未选择文件'
      fileInputRef.value!.value = ''
      await fetchArticles()
      return response.data.data
    } else {
      throw new Error(response.data.msg || '上传失败')
    }
  }, handleUploadError)

  if (result) {
    console.log('文件上传成功:', result)
  }
}

// ========================== 7. 文件删除函数（使用统一确认和错误处理）==========================
const handleConfirmDelete = async (articleId: number, fileName: string): Promise<void> => {
  const confirmed = await confirm.confirmDelete(fileName, '文件')
  
  if (!confirmed) return

  const result = await handleAsyncError(async () => {
    const response: AxiosResponse<{ success: boolean; msg: string; data: null }> = await axios.delete(`/api/files/delete/${articleId}`)
    if (response.data.success) {
      operation.deleteSuccess(fileName)
      await fetchArticles()
      return true
    } else {
      throw new Error(response.data.msg || '删除失败')
    }
  })

  if (result) {
    console.log('文件删除成功')
  }
}

// ========================== 8. 审查相关函数（优化提示）==========================
const handleStartReview = async (articleId: number): Promise<void> => {
  showReviewProgress.value = true
  reviewProgress.value = 0
  isReviewInitiated.value = false

  if (progressInterval.value) {
    clearInterval(progressInterval.value)
  }

  // 轮询间隔从500ms改为1000ms，减少请求压力
  progressInterval.value = setInterval(() => {
    fetchReviewProgress(articleId)
  }, 1000)

  const result = await handleAsyncError(async () => {
    const response: AxiosResponse<{ success: boolean; msg: string; data: null }> = await axios.post(`/api/reviews/start/${articleId}`)
    if (response.data.success) {
      isReviewInitiated.value = true
      return true
    } else {
      throw new Error(response.data.msg || '发起审查请求失败')
    }
  }, handleReviewError)

  if (!result) {
    setTimeout(() => {
      if (!isReviewInitiated.value) {
        clearInterval(progressInterval.value!)
        showReviewProgress.value = false
      }
    }, 1000)
  }
}

const fetchReviewProgress = async (articleId: number): Promise<void> => {
  try {
    const response: AxiosResponse<{ success: boolean; data: ReviewProgress }> = await axios.get(`/api/reviews/progress/${articleId}`)
    const { progress, status } = response.data.data

    // 进度处理逻辑保持不变
    if (typeof progress === 'number' && progress >= 0 && progress <= 100) {
      if (
        progress > reviewProgress.value ||
        (progress < reviewProgress.value && reviewProgress.value - progress < 5)
      ) {
        reviewProgress.value = progress
      }
    }

    // 审查完成：优化提示
    if (reviewProgress.value >= 100 || status === '已审查') {
      reviewProgress.value = 100
      clearInterval(progressInterval.value!)
      setTimeout(async () => {
        showReviewProgress.value = false
        operation.reviewCompleted('文件', '已完成')
        await fetchArticles()
      }, 800)
    }
  } catch (error) {
    console.error('获取审查进度失败:', error)
    if (!isReviewInitiated.value && reviewProgress.value === 0) {
      clearInterval(progressInterval.value!)
      showReviewProgress.value = false
      ElMessage.error('获取审查进度失败，请重试')
    }
  }
}

// ========================== 9. 查看文件详情函数（修复路由路径）==========================
const handleViewArticle = async (articleId: number): Promise<void> => {
  try {
    // 路由路径和ReviewPage的路由配置保持一致（之前可能是/review-detail，需和router/index.ts对应）
    router.push(`/review/${articleId}`)
  } catch (error) {
    console.error('跳转到详情页失败:', error)
    ElMessage.error('查看详情失败，请重试')
  }
}

// ========================== 10. 获取文件列表（使用统一错误处理）==========================
const fetchArticles = async (): Promise<void> => {
  const result = await handleAsyncError(async () => {
    const response: AxiosResponse<{ success: boolean; msg: string; data: { list: Article[]; pagination: { page: number; page_size: number; total: number; total_pages: number } } }> = await axios.get('/api/files/list')
    const data = response.data.data
    articles.value = Array.isArray(data.list) ? data.list : []
    return data
  })

  if (!result) {
    articles.value = []
  }
}

// ========================== 11. 生命周期钩子（保持不变）==========================
onMounted(() => {
  fetchArticles()
  // 定时刷新从150秒改为300秒，减少请求压力
  listRefreshInterval.value = setInterval(() => {
    fetchArticles()
  }, 300000)
})

onUnmounted(() => {
  if (progressInterval.value) {
    clearInterval(progressInterval.value)
  }
  if (listRefreshInterval.value) {
    clearInterval(listRefreshInterval.value)
  }
})
</script>




<style scoped>
/* 响应式优化：更精细的屏幕适配 */
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

@media (max-width: 1024px) {
  .grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
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
    padding-top: 1rem; /* 对应 Tailwind 的 py-4（1rem = 16px） */
    padding-bottom: 1rem;
  }


  h1 {
    font-size: 1.5rem !important;
  }

  .nav ul {
    justify-content: center;
  }

  .section {
    padding: 4px !important;
  }
}
</style>
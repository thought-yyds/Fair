<template>
  <!-- 根容器：和其他页面保持一致的布局结构 -->
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- 1. 顶部导航栏：和其他页面完全一致 -->
    <header class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg transition-all duration-300">
      <div class="container mx-auto px-4 py-6">
        <h1 class="text-[clamp(1.5rem,3vw,2.5rem)] font-bold tracking-tight flex items-center">
          <i class="fa fa-balance-scale mr-3 text-yellow-300"></i>
          公平审查大数据平台
        </h1>
      </div>
    </header>

    <!-- 2. 导航菜单：和其他页面保持一致 -->
    <nav class="bg-white shadow-md sticky top-0 z-10 transition-all duration-300">
      <div class="container mx-auto px-4">
        <ul class="flex space-x-3 py-3">
          <!-- 首页按钮 -->
          <li>
            <router-link
              to="/"
              class="inline-flex items-center px-5 py-2.5 rounded-md font-medium text-sm transition-all duration-200"
              :class="{ 
                'bg-blue-600 text-white shadow-sm': $route.path === '/', 
                'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700': $route.path !== '/' 
              }"
            >
              <i class="fa fa-home mr-2"></i>
              首页
            </router-link>
          </li>
          <!-- 文件管理按钮 -->
          <li>
            <router-link
              to="/file-manage"
              class="inline-flex items-center px-5 py-2.5 rounded-md font-medium text-sm transition-all duration-200"
              :class="{ 
                'bg-blue-600 text-white shadow-sm': $route.path === '/file-manage', 
                'bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700': $route.path !== '/file-manage' 
              }"
            >
              <i class="fa fa-folder mr-2"></i>
              文件管理
            </router-link>
          </li>
          <!-- 返回按钮：融入导航栏 -->
          <li>
            <button
              @click="$router.push('/')"
              class="inline-flex items-center px-5 py-2.5 rounded-md font-medium text-sm transition-all duration-200 bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700"
            >
              <i class="fa fa-arrow-left mr-2"></i>
              返回
            </button>
          </li>
        </ul>
      </div>
    </nav>

    <!-- 3. 主要内容区：和其他页面一致的容器布局 -->
    <main class="flex-grow container mx-auto px-4 py-8">
      <!-- 页面加载中 -->
      <div v-if="isLoading" class="bg-white rounded-xl shadow-lg p-8 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-4 text-gray-600">加载审查信息中...</p>
      </div>

      <!-- 核心内容 -->
      <div v-else class="space-y-8">
        <!-- 文件信息卡片：和其他页面的卡片样式一致 -->
        <section class="bg-white rounded-xl shadow-lg p-6 transform hover:shadow-xl transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-semibold text-gray-800 flex items-center">
              <i class="fa fa-file-text text-blue-600 mr-2"></i>
              文件信息
            </h2>
            <div class="flex items-center space-x-4">
              <!-- 状态标签 -->
              <span 
                class="px-3 py-1 rounded-full text-sm font-medium"
                :class="getStatusClass(reviewStatus)"
              >
                {{ reviewStatus }}
              </span>
              <!-- 风险等级标签 -->
              <span 
                v-if="reviewStatus === '已审查'"
                class="px-3 py-1 rounded-full text-sm font-medium"
                :class="getRiskLevelClass(riskLevel)"
              >
                {{ riskLevel || '无风险' }}
              </span>
            </div>
          </div>
          
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="text-lg font-medium text-gray-800 mb-2">
              <i class="fa fa-file mr-2 text-blue-600"></i>
              {{ fileName }}
            </div>
            <div class="text-sm text-gray-600">
              文件ID: {{ articleId }}
            </div>
          </div>
        </section>

        <!-- 审查进度卡片：和其他页面的卡片样式一致 -->
        <section class="bg-white rounded-xl shadow-lg p-6 transform hover:shadow-xl transition-all duration-300 border border-gray-100">
          <h2 class="text-xl font-semibold text-gray-800 mb-6 flex items-center">
            <i class="fa fa-tasks text-blue-600 mr-2"></i>
            审查进度
          </h2>

          <!-- 进度条 -->
          <div class="mb-6">
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm font-medium text-gray-700">审查进度</span>
              <span class="text-sm font-medium text-blue-600">{{ reviewProgress }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-3">
              <div
                class="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                :style="{ width: `${reviewProgress}%` }"
              ></div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-4">
            <!-- 启动审查按钮 -->
            <button
              v-if="reviewStatus === '待审查'"
              @click="handleStartReview"
              class="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 hover:shadow-md transition-all duration-200 flex items-center"
            >
              <i class="fa fa-play mr-2"></i>
              启动审查
            </button>

            <!-- 审查中状态 -->
            <div v-else-if="reviewStatus === '审查中'" class="flex items-center text-amber-600">
              <i class="fa fa-spinner fa-spin mr-2"></i>
              <span class="font-medium">审查进行中，请稍候...</span>
            </div>

            <!-- 审查完成状态 -->
            <div v-else class="flex items-center text-green-600">
              <i class="fa fa-check-circle mr-2"></i>
              <span class="font-medium">审查已完成</span>
            </div>
          </div>
        </section>

        <!-- 审查结果详情：左右布局 -->
        <section 
          v-if="reviewProgress === 100" 
          class="bg-white rounded-xl shadow-lg p-6 transform hover:shadow-xl transition-all duration-300 border border-gray-100"
        >
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-semibold text-gray-800 flex items-center">
              <i class="fa fa-shield text-blue-600 mr-2"></i>
              审查结果详情
              <span class="ml-3 px-3 py-1 rounded-full text-sm font-normal"
                    :class="violationSentences.length ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'">
                {{ violationSentences.length ? '发现违规内容' : '未发现违规' }}
              </span>
            </h2>
            
            <!-- PDF下载按钮 -->
            <button
              @click="downloadPDF"
              class="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200 shadow-sm"
            >
              <i class="fa fa-download mr-2"></i>
              下载PDF报告
              </button>
          </div>

          <!-- 左右布局容器 -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 左侧：原始文档 -->
            <div class="space-y-4">
              <h3 class="text-lg font-medium text-gray-800 flex items-center">
                <i class="fa fa-file-text text-blue-600 mr-2"></i>
                原始文档
              </h3>
              
              <div class="border border-gray-200 rounded-lg p-4 bg-gray-50 max-h-96 overflow-y-auto">
                <div 
                  ref="documentContainer"
                  v-if="documentContent"
                  class="text-gray-800 whitespace-pre-wrap leading-relaxed"
                  v-html="getHighlightedContent()"
                ></div>
                <div v-else class="text-gray-500 text-center py-8">
                  <i class="fa fa-file-o text-2xl mb-2"></i>
                  <p>文档内容加载中...</p>
                </div>
              </div>
            </div>

            <!-- 右侧：违规句子列表 -->
            <div class="space-y-4">
              <h3 class="text-lg font-medium text-gray-800 flex items-center">
                <i class="fa fa-exclamation-triangle text-red-600 mr-2"></i>
                违规内容
                <span class="ml-2 text-sm text-gray-500">({{ violationSentences.length }} 项)</span>
              </h3>
              
              <!-- 违规句子列表 -->
              <div v-if="violationSentences.length" class="space-y-3 max-h-96 overflow-y-auto">
                <div
                  v-for="(sentence, index) in violationSentences"
                  :key="sentence.id"
                  class="border border-red-200 rounded-lg p-4 bg-red-50 hover:bg-red-100 transition-colors duration-200 cursor-pointer"
                  @mouseenter="highlightSentence(sentence.content)"
                  @mouseleave="clearHighlight"
                  :class="{ 'ring-2 ring-red-300': highlightedSentence === sentence.content }"
                >
                  <div class="flex items-start justify-between mb-2">
                    <span class="inline-flex items-center px-2 py-1 bg-red-200 text-red-800 rounded text-xs font-medium">
                      违规 #{{ index + 1 }}
                    </span>
                  </div>
                  
                  <div class="mb-2">
                    <div class="text-sm font-medium text-gray-700 mb-1">句子内容：</div>
                    <div class="text-gray-800 bg-white p-2 rounded border text-sm">
                      {{ sentence.content }}
                    </div>
                  </div>
                  
                  <div>
                    <div class="text-sm font-medium text-gray-700 mb-1">违规原因：</div>
                    <div class="inline-flex items-center px-2 py-1 bg-red-100 text-red-800 rounded text-xs">
                      {{ sentence.annotation_content }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 无违规提示 -->
              <div v-else class="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg bg-green-50">
                <i class="fa fa-check-circle text-4xl text-green-500 mb-4"></i>
                <h3 class="text-lg font-medium text-gray-800 mb-2">审查完成</h3>
                <p class="text-gray-600">恭喜！该文件未发现任何违规内容</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- 4. 页脚：和其他页面完全一致 -->
    <footer class="bg-gray-800 text-white py-4 mt-auto">
      <div class="container mx-auto px-4 text-center text-sm">
        <p>© 2023 公平审查大数据平台 版权所有</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { getReviewDetail, startReview, createReviewProgressSSE } from '@/api/reviewApi';
import { getFileDetail, getFullContent } from '@/api/fileApi';
import { useReviewStore } from '@/store/reviewStore';
import type { Article } from '@/types/article';
import type { ViolationSentence, StartReviewParams } from '@/types/review';
import jsPDF from 'jspdf'
import 'jspdf-autotable';
import html2canvas from 'html2canvas';

// 接收路由参数（props: true 已开启）
// 注意：路由参数总是字符串类型，需要转换为数字
const props = defineProps<{ articleId: string }>();
const articleId = computed(() => Number(props.articleId));

// 使用store
const reviewStore = useReviewStore();

// 页面状态
const isLoading = ref(true);
const fileName = ref('');
const reviewProgress = ref(0);
const reviewStatus = ref<Article['status']>('待审查');
const riskLevel = ref<Article['risk_level']>('无风险');
const reviewTime = ref<string>('');
const violationSentences = ref<ViolationSentence[]>([]);
const documentContent = ref<string>('');
const highlightedSentence = ref<string>('');
const allSentences = ref<Array<{
  content: string;
  start_pos: number;
  end_pos: number;
  id: number | null;
  has_problem: boolean | null;
  annotation_id: number | null;
  annotation_content: string;
}>>([]);
let sseConnection: EventSource | null = null;

// 文档容器引用
const documentContainer = ref<HTMLElement | null>(null);

// 样式函数：和其他页面保持一致
const getStatusClass = (status: string): string => {
  switch (status) {
    case '待审查':
      return 'bg-amber-100 text-amber-800';
    case '审查中':
      return 'bg-blue-100 text-blue-800';
    case '已审查':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getRiskLevelClass = (level?: string): string => {
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
};

// 页面加载初始化
onMounted(async () => {
  console.log('ReviewPage onMounted 开始，articleId:', articleId.value);
  try {
    // 1. 获取文件基本信息
    console.log('开始获取文件详情，articleId:', articleId.value);
    const response = await getFileDetail(articleId.value);
    console.log('文件详情响应:', response);
    
    const fileInfo = response; // response 已经是 data 字段的内容
    console.log('文件信息:', fileInfo);
    
    fileName.value = fileInfo.name;
    reviewStatus.value = fileInfo.status;
    reviewProgress.value = fileInfo.review_progress;
    riskLevel.value = fileInfo.risk_level || '无风险';

    console.log('文件状态:', reviewStatus.value, '进度:', reviewProgress.value);

    // 2. 处理不同状态
    if (reviewStatus.value === '审查中') {
      console.log('启动SSE连接');
      startSSEConnection(); // 启动SSE连接
    } else if (reviewStatus.value === '已审查') {
      console.log('获取审查详情');
      await fetchReviewDetail(); // 获取详情
    }
    
    console.log('ReviewPage 初始化完成');
  } catch (err: any) {
    console.error('ReviewPage 加载失败:', err);
    console.error('错误详情:', {
      message: err.message,
      stack: err.stack,
      response: err.response?.data,
      status: err.response?.status
    });
    ElMessage.error(`加载失败: ${err.message || '未知错误'}，请刷新`);
  } finally {
    isLoading.value = false;
  }
});

// 页面销毁清除SSE连接
onUnmounted(() => {
  if (sseConnection) {
    sseConnection.close();
    sseConnection = null;
  }
  reviewStore.closeSSEConnection(articleId.value);
});

// PDF下载功能
const downloadPDF = async () => {
  try {
    ElMessage.info('正在生成PDF报告，请稍候...');
    
    // 创建PDF实例
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 15;
    const contentWidth = pageWidth - 2 * margin;
    
    let yPosition = margin;
    
    // 构建HTML内容用于PDF生成
    const buildPDFContent = () => {
      let html = `
        <div style="font-family: 'Microsoft YaHei', 'SimHei', 'Arial', sans-serif; padding: 20px; color: #333;">
          <h1 style="text-align: center; font-size: 24px; margin-bottom: 20px; color: #1e40af;">
            公平审查大数据平台 - 审查报告
          </h1>
          <hr style="border: 1px solid #e5e7eb; margin-bottom: 20px;">
          
          <h2 style="font-size: 18px; margin-top: 20px; margin-bottom: 15px; color: #1e40af;">
            基本信息
          </h2>
          <div style="margin-left: 10px; line-height: 1.8;">
            <p><strong>文档名称：</strong>${fileName.value}</p>
            <p><strong>审查时间：</strong>${reviewTime.value ? new Date(reviewTime.value).toLocaleString('zh-CN') : '未完成审查'}</p>
            <p><strong>风险等级：</strong>${riskLevel.value}</p>
            <p><strong>违规数量：</strong>${violationSentences.value.length} 项</p>
          </div>
          
          <hr style="border: 1px solid #e5e7eb; margin: 20px 0;">
          
          <h2 style="font-size: 18px; margin-top: 20px; margin-bottom: 15px; color: #1e40af;">
            ${violationSentences.value.length > 0 ? '违规内容详情' : '审查结果'}
          </h2>
      `;
      
      if (violationSentences.value.length > 0) {
        violationSentences.value.forEach((sentence, index) => {
          html += `
            <div style="margin-bottom: 20px; padding: 15px; background-color: #fef2f2; border-left: 4px solid #ef4444; border-radius: 4px;">
              <h3 style="font-size: 16px; color: #dc2626; margin-bottom: 10px;">
                违规 #${index + 1}
              </h3>
              <p style="margin-bottom: 10px;">
                <strong>原句：</strong><br>
                <span style="padding-left: 10px; color: #374151;">${sentence.content}</span>
              </p>
              <p>
                <strong>违规原因：</strong><br>
                <span style="padding-left: 10px; color: #dc2626;">${sentence.annotation_content}</span>
              </p>
            </div>
          `;
        });
      } else {
        html += `
          <div style="padding: 20px; background-color: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 4px;">
            <p style="color: #16a34a; font-size: 16px;">恭喜！该文件未发现任何违规内容。</p>
          </div>
        `;
      }
      
      html += `
          <hr style="border: 1px solid #e5e7eb; margin: 20px 0;">
          <div style="text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; padding-bottom: 20px;">
            <p>生成时间：${new Date().toLocaleString('zh-CN')}</p>
            <p style="margin-top: 5px;">公平审查大数据平台</p>
          </div>
        </div>
      `;
      
      return html;
    };
    
    // 创建一个临时div来渲染HTML内容
    const tempDiv = document.createElement('div');
    tempDiv.style.position = 'absolute';
    tempDiv.style.left = '-9999px';
    tempDiv.style.width = `${contentWidth}mm`;
    tempDiv.style.padding = '20px';
    tempDiv.style.fontFamily = "'Microsoft YaHei', 'SimHei', 'Arial', sans-serif";
    tempDiv.style.fontSize = '14px';
    tempDiv.style.color = '#333';
    tempDiv.style.backgroundColor = '#ffffff';
    tempDiv.innerHTML = buildPDFContent();
    document.body.appendChild(tempDiv);
    
    // 使用html2canvas将HTML转换为图片
    const canvas = await html2canvas(tempDiv, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      width: tempDiv.scrollWidth,
      height: tempDiv.scrollHeight
    });
    
    // 清理临时元素
    document.body.removeChild(tempDiv);
    
    const imgData = canvas.toDataURL('image/png');
    const imgWidth = pageWidth - 2 * margin;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    
    // 如果内容超过一页，需要分页
    let heightLeft = imgHeight;
    let position = 0;
    
    // 添加第一页
    pdf.addImage(imgData, 'PNG', margin, yPosition, imgWidth, imgHeight);
    heightLeft -= (pageHeight - yPosition - margin);
    
    // 如果内容超过一页，添加新页面
    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', margin, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }
    
    // 添加页脚（使用英文避免中文乱码，或者可以省略，因为生成时间已在HTML内容中）
    // 如果需要页码，可以使用英文：Page X of Y
    const totalPages = pdf.internal.pages.length - 1;
    if (totalPages > 1) {
      for (let i = 1; i <= totalPages; i++) {
        pdf.setPage(i);
        pdf.setFontSize(10);
        pdf.setTextColor(107, 114, 128); // #6b7280
        // 使用英文页码避免中文乱码
        pdf.text(
          `Page ${i} of ${totalPages}`,
          pageWidth / 2,
          pageHeight - 10,
          { align: 'center' }
        );
      }
    }
    
    // 下载PDF
    const pdfFileName = `审查报告_${fileName.value}_${new Date().toISOString().split('T')[0]}.pdf`;
    pdf.save(pdfFileName);
    
    ElMessage.success('PDF报告下载成功');
  } catch (error) {
    console.error('PDF生成失败:', error);
    ElMessage.error('PDF生成失败，请重试');
  }
};


// 启动SSE连接监听进度
const startSSEConnection = () => {
  // 关闭现有连接
  if (sseConnection) {
    sseConnection.close();
  }
  
  sseConnection = createReviewProgressSSE(
    articleId.value,
    (progress: number) => {
      // 进度更新回调
      reviewProgress.value = progress;
      reviewStore.setReviewProgress(articleId.value, {
        progress,
        status: '审查中',
        risk_level: riskLevel.value
      });
    },
    async () => {
      // 完成回调
      reviewStatus.value = '已审查';
      reviewProgress.value = 100;
      reviewStore.removeActiveReview(articleId.value);
      await fetchReviewDetail();
      ElMessage.success('审查完成！');
    },
    (error: Event) => {
      // 错误回调
      console.error('SSE连接错误:', error);
      ElMessage.error('连接中断，请刷新页面重试');
    }
  );
  
  // 保存连接引用
  reviewStore.setSSEConnection(articleId.value, sseConnection);
  reviewStore.addActiveReview(articleId.value);
};

// 获取审查详情（违规句子）
const fetchReviewDetail = async () => {
  try {
    console.log('开始获取审查详情，articleId:', articleId.value);
    
    // 并行获取审查详情和完整文档内容
    const [reviewRes, fullContentRes] = await Promise.all([
      getReviewDetail(articleId.value),
      getFullContent(articleId.value)
    ]);
    
    console.log('审查详情响应:', reviewRes);
    console.log('完整文档内容响应:', fullContentRes);
    
    // 设置审查详情
    violationSentences.value = reviewRes.violation_sentences || [];
    riskLevel.value = (reviewRes.risk_level as Article['risk_level']) || '无风险';
    reviewTime.value = reviewRes.review_time || '';
    
    // 设置完整文档内容
    documentContent.value = fullContentRes.full_content || '';
    allSentences.value = fullContentRes.sentences || [];
    
    reviewStore.setViolationSentences(articleId.value, violationSentences.value);
    
    console.log('审查详情获取成功，违规句子数量:', violationSentences.value.length);
    console.log('完整文档内容长度:', documentContent.value.length);
    console.log('句子总数:', allSentences.value.length);
  } catch (err) {
    console.error('获取审查详情失败:', err);
    ElMessage.error('获取详情失败');
  }
};

// 启动审查（接收组件事件）
const handleStartReview = async () => {
  try {
    const params: StartReviewParams = { articleId: articleId.value };
    await startReview(params);
    reviewStatus.value = '审查中';
    startSSEConnection();
  } catch (err) {
    ElMessage.error('启动审查失败');
  }
};

// 鼠标悬停高亮违规句子
const highlightSentence = (sentence: string) => {
  highlightedSentence.value = sentence;
  
  // 自动滚动到高亮位置
  nextTick(() => {
    scrollToHighlightedSentence();
  });
};

// 鼠标离开清除高亮
const clearHighlight = () => {
  highlightedSentence.value = '';
};

// 滚动到高亮的句子位置
const scrollToHighlightedSentence = () => {
  if (!documentContainer.value || !highlightedSentence.value) {
    return;
  }
  
  // 等待 DOM 更新完成
  setTimeout(() => {
    // 查找高亮的 mark 元素
    const highlightedElement = documentContainer.value?.querySelector('.highlight-sentence');
    if (highlightedElement) {
      // 平滑滚动到高亮元素
      highlightedElement.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
      });
    } else {
      // 如果找不到 .highlight-sentence，尝试查找包含目标文本的元素
      const textNodes = documentContainer.value?.querySelectorAll('*');
      if (textNodes) {
        for (const node of textNodes) {
          if (node.textContent?.includes(highlightedSentence.value)) {
            node.scrollIntoView({
              behavior: 'smooth',
              block: 'center',
              inline: 'nearest'
            });
            break;
          }
        }
      }
    }
  }, 100); // 给 DOM 更新一些时间
};

// 获取高亮后的文档内容
const getHighlightedContent = () => {
  if (!documentContent.value) {
    return '';
  }
  
  if (!highlightedSentence.value) {
    return documentContent.value;
  }
  
  // 首先尝试精确匹配
  let sentenceInfo = allSentences.value.find(s => s.content === highlightedSentence.value);
  
  // 如果精确匹配失败，尝试模糊匹配（去除首尾空格和换行符）
  if (!sentenceInfo) {
    const trimmedHighlighted = highlightedSentence.value.trim();
    sentenceInfo = allSentences.value.find(s => s.content.trim() === trimmedHighlighted);
  }
  
  // 如果还是找不到，尝试包含匹配
  if (!sentenceInfo) {
    const trimmedHighlighted = highlightedSentence.value.trim();
    sentenceInfo = allSentences.value.find(s => 
      s.content.includes(trimmedHighlighted) || trimmedHighlighted.includes(s.content.trim())
    );
  }
  
  if (sentenceInfo) {
    const before = documentContent.value.substring(0, sentenceInfo.start_pos);
    const highlighted = `<mark class="highlight-sentence">${sentenceInfo.content}</mark>`;
    const after = documentContent.value.substring(sentenceInfo.end_pos);
    return before + highlighted + after;
  }
  // 如果找不到位置信息，使用正则表达式作为备选
  const escapedSentence = highlightedSentence.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const highlightedContent = documentContent.value.replace(
    new RegExp(escapedSentence, 'g'),
    `<mark class="highlight-sentence">${highlightedSentence.value}</mark>`
  );
  
  return highlightedContent;
};
</script>

<!-- 响应式样式：和其他页面保持一致 -->
<style scoped>
/* 高亮样式 */
:deep(.highlight-sentence) {
  background-color: #fef3c7;
  color: #92400e;
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: 600;
  box-shadow: 0 0 0 2px #f59e0b;
  animation: highlight-pulse 0.3s ease-in-out;
}

@keyframes highlight-pulse {
  0% {
    box-shadow: 0 0 0 0 #f59e0b;
  }
  50% {
    box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.3);
  }
  100% {
    box-shadow: 0 0 0 2px #f59e0b;
  }
}

/* 响应式优化：更精细的屏幕适配 */
@media (max-width: 1024px) {
  .space-y-8 > * + * {
    margin-top: 1.5rem;
  }
  
  /* 在大屏幕上，左右布局改为上下布局 */
  .grid-cols-1.lg\\:grid-cols-2 {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .space-y-8 > * + * {
    margin-top: 1rem;
  }
  
  .flex.gap-4 {
    flex-direction: column;
    align-items: stretch;
  }
  
  .flex.gap-4 button {
    width: 100%;
    justify-content: center;
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
    flex-wrap: wrap;
  }

  section {
    padding: 1rem !important;
  }
}
</style>
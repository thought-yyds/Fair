<template>
  <div class="file-list-container">
    <!-- 搜索和操作区 -->
    <div class="file-list-header">
      <div class="search-container">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文件名..."
          clearable
          class="search-input"
          @keyup.enter="handleSearch"
          @input="handleSearchInput"
          @clear="handleSearchClear"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button 
              type="primary" 
              :icon="Search" 
              @click="handleSearch"
              :loading="isSearching"
            >
              搜索
            </el-button>
          </template>
        </el-input>
        
        <!-- 搜索状态提示 -->
        <div v-if="isSearching" class="search-status">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>搜索中...</span>
        </div>
        
        <!-- 搜索结果统计 -->
        <div v-if="searchKeyword && !isSearching" class="search-result-info">
          <el-tag type="info" size="small">
            搜索 "{{ searchKeyword }}" 找到 {{ total }} 条结果
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 列表内容：用ProgressCard展示每个文件 -->
    <div class="file-cards">
      <!-- 骨架屏：加载时显示 -->
      <template v-if="isLoading">
        <SkeletonCard v-for="n in 3" :key="`skeleton-${n}`" />
      </template>
      
      <!-- 实际内容：加载完成后显示 -->
      <template v-else>
        <ProgressCard
          v-for="file in fileList"
          :key="file.id"
          :articleId="file.id"
          :fileName="file.name"
          :progress="file.review_progress"
          :status="file.status"
          :riskLevel="file.risk_level"
          @startReview="handleStartReview"
          @viewDetail="handleViewDetail"
          @deleteFile="handleDeleteFile"
        />
      </template>
    </div>

    <!-- 空状态：无文件或搜索无结果 -->
    <EmptyState
      v-if="!isLoading && fileList.length === 0"
      description="未找到文件，请上传新文件或更换搜索关键词"
    ></EmptyState>

    <!-- 分页控件 -->
    <el-pagination
      v-if="!isLoading && total > 0"
      class="pagination"
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      :page-sizes="[5, 10, 20, 50]"
      :pager-count="7"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handlePageSizeChange"
      @current-change="handlePageChange"
    >
      <template #total="{ total }">
        <span class="pagination-total">
          共 {{ total }} 条记录，第 {{ page }} / {{ Math.ceil(total / pageSize) }} 页
        </span>
      </template>
    </el-pagination>
  </div>
</template>

<script setup lang="ts">
import { startReview } from '@/api/reviewApi';
// 其他已有导入...
// 2. 定义emit（声明要触发的事件）

import { ref, onMounted } from 'vue';
import { ElInput, ElButton, ElPagination, ElMessage, ElIcon, ElTag } from 'element-plus';
import { Search, Loading } from '@element-plus/icons-vue';
import { getFileList} from '@/api/fileApi';
import ProgressCard from './ProgressCard.vue';
import EmptyState from './EmptyState.vue';
import SkeletonCard from './SkeletonCard.vue';
import { withLoading } from '@/utils/loadingManager';
import { validateSearchKeyword, validatePaginationParams } from '@/utils/validators';
import type { Article, ArticleListParams } from '@/types/article';
const emit = defineEmits<{
  (e: 'viewDetail', articleId: number): void;
  (e: 'updateTotal', total: number): void;
  (e: 'deleteFile', articleId: number, fileName: string): void;
}>();
// 分页和搜索参数
const page = ref(1);
const pageSize = ref(10);
const total = ref(0);
const searchKeyword = ref('');

// 列表状态
const fileList = ref<Article[]>([]);
const isLoading = ref(false);
const isSearching = ref(false);

// 搜索防抖定时器
let searchTimeout: NodeJS.Timeout | null = null;

// 页面加载时获取列表
onMounted(() => {
  fetchFileList();
});

// 获取文件列表（核心方法）
const fetchFileList = async () => {
  const result = await withLoading(async () => {
    isSearching.value = !!searchKeyword.value.trim();
    
    const params: ArticleListParams = {
      page: page.value,
      pageSize: pageSize.value,
      keyword: searchKeyword.value.trim() || undefined // 搜索关键词（可选）
    };
    const response = await getFileList(params);
    fileList.value = response.list;
    total.value = response.pagination.total; // 总条数（用于分页）
    
    // 通知父组件更新总数
    emit('updateTotal', response.pagination.total);
    
    return response;
  }, {
    local: 'fileList',
    text: isSearching.value ? '搜索中...' : '加载文件列表中...'
  });

  if (!result) {
    ElMessage.error('获取文件列表失败，请刷新重试');
  }
  
  isSearching.value = false;
};

// 搜索文件
const handleSearch = () => {
  // 验证搜索关键词
  const keywordValidation = validateSearchKeyword(searchKeyword.value);
  if (!keywordValidation.valid) {
    ElMessage.error(keywordValidation.message || '搜索关键词无效');
    return;
  }
  
  page.value = 1; // 搜索时重置到第1页
  fetchFileList();
};

// 实时搜索输入处理（防抖）
const handleSearchInput = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  // 防抖延迟500ms
  searchTimeout = setTimeout(() => {
    if (searchKeyword.value.trim()) {
      handleSearch();
    } else {
      // 如果搜索框为空，重置到第一页并刷新
      page.value = 1;
      fetchFileList();
    }
  }, 500);
};

// 清空搜索
const handleSearchClear = () => {
  searchKeyword.value = '';
  page.value = 1;
  fetchFileList();
};

// 分页：页码变化
const handlePageChange = (newPage: number) => {
  // 验证分页参数
  const paginationValidation = validatePaginationParams(newPage, pageSize.value);
  if (!paginationValidation.valid) {
    ElMessage.error(paginationValidation.message || '分页参数无效');
    return;
  }
  
  page.value = newPage;
  fetchFileList();
};

// 分页：每页条数变化
const handlePageSizeChange = (newSize: number) => {
  // 验证分页参数
  const paginationValidation = validatePaginationParams(page.value, newSize);
  if (!paginationValidation.valid) {
    ElMessage.error(paginationValidation.message || '分页参数无效');
    return;
  }
  
  pageSize.value = newSize;
  page.value = 1; // 条数变化时重置到第1页
  fetchFileList();
};

// 启动审查（传递给父组件处理）
// 启动审查（需要用articleId调用API，再刷新列表）
const handleStartReview = async (articleId: number) => {
  try {
    // 实际调用启动审查的API（使用articleId）
    await startReview({ articleId });
    ElMessage.success('审查已启动');
    // 刷新列表，更新该文件的状态
    fetchFileList();
  } catch (error) {
    ElMessage.error('启动审查失败');
  }
};

// 查看详情（通过emit传递articleId给父组件，实现路由跳转）
const handleViewDetail = (articleId: number) => {
  // 实际触发事件，将articleId传给父组件（父组件会处理跳转）
  emit('viewDetail', articleId);
};

// 删除文件（通过emit传递articleId和fileName给父组件）
const handleDeleteFile = (articleId: number, fileName: string) => {
  // 实际触发事件，将articleId和fileName传给父组件（父组件会处理删除）
  emit('deleteFile', articleId, fileName);
};
</script>

<style scoped>
.file-list-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
}

.file-list-header {
  margin-bottom: 24px;
}

.search-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-input {
  width: 400px;
}

.search-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.search-result-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.pagination {
  text-align: right;
  margin-top: 24px;
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
}

.pagination-total {
  color: #666;
  font-size: 14px;
  margin-right: 16px;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .file-cards {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .file-list-container {
    padding: 12px;
  }
  
  .search-input {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .file-cards {
    gap: 12px;
  }
  
  .file-list-container {
    padding: 8px;
  }
}
</style>
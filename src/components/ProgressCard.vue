<template>
  <el-card shadow="hover" class="progress-card">
    <!-- 文件名与状态 -->
    <div class="card-header">
      <h3 class="file-name">{{ fileName }}</h3>
      <el-tag :type="statusType" :icon="statusIcon">{{ status }}</el-tag>
    </div>

    <!-- 进度条 -->
    <el-progress
      :percentage="progress"
      :status="progress === 100 ? 'success' : undefined"
      :indeterminate="status === '审查中'"
      class="progress-bar"
    ></el-progress>

    <!-- 操作区 -->
    <div class="actions">
      <!-- 待审查：显示启动按钮和删除按钮 -->
      <div v-if="status === '待审查'" class="pending-actions">
        <el-button
          type="primary"
          size="small"
          @click="handleStart"
        >
          <el-icon><VideoPlay /></el-icon> 启动审查
        </el-button>
        <el-button
          type="danger"
          size="small"
          @click="handleDelete"
        >
          <el-icon><Delete /></el-icon> 删除
        </el-button>
      </div>

      <!-- 审查中：显示加载提示和删除按钮 -->
      <div v-else-if="status === '审查中'" class="reviewing-actions">
        <div class="reviewing">
          <el-icon class="loading"><Loading /></el-icon>
          <span>审查中...</span>
        </div>
        <el-button
          type="danger"
          size="small"
          @click="handleDelete"
        >
          <el-icon><Delete /></el-icon> 删除
        </el-button>
      </div>

      <!-- 已审查：显示风险等级、详情按钮和删除按钮 -->
      <div v-else class="reviewed-actions">
        <div class="reviewed-info">
          <el-tag :type="riskLevelType" size="small">
            {{ riskLevel || '无风险' }}
          </el-tag>
          <el-button
            type="text"
            size="small"
            @click="handleViewDetail"
          >
            <el-icon><View /></el-icon> 详情
          </el-button>
        </div>
        <el-button
          type="danger"
          size="small"
          @click="handleDelete"
        >
          <el-icon><Delete /></el-icon> 删除
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ElTag, ElProgress, ElButton, ElIcon } from 'element-plus';
// 修复图标导入
import { VideoPlay, Loading, View, Delete } from '@element-plus/icons-vue';
import type { Article } from '@/types/article';

// Props：接收文件信息
const { articleId, fileName, progress, status, riskLevel } = defineProps<{
  articleId: number;
  fileName: string;
  progress: number;
  status: Article['status'];
  riskLevel?: Article['risk_level'];
}>();

// Emits：操作事件通知父组件
const emit = defineEmits<{
  (e: 'startReview', id: number): void;
  (e: 'viewDetail', id: number): void;
  (e: 'deleteFile', id: number, fileName: string): void;
}>();

// 状态标签样式
const statusType = computed(() => {
  switch (status) {
    case '待审查': return 'info';
    case '审查中': return 'warning';
    case '已审查': return 'success';
    default: return 'info';
  }
});

// 状态图标
const statusIcon = computed(() => {
  switch (status) {
    case '待审查': return 'el-icon-time';
    case '审查中': return 'el-icon-loading';
    case '已审查': return 'el-icon-check';
    default: return 'el-icon-time';
  }
});

// 风险等级标签样式
const riskLevelType = computed(() => {
  switch (riskLevel) {
    case '低风险': return 'info';
    case '中风险': return 'warning';
    case '高风险': return 'danger';
    default: return 'success';
  }
});

// 启动审查
const handleStart = () => {
  emit('startReview', articleId);
};

// 查看详情
const handleViewDetail = () => {
  emit('viewDetail', articleId);
};

// 删除文件
const handleDelete = () => {
  emit('deleteFile', articleId, fileName);
};
</script>

<style scoped>
.progress-card {
  width: 100%;
  min-width: 300px;
  max-width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 12px;
}

.file-name {
  margin: 0;
  font-size: 16px;
  white-space: normal;
  word-break: break-all;
  line-height: 1.4;
  flex: 1;
  min-width: 0;
}

.progress-bar {
  margin: 8px 0;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.pending-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.reviewing-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.reviewing {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.loading {
  animation: spin 1.5s linear infinite;
}

.reviewed-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.reviewed-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式优化 */
@media (max-width: 768px) {
  .progress-card {
    min-width: 280px;
  }
  
  .file-name {
    font-size: 14px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .actions {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .pending-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .reviewing-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .reviewed-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .reviewed-info {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .progress-card {
    min-width: 250px;
  }
  
  .file-name {
    font-size: 13px;
  }
}
</style>
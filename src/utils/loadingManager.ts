// src/utils/loadingManager.ts
/**
 * 加载状态管理工具
 * 提供全局loading、局部loading、骨架屏等加载状态管理
 */

import { ref, reactive } from 'vue';
import { ElLoading } from 'element-plus';

// 全局加载状态
const globalLoading = ref(false);
let globalLoadingInstance: ReturnType<typeof ElLoading.service> | null = null;

// 局部加载状态映射
const localLoadingStates = reactive<Record<string, boolean>>({});

/**
 * 全局加载状态管理
 */
export const useGlobalLoading = () => {
  const showGlobalLoading = (text = '加载中...') => {
    if (globalLoadingInstance) {
      globalLoadingInstance.close();
    }
    
    globalLoading.value = true;
    globalLoadingInstance = ElLoading.service({
      text,
      lock: true,
      background: 'rgba(0, 0, 0, 0.7)',
      customClass: 'global-loading'
    });
  };

  const hideGlobalLoading = () => {
    if (globalLoadingInstance) {
      globalLoadingInstance.close();
      globalLoadingInstance = null;
    }
    globalLoading.value = false;
  };

  return {
    globalLoading: globalLoading.value,
    showGlobalLoading,
    hideGlobalLoading
  };
};

/**
 * 局部加载状态管理
 */
export const useLocalLoading = (key: string) => {
  const showLocalLoading = () => {
    localLoadingStates[key] = true;
  };

  const hideLocalLoading = () => {
    localLoadingStates[key] = false;
  };

  const isLoading = () => {
    return localLoadingStates[key] || false;
  };

  return {
    isLoading: isLoading(),
    showLocalLoading,
    hideLocalLoading
  };
};

/**
 * 异步操作加载状态管理
 */
export const withLoading = async <T>(
  asyncFn: () => Promise<T>,
  options: {
    global?: boolean;
    local?: string;
    text?: string;
  } = {}
): Promise<T | null> => {
  const { global = false, local, text = '加载中...' } = options;

  try {
    // 显示加载状态
    if (global) {
      const { showGlobalLoading } = useGlobalLoading();
      showGlobalLoading(text);
    }

    if (local) {
      localLoadingStates[local] = true;
    }

    // 执行异步操作
    const result = await asyncFn();
    return result;
  } catch (error) {
    console.error('异步操作失败:', error);
    return null;
  } finally {
    // 隐藏加载状态
    if (global) {
      const { hideGlobalLoading } = useGlobalLoading();
      hideGlobalLoading();
    }

    if (local) {
      localLoadingStates[local] = false;
    }
  }
};

/**
 * 文件上传加载状态
 */
export const useUploadLoading = () => {
  const uploadLoading = ref(false);
  const uploadProgress = ref(0);

  const startUpload = () => {
    uploadLoading.value = true;
    uploadProgress.value = 0;
  };

  const updateProgress = (progress: number) => {
    uploadProgress.value = Math.min(100, Math.max(0, progress));
  };

  const finishUpload = () => {
    uploadLoading.value = false;
    uploadProgress.value = 100;
    
    // 延迟重置进度
    setTimeout(() => {
      uploadProgress.value = 0;
    }, 1000);
  };

  return {
    uploadLoading: uploadLoading.value,
    uploadProgress: uploadProgress.value,
    startUpload,
    updateProgress,
    finishUpload
  };
};

/**
 * 审查进度加载状态
 */
export const useReviewLoading = () => {
  const reviewLoading = ref(false);
  const reviewProgress = ref(0);
  const reviewStatus = ref<'pending' | 'reviewing' | 'completed' | 'error'>('pending');

  const startReview = () => {
    reviewLoading.value = true;
    reviewProgress.value = 0;
    reviewStatus.value = 'reviewing';
  };

  const updateReviewProgress = (progress: number) => {
    reviewProgress.value = Math.min(100, Math.max(0, progress));
  };

  const completeReview = () => {
    reviewLoading.value = false;
    reviewProgress.value = 100;
    reviewStatus.value = 'completed';
  };

  const errorReview = () => {
    reviewLoading.value = false;
    reviewStatus.value = 'error';
  };

  const resetReview = () => {
    reviewLoading.value = false;
    reviewProgress.value = 0;
    reviewStatus.value = 'pending';
  };

  return {
    reviewLoading: reviewLoading.value,
    reviewProgress: reviewProgress.value,
    reviewStatus: reviewStatus.value,
    startReview,
    updateReviewProgress,
    completeReview,
    errorReview,
    resetReview
  };
};

/**
 * 批量操作加载状态
 */
export const useBatchLoading = () => {
  const batchLoading = ref(false);
  const batchProgress = ref(0);
  const batchTotal = ref(0);
  const batchCurrent = ref(0);

  const startBatch = (total: number) => {
    batchLoading.value = true;
    batchTotal.value = total;
    batchCurrent.value = 0;
    batchProgress.value = 0;
  };

  const updateBatchProgress = (current: number) => {
    batchCurrent.value = current;
    batchProgress.value = Math.round((current / batchTotal.value) * 100);
  };

  const finishBatch = () => {
    batchLoading.value = false;
    batchProgress.value = 100;
    
    // 延迟重置
    setTimeout(() => {
      batchTotal.value = 0;
      batchCurrent.value = 0;
      batchProgress.value = 0;
    }, 2000);
  };

  return {
    batchLoading: batchLoading.value,
    batchProgress: batchProgress.value,
    batchTotal: batchTotal.value,
    batchCurrent: batchCurrent.value,
    startBatch,
    updateBatchProgress,
    finishBatch
  };
};
